"""Paper analyzer module.

Provides multi-level analysis capabilities for papers converted by MinerU.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

# Default output directory
DEFAULT_OUTPUT_DIR = Path.home() / ".paper-reader" / "outputs"


class AnalysisLevel(Enum):
    """Analysis depth levels.

    v1.0 A/B/C: legacy, method-light summarization.
    v2.0 L1-L4: method-driven, decision-framework-backed granularity.
    Both coexist for backward compatibility.
    """
    A = "A"  # v1.0 legacy: basic — summary + key findings
    B = "B"  # v1.0 legacy: complete — + methodology + figures + related work
    C = "C"  # v1.0 legacy: deep — + limitations + trends + reproducibility
    L1 = "L1"  # v2.0: concepts only
    L2 = "L2"  # v2.0: concepts + relations
    L3 = "L3"  # v2.0: concepts + relations + hierarchy (ontology)
    L4 = "L4"  # v2.0: concepts + relations + hierarchy + evidence


@dataclass
class AnalysisResult:
    """Result of a paper analysis."""
    paper_id: str
    level: AnalysisLevel
    output_dir: Path
    files: dict[str, str] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class Decision:
    """v2.0 decision object produced by the LLM agent from METHODOLOGY.md.

    All fields have defaults so callers can construct a Decision with only
    the core fields (level, base_dir, doc_name, format, use_case) populated.
    The optional toggles (chunks / relations / hierarchy / evidence) are
    used by future extensions; in the v2.0 scaffold stage they are stored
    but not yet consumed.
    """
    level: str = "L1"            # "L1" | "L2" | "L3" | "L4" | "A" | "B" | "C"
    base_dir: Path = Path()      # pathlib.Path is immutable; safe as direct default
    doc_name: str = ""
    format: str = "markdown"     # "markdown" | "wiki" | "json"
    use_case: str = "transient"  # "obsidian" | "kb" | "transient"
    chunks: list | None = None
    relations: bool = False
    hierarchy: bool = False
    evidence: bool = False


def get_output_files(level: AnalysisLevel) -> list[str]:
    """Get list of output files for a given analysis level.

    v1.0 (A/B/C) returns legacy files; v2.0 (L1-L4) returns new files.
    Both paths are supported for backward compatibility.
    """
    if level == AnalysisLevel.A:
        return ["summary.md", "key_findings.md"]
    if level == AnalysisLevel.B:
        return ["summary.md", "key_findings.md", "methodology.md", "figures.md", "related_work.md"]
    if level == AnalysisLevel.C:
        return [
            "summary.md", "key_findings.md", "methodology.md", "figures.md", "related_work.md",
            "limitations.md", "trends.md", "reproducibility.md",
        ]
    if level == AnalysisLevel.L1:
        return ["concepts.md"]
    if level == AnalysisLevel.L2:
        return ["concepts.md", "relations.md"]
    if level == AnalysisLevel.L3:
        return ["concepts.md", "relations.md", "hierarchy.md"]
    if level == AnalysisLevel.L4:
        return ["concepts.md", "relations.md", "hierarchy.md", "evidence.md"]
    return []


def _files_for_decision_level(level: str) -> list[str]:
    """Resolve a Decision.level string to the list of files to scaffold.

    Accepts the v2.0 (L1-L4) and v1.0 (A/B/C) level names. A/B/C
    return an empty list because the v1.0 legacy code path is not
    exercised by the v2.0 scaffold.
    """
    if level in {"A", "B", "C"}:
        return []
    try:
        return get_output_files(AnalysisLevel(level))
    except ValueError:
        return []


def prepare_decision_framework() -> Path:
    """Return the absolute Path to METHODOLOGY.md.

    The file contains the v2.0 decision framework (决策四问) which the
    LLM agent must read before invoking analyze_with_decision().
    """
    return Path(__file__).parent / "METHODOLOGY.md"


def analyze_with_decision(
    paper_id: str,
    mineru_content: str,
    decision: Decision,
    output_dir: Path,
) -> AnalysisResult:
    """Generate the file scaffold for a paper based on the agent's Decision.

    This is a pure file-scaffold function: it creates the output directory
    and one empty file per the level's file list. It does NOT call any
    LLM. LLM-driven content filling is a separate, later stage.

    The ``mineru_content`` parameter is accepted for API compatibility
    with the agent's call site but is not consumed at the scaffold stage.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    files = _files_for_decision_level(decision.level)
    written: dict[str, str] = {}
    for name in files:
        path = output_dir / name
        path.write_text("", encoding="utf-8")
        written[name] = ""

    try:
        level_enum = AnalysisLevel(decision.level)
    except ValueError:
        level_enum = AnalysisLevel.L1

    return AnalysisResult(
        paper_id=paper_id,
        level=level_enum,
        output_dir=output_dir,
        files=written,
        success=True,
    )


def get_analysis_prompt(level: AnalysisLevel) -> str:
    """Get the analysis prompt for a given level."""
    prompts = {
        AnalysisLevel.A: """
## 任务
基于以下 MinerU 输出的论文 markdown 内容，生成论文摘要和关键发现。

## 输出文件
1. summary.md - 论文摘要
2. key_findings.md - 3-5个关键发现

## 内容标准
- 摘要：简洁、准确概括论文核心贡献（300-500字）
- 关键发现：具体、可验证、与论文证据一致
""",
        AnalysisLevel.B: """
## 任务
基于以下 MinerU 输出的论文 markdown 内容，生成完整学术分析。

## 输出文件
1. summary.md - 论文摘要
2. key_findings.md - 5-8个关键发现
3. methodology.md - 创新点、技术路线、实验设计
4. figures.md - 主要图表及其意义
5. related_work.md - 与最相关工作的差异对比

## 内容标准
- 摘要：准确概括论文核心贡献
- 方法论：清晰描述创新点和技术路线
- 图表：解读主要图表传达的信息
- 相关工作：客观对比，指出优势和不足
""",
        AnalysisLevel.C: """
## 任务
基于以下 MinerU 输出的论文 markdown 内容，生成深度研究分析。

## 输出文件
Level B 所有文件 + 以下三个：
6. limitations.md - 数据、方法、结论的局限性
7. trends.md - 基于论文推断的未来研究方向
8. reproducibility.md - 代码/算法可复现性评估

## 内容标准
- 局限性：具体、有依据，不过分苛刻
- 趋势：基于论文证据推断，有逻辑支撑
- 复现：评估代码可用性、依赖环境、复现难度
""",
    }
    return prompts.get(level, prompts[AnalysisLevel.A])


def parse_mineru_output(content: str) -> dict:
    """Parse MinerU markdown output into structured sections."""
    lines = content.split("\n")
    title = ""
    abstract_lines = []
    body_lines = []
    in_abstract = False

    for i, line in enumerate(lines):
        if i == 0 and line.startswith("#"):
            title = line.lstrip("#").strip()
        elif line.startswith("##"):
            if in_abstract:
                in_abstract = False
                body_lines.append(line)
            elif "abstract" in line.lower():
                in_abstract = True
        elif in_abstract:
            abstract_lines.append(line)
        else:
            body_lines.append(line)

    return {
        "title": title,
        "abstract": " ".join(abstract_lines).strip(),
        "body": "\n".join(body_lines).strip(),
    }


def create_output_dir(paper_id: str) -> Path:
    """Create output directory for a paper's analysis results."""
    safe_id = paper_id.replace("/", "_").replace(":", "_")
    output_dir = DEFAULT_OUTPUT_DIR / safe_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def write_analysis_files(output_dir: Path, files: dict[str, str]) -> None:
    """Write analysis files to output directory."""
    for filename, content in files.items():
        filepath = output_dir / filename
        filepath.write_text(content, encoding="utf-8")


def analyze_summary(paper_id: str, mineru_content: str, output_dir: Path) -> AnalysisResult:
    """Run Level A (basic) analysis on a paper."""
    return _run_analysis(paper_id, AnalysisLevel.A, mineru_content, output_dir)


def _run_analysis(
    paper_id: str,
    level: AnalysisLevel,
    mineru_content: str,
    output_dir: Path,
) -> AnalysisResult:
    """Internal analysis runner - provides structure, agent provides LLM generation."""
    files = {}
    for filename in get_output_files(level):
        files[filename] = ""

    return AnalysisResult(
        paper_id=paper_id,
        level=level,
        output_dir=output_dir,
        files=files,
        success=True,
    )
