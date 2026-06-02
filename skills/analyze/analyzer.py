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
    """Analysis depth levels."""
    A = "A"  # Basic: summary + key findings
    B = "B"  # Complete: + methodology + figures + related work
    C = "C"  # Deep: + limitations + trends + reproducibility


@dataclass
class AnalysisResult:
    """Result of a paper analysis."""
    paper_id: str
    level: AnalysisLevel
    output_dir: Path
    files: dict[str, str] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


def get_output_files(level: AnalysisLevel) -> list[str]:
    """Get list of output files for a given analysis level."""
    base_files = ["summary.md", "key_findings.md"]
    if level == AnalysisLevel.A:
        return base_files
    elif level == AnalysisLevel.B:
        return base_files + ["methodology.md", "figures.md", "related_work.md"]
    else:  # Level.C
        return base_files + [
            "methodology.md", "figures.md", "related_work.md",
            "limitations.md", "trends.md", "reproducibility.md"
        ]


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
