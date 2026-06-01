# Analysis Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现完整的 paper 分析流水线，从搜索到分析报告生成，支持三级分析级别和多文件 Markdown 输出

**Architecture:** fetch 多源搜索 → 用户选择 → MinerU 转换 → 三级分析选择 → Markdown 多文件输出 + 临时 Q&A

**Tech Stack:** Python + MinerU + LLM (agent) + SKILL.md 提示词驱动

---

## File Structure

```
skills/analyze/
├── SKILL.md              # 分析提示词定义（修改）
├── __init__.py           # 模块导出（已存在）
├── analyzer.py           # 分析执行器（新建）
├── qa_logger.py          # Q&A 日志（已存在，临时会话用）
├── cache.py              # 论文缓存（已存在）
└── parallel_evaluator.py # 并行评估（已存在）

skills/fetch/
├── fetcher.py            # PDF 下载（需修改，添加 analyze 联动）
└── ...
```

---

## Task 1: 更新 SKILL.md 分析提示词

**Files:**
- Modify: `skills/analyze/SKILL.md`

- [ ] **Step 1: 添加分析级别定义**

在 SKILL.md 末尾添加：

```markdown
## Analysis Levels

### Level A - 基础分析
生成 `summary.md` 和 `key_findings.md`

### Level B - 完整学术分析
生成 `summary.md`, `key_findings.md`, `methodology.md`, `figures.md`, `related_work.md`

### Level C - 深度研究分析
生成 Level B 所有文件 + `limitations.md`, `trends.md`, `reproducibility.md`
```

- [ ] **Step 2: 添加 Level A 提示词**

```markdown
## Analysis Prompts

### Level A: Basic Analysis

**任务:** 基于以下 MinerU 输出的论文 markdown 内容，生成论文摘要和关键发现。

**输入:** MinerU markdown 内容

**输出要求:**
生成两个 Markdown 文件：

**1. summary.md**
```markdown
# 论文摘要

[300-500字的论文摘要，概括核心贡献]

## 基本信息
- **标题:** [论文标题]
- **作者:** [作者列表]
- **年份:** [年份]
- **来源:** [arXiv/PubMed等]
```

**2. key_findings.md**
```markdown
# 关键发现

## 发现 1
[具体发现描述，引用论文证据]

## 发现 2
...

## 发现 3
...
```
```

- [ ] **Step 3: 添加 Level B 提示词**

```markdown
### Level B: Complete Academic Analysis

**任务:** 基于 MinerU 输出的论文内容，生成完整学术分析。

**输出要求:**
生成五个 Markdown 文件（见 Level A + 以下）：

**3. methodology.md**
```markdown
# 方法论分析

## 创新点
[论文的主要创新点]

## 技术路线
[采用的技术方法和路线]

## 实验设计
[实验设置、数据集、评估指标]
```

**4. figures.md**
```markdown
# 图表解读

## 图 1: [标题]
- **内容:** [图表描述]
- **意义:** [该图表传达的关键信息]

## 表 1: [标题]
...
```

**5. related_work.md**
```markdown
# 相关工作对比

## 与 [工作A] 的比较
- **差异:** [描述主要差异]
- **优势:** [本文的优势]
- **劣势:** [本文的不足]

## 与 [工作B] 的比较
...
```

- [ ] **Step 4: 添加 Level C 提示词**

```markdown
### Level C: Deep Research Analysis

**任务:** 基于 MinerU 输出的论文内容，生成深度研究分析。

**输出要求:**
生成 Level B 所有文件 + 以下三个文件：

**6. limitations.md**
```markdown
# 论文局限性评估

## 数据局限性
[数据集相关限制]

## 方法局限性
[方法学上的限制]

## 结论局限性
[结论可推广性的限制]
```

**7. trends.md**
```markdown
# 研究趋势推断

## 当前研究状态
[论文在领域中的位置]

## 未来研究方向
[基于论文推断的潜在研究方向]

## 技术演进趋势
[该领域技术的发展趋势]
```

**8. reproducibility.md**
```markdown
# 复现分析

## 代码可用性
- **官方代码:** [是否开源、地址]
- **依赖环境:** [所需依赖]
- **复现难度:** [易/中/难]

## 算法复现要点
[复现时需要注意的关键点]
```

- [ ] **Step 5: 添加 Q&A 模式提示词**

```markdown
## Q&A Mode

当分析完成后，进入临时 Q&A 模式。用户可追问关于论文内容的问题。

### Q&A 上下文格式
```
## 当前论文
- **标题:** [论文标题]
- **已生成分析:** [summary.md, key_findings.md, ...]
- **MinerU 内容:** [markdown 内容摘要]

## 用户问题
[用户输入的问题]

## 回答要求
- 基于已有分析内容和 MinerU markdown 回答
- 如需引用原文，提供具体位置（如 "根据 summary.md 第 3 段..."）
- 超出上下文范围时，明确告知用户
```

- [ ] **Step 6: 添加 analyze 命令详细说明**

更新现有命令部分：

```markdown
### Analyze Commands

#### /paper-reader analyze
分析已下载的 paper。

**工作流程:**
1. Agent 调用 MinerU 转换 PDF → markdown
2. Agent 询问用户选择分析级别 (A/B/C)
3. Agent 基于提示词生成分析报告
4. 输出多文件 Markdown 至 `~/.paper-reader/outputs/<paper_id>/`
5. 进入临时 Q&A 模式

**用法:**
```
/paper-reader analyze <paper-id>
```

**分析级别:**
- Level A: 基础分析 (summary.md + key_findings.md)
- Level B: 完整学术分析 (+ methodology.md + figures.md + related_work.md)
- Level C: 深度研究分析 (+ limitations.md + trends.md + reproducibility.md)

**示例:**
```
/paper-reader analyze arxiv:2301.00001
```
```

- [ ] **Step 7: Commit**

```bash
git add skills/analyze/SKILL.md
git commit -m "feat(analyze): add multi-level analysis prompts to SKILL.md"
```

---

## Task 2: 实现 analyze/analyzer.py

**Files:**
- Create: `skills/analyze/analyzer.py`
- Test: `tests/skills/analyze/test_analyzer.py`

- [ ] **Step 1: 编写测试框架**

```python
"""Tests for analyzer module."""

import pytest
from pathlib import Path
from skills.analyze.analyzer import (
    AnalysisLevel,
    AnalysisResult,
    get_analysis_prompt,
    parse_mineru_output,
)

def test_analysis_level_enum():
    """Test AnalysisLevel enum values."""
    assert AnalysisLevel.A.value == "A"
    assert AnalysisLevel.B.value == "B"
    assert AnalysisLevel.C.value == "C"

def test_get_analysis_prompt_level_a():
    """Test Level A prompt contains expected file list."""
    prompt = get_analysis_prompt(AnalysisLevel.A)
    assert "summary.md" in prompt
    assert "key_findings.md" in prompt

def test_get_analysis_prompt_level_b():
    """Test Level B prompt includes methodology and figures."""
    prompt = get_analysis_prompt(AnalysisLevel.B)
    assert "methodology.md" in prompt
    assert "figures.md" in prompt
    assert "related_work.md" in prompt

def test_get_analysis_prompt_level_c():
    """Test Level C prompt includes all Level C specific files."""
    prompt = get_analysis_prompt(AnalysisLevel.C)
    assert "limitations.md" in prompt
    assert "trends.md" in prompt
    assert "reproducibility.md" in prompt

def test_parse_mineru_output_valid():
    """Test parsing valid MinerU markdown output."""
    content = "# Title\n\nAbstract text..."
    result = parse_mineru_output(content)
    assert result["title"] == "Title"
    assert "Abstract text" in result["abstract"]

def test_parse_mineru_output_empty():
    """Test parsing empty MinerU output."""
    result = parse_mineru_output("")
    assert result["title"] == ""
    assert result["abstract"] == ""

def test_analysis_result_dataclass():
    """Test AnalysisResult holds expected fields."""
    result = AnalysisResult(
        paper_id="test:123",
        level=AnalysisLevel.A,
        output_dir=Path("/tmp/test"),
        files={"summary.md": "# Summary\n"},
    )
    assert result.paper_id == "test:123"
    assert result.level == AnalysisLevel.A
    assert "summary.md" in result.files
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /home/user/obsidian/AI/claude\ code/paper-reader && pytest tests/skills/analyze/test_analyzer.py -v`
Expected: FAIL - module doesn't exist

- [ ] **Step 3: 实现 analyzer.py**

```python
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
    """Get list of output files for a given analysis level.

    Args:
        level: Analysis level

    Returns:
        List of output filenames
    """
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
    """Get the analysis prompt for a given level.

    The prompt is extracted from SKILL.md - this function returns
    the appropriate section based on the analysis level.

    Args:
        level: Analysis level

    Returns:
        The prompt string for the given level
    """
    # This returns the prompt section from SKILL.md
    # In practice, the agent reads SKILL.md directly
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
    """Parse MinerU markdown output into structured sections.

    Args:
        content: Raw markdown content from MinerU

    Returns:
        Dict with keys: title, abstract, body
    """
    lines = content.split("\n")
    title = ""
    abstract_lines = []
    body_lines = []
    in_abstract = False

    for i, line in enumerate(lines):
        if i == 0 and line.startswith("#"):
            title = line.lstrip("#").strip()
        elif "abstract" in line.lower():
            in_abstract = True
        elif in_abstract and line.startswith("##"):
            in_abstract = False
            body_lines.append(line)
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
    """Create output directory for a paper's analysis results.

    Args:
        paper_id: Unique paper identifier

    Returns:
        Path to the output directory
    """
    safe_id = paper_id.replace("/", "_").replace(":", "_")
    output_dir = DEFAULT_OUTPUT_DIR / safe_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def write_analysis_files(output_dir: Path, files: dict[str, str]) -> None:
    """Write analysis files to output directory.

    Args:
        output_dir: Directory to write files to
        files: Dict mapping filename to content
    """
    for filename, content in files.items():
        filepath = output_dir / filename
        filepath.write_text(content, encoding="utf-8")


# Convenience functions for external use
def analyze_summary(paper_id: str, mineru_content: str, output_dir: Path) -> AnalysisResult:
    """Run Level A (basic) analysis on a paper.

    Args:
        paper_id: Unique paper identifier
        mineru_content: Markdown content from MinerU
        output_dir: Directory for output files

    Returns:
        AnalysisResult with summary.md and key_findings.md
    """
    return _run_analysis(paper_id, AnalysisLevel.A, mineru_content, output_dir)


def _run_analysis(
    paper_id: str,
    level: AnalysisLevel,
    mineru_content: str,
    output_dir: Path,
) -> AnalysisResult:
    """Internal analysis runner.

    This function generates the analysis using the LLM via the agent.
    In practice, this is called by the agent which provides the LLM generation.

    Args:
        paper_id: Unique paper identifier
        level: Analysis level
        mineru_content: Markdown content from MinerU
        output_dir: Directory for output files

    Returns:
        AnalysisResult
    """
    # The actual LLM call is done by the agent
    # This function provides the structure and file writing
    files = {}
    for filename in get_output_files(level):
        files[filename] = ""  # Placeholder - filled by agent

    return AnalysisResult(
        paper_id=paper_id,
        level=level,
        output_dir=output_dir,
        files=files,
        success=True,
    )
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd /home/user/obsidian/AI/claude\ code/paper-reader && pytest tests/skills/analyze/test_analyzer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/analyze/analyzer.py tests/skills/analyze/test_analyzer.py
git commit -m "feat(analyze): add analyzer module with multi-level support"
```

---

## Task 3: 更新 fetch/fetcher.py 实现完整流水线

**Files:**
- Modify: `skills/fetch/fetcher.py:1-50` (添加 analyze 联动)

- [ ] **Step 1: 添加 analyze 联动函数**

在 `fetcher.py` 末尾添加：

```python
def search_and_analyze(topic: str, max_results: int = 10) -> dict:
    """Complete workflow: search papers, let user select, then analyze.

    This function coordinates the fetch + analyze workflow:
    1. Search papers from multiple sources
    2. Present results for user selection
    3. Download and analyze selected papers

    Args:
        topic: Search topic/keywords
        max_results: Maximum papers to search per source

    Returns:
        Dict with keys:
            - search_results: List of PaperResult from search
            - selected: List of selected paper IDs
            - analysis_results: Dict mapping paper_id to AnalysisResult
    """
    from skills.fetch.searcher import search_papers

    # Step 1: Search papers
    search_results = search_papers(topic, max_results)

    return {
        "search_results": search_results,
        "selected": [],  # User fills this
        "analysis_results": {},
    }
```

- [ ] **Step 2: 运行现有测试确保无破坏**

Run: `cd /home/user/obsidian/AI/claude\ code/paper-reader && pytest tests/skills/fetch/ -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add skills/fetch/fetcher.py
git commit -m "feat(fetch): add search_and_analyze workflow helper"
```

---

## Task 4: 创建测试骨架

**Files:**
- Create: `tests/skills/analyze/__init__.py`
- Modify: `tests/skills/analyze/test_analyzer.py` (扩展测试)

- [ ] **Step 1: 创建 __init__.py**

```python
"""Tests for analyze module."""
```

- [ ] **Step 2: 扩展测试覆盖**

添加更多边界测试到 `test_analyzer.py`：

```python
def test_create_output_dir():
    """Test output directory creation."""
    from skills.analyze.analyzer import create_output_dir
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = create_output_dir("test:123")
        assert out_dir.exists()
        assert "test_123" in str(out_dir)

def test_write_analysis_files(tmp_path):
    """Test writing multiple analysis files."""
    from skills.analyze.analyzer import write_analysis_files

    files = {
        "summary.md": "# Summary\nTest content",
        "key_findings.md": "# Key Findings\nFinding 1",
    }
    write_analysis_files(tmp_path, files)

    assert (tmp_path / "summary.md").exists()
    assert (tmp_path / "key_findings.md").exists()
    assert (tmp_path / "summary.md").read_text() == "# Summary\nTest content"
```

- [ ] **Step 3: 运行完整测试**

Run: `cd /home/user/obsidian/AI/claude\ code/paper-reader && pytest tests/skills/analyze/ -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add tests/skills/analyze/
git commit -m "test(analyze): add test coverage for analyzer module"
```

---

## 任务完成摘要

| Task | Description | Status |
|------|-------------|--------|
| 1 | 更新 SKILL.md 分析提示词 | ⬜ |
| 2 | 实现 analyze/analyzer.py | ⬜ |
| 3 | 更新 fetch/fetcher.py 联动 | ⬜ |
| 4 | 创建测试骨架 | ⬜ |
