# Analyze Sub-Skill (v2.0)

**决策驱动的 paper analysis.** v1.0 (Level A/B/C) 仍可用，向后兼容。

## v2.0 流程入口

Agent 拿到 PDF / MD / 解析后内容后必须按以下顺序执行：

1. **读** [METHODOLOGY.md](./METHODOLOGY.md) — v2.0 决策框架（"宪法"）
2. **答 4 问** — Q1 文档类型 / Q2 规模结构 / Q3 用户意图 / Q4 存哪里
3. **跑 4 个 decision prompt** — `decision_prompts/decide-{granularity,chunking,graph,output}.md`
4. **调 API** — `analyze_with_decision(paper_id, mineru_content, decision, output_dir)`

详细 8 步流程见 [§2](#2-v20-决策驱动流程-new)。

---

## §2. v2.0 决策驱动流程 (NEW)

### 2.1 强制 8 步（来自 METHODOLOGY §七）

```
[1] 读 METHODOLOGY.md
    ↓
[2] 读 granularity/level-X-*.md (X = Q1 决策的档位)
    ↓
[3] 读 chunking-guide.md → 决策切分策略
    ↓
[4] 调 output-questionnaire.md → 问用户 3 件事 (format/location/level)
    ↓
[5] 调 decision_prompts/decide-*.md → 4 个 LLM 决策 prompt
    ↓
[6] 构造 Decision 对象
    ↓
[7] 调 analyze_with_decision(decision) → 生成文件脚手架
    ↓
[8] agent 自己的 LLM 填文件内容
```

**禁止跳过任何一步**（特别是 [1] 和 [4]）。

### 2.2 `Decision` dataclass signature

`skills/analyze/analyzer.py` 里的 dataclass（9 字段）：

```python
@dataclass
class Decision:
    level: str = "L1"            # "L1" | "L2" | "L3" | "L4" | "A" | "B" | "C"
    base_dir: Path = Path()      # 输出根目录
    doc_name: str = ""           # 文档名（用于子目录）
    format: str = "markdown"     # "markdown" | "wiki" | "json"
    use_case: str = "transient"  # "obsidian" | "kb" | "transient"
    chunks: list | None = None   # 切分结果（来自 decide-chunking）
    relations: bool = False      # 是否抽关系
    hierarchy: bool = False      # 是否抽层级
    evidence: bool = False       # 是否抽证据
```

| 字段 | 决策来源 | 说明 |
|---|---|---|
| `level` | `decide-granularity.md` | L1-L4（v2.0）或 A/B/C（v1.0 向后兼容） |
| `base_dir` | `output-questionnaire.md` Q2 | 用户指定输出位置 |
| `doc_name` | agent 自取 | 文档名 → 子目录名 |
| `format` | `output-questionnaire.md` Q1 | `wiki`/`md`/`json` |
| `use_case` | `output-questionnaire.md` Q1 → 推断 | `obsidian`/`kb`/`transient` |
| `chunks` | `decide-chunking.md` | 切分后 chunks 列表 |
| `relations`/`hierarchy`/`evidence` | `decide-graph.md` | 抽哪些东西 |
| （`relation_types`, `ontology_style` 等） | 暂存于 `chunks` 或外部 YAML | v2.0 扩展点 |

### 2.3 L1-L4 档位速览

| 档 | 目标 | 输出文件 | Token 预算 | 切分要求 | 典型场景 |
|---|---|---|---|---|---|
| **L1** | 概念字典 | `concepts.md` | < 1k | 可一次过 | 速查表、API 概览 |
| **L2** | 概念 + 关系 | `concepts.md` + `relations.md` | ~2-5k | ≤ 200 页可一次过 | 用户指南、教程 |
| **L3** | 完整 ontology | `concepts.md` + `relations.md` + `hierarchy.md` | ~10-50k | **必须分块** | 教材、大型手册、KB 建设 |
| **L4** | 全文图谱 | `concepts.md` + `relations.md` + `hierarchy.md` + `evidence.md` | ~50-200k | **必须分块** | 学术论文、深度分析 |

详细定义见 [granularity/level-1-concepts.md](./granularity/level-1-concepts.md) ~ [level-4-full-graph.md](./granularity/level-4-full-graph.md)。

### 2.4 何时用 L1 / L2 / L3 / L4

| 文档类型 | 规模 | 首选档 | 理由 |
|---|---|---|---|
| 速查表 / cheat sheet | 1-10 页 | **L1** | 概念字典足够 |
| 用户指南 (user guide) | 10-200 页 | **L2** | 概念+关系足够 |
| API 文档 | 50-500 页 | **L2**-L3 | 看深度 |
| 教材 / 教科书 | 200-1000 页 | **L3** | 需要 hierarchy |
| 大型手册 (amber 1112 页) | 500+ 页 | **L3** | 同上 |
| 学术论文 | 10-30 页 | **L4** | 需要 evidence |

**自检**（用户没说清时按此推）：

- 用户没明确说要 KG → 默认 **L2**
- 明确说"深度"/"详细"/"做 KB" → 升 **L3**
- 明确说"论文"/"原文"/"逐句" → **L4**
- 明确说"快"/"概览" → **L1**

详细决策表见 [METHODOLOGY.md §三 Q1](./METHODOLOGY.md#三决策四问agent-必答)。

---

## §3. v2.0 Public API

API 全部在 `skills/analyze/analyzer.py`。三个核心函数 + 1 个 enum + 1 个 dataclass。

### 3.1 `prepare_decision_framework() -> Path`

返回 `METHODOLOGY.md` 的绝对路径。**Agent 必先调用此函数拿到路径并读完整内容**，再做任何决策。

```python
from skills.analyze.analyzer import prepare_decision_framework

methodology_path = prepare_decision_framework()
# → /home/user/obsidian/AI/claude code/paper-reader/skills/analyze/METHODOLOGY.md

# agent 然后必须 read_file(methodology_path) 并按 §七 8 步走
```

### 3.2 `analyze_with_decision(...) -> AnalysisResult`

按 `Decision` 生成文件脚手架（**只建空文件，不调 LLM**）。LLM 填内容是 agent 自己的事。

```python
from pathlib import Path
from skills.analyze.analyzer import (
    analyze_with_decision,
    Decision,
    AnalysisLevel,
)

# 例：amber 用户指南 200 页, L2, 推 amber-agent KB
decision = Decision(
    level="L2",
    base_dir=Path("~/obsidian/AI/amber-agent/knowledge_base/amber24/"),
    doc_name="amber24",
    format="markdown",
    use_case="kb",
    chunks=[{"start": 0, "end": 50}, {"start": 50, "end": 200}],
    relations=True,     # L2 必开
    hierarchy=False,    # L2 不开
    evidence=False,     # L2 不开
)

result = analyze_with_decision(
    paper_id="amber24",
    mineru_content="<已读到的 markdown 内容>",  # scaffold 阶段不用，但 API 要
    decision=decision,
    output_dir=Path("~/obsidian/AI/amber-agent/knowledge_base/amber24/"),
)

# result.files == {"concepts.md": "", "relations.md": ""}
# result.success == True
# agent 下一步：自己调 LLM 填这两个文件
```

### 3.3 `get_output_files(level) -> list[str]`

返回某个档位的输出文件名列表。支持 **L1-L4（v2.0）** 和 **A/B/C（v1.0 向后兼容）**。

```python
from skills.analyze.analyzer import get_output_files, AnalysisLevel

# v2.0
get_output_files(AnalysisLevel.L1)  # ['concepts.md']
get_output_files(AnalysisLevel.L2)  # ['concepts.md', 'relations.md']
get_output_files(AnalysisLevel.L3)  # ['concepts.md', 'relations.md', 'hierarchy.md']
get_output_files(AnalysisLevel.L4)  # ['concepts.md', 'relations.md', 'hierarchy.md', 'evidence.md']

# v1.0 向后兼容
get_output_files(AnalysisLevel.A)   # ['summary.md', 'key_findings.md']
get_output_files(AnalysisLevel.B)   # 5 files
get_output_files(AnalysisLevel.C)   # 8 files
```

### 3.4 `AnalysisLevel` enum

```python
class AnalysisLevel(Enum):
    # v1.0 旧档（method-light summarization）
    A = "A"  # basic: summary + key findings
    B = "B"  # + methodology + figures + related work
    C = "C"  # + limitations + trends + reproducibility
    # v2.0 新档（method-driven, decision-framework-backed）
    L1 = "L1"  # concepts only
    L2 = "L2"  # concepts + relations
    L3 = "L3"  # concepts + relations + hierarchy (ontology)
    L4 = "L4"  # concepts + relations + hierarchy + evidence
```

### 3.5 Decision YAML 输出 schema

4 个 `decision_prompts/decide-*.md` 提示的 YAML 输出 schema：

- **granularity** — [decision_prompts/decide-granularity.md](./decision_prompts/decide-granularity.md)
  → `level` / `reasoning` / `alternative`
- **chunking** — [decision_prompts/decide-chunking.md](./decision_prompts/decide-chunking.md)
  → `strategy` / `chunk_size` / `overlap` / `reasoning`
- **graph** — [decision_prompts/decide-graph.md](./decision_prompts/decide-graph.md)
  → `extract_relations` / `extract_hierarchy` / `extract_evidence` / `relation_types` / `ontology_style` / `relation_extraction_granularity` / `reasoning`
- **output** — [decision_prompts/decide-output.md](./decision_prompts/decide-output.md)
  → `files` / `base_dir` / `format` / `wikilinks` / `cross_links` / `reasoning`

**完整 Decision 流程示例**（amber 1112 页 PDF → KB，L3）：

```yaml
# decide-granularity.md 输出
level: L3
reasoning: |
  amber 手册 1112 页, 文档类型"大型手册", 章节清晰
  (Q1 表第 3 行: 500+ 页手册首选 L3, 需要 hierarchy)
alternative: |
  备选 L2: 若用户说"不要 KB"则降 L2 (skip hierarchy.md)
  升 L4: 若用户后续说"要 evidence 追溯"则升 L4

# decide-chunking.md 输出
strategy: by_chapter_with_overlap
chunk_size: null  # by_chapter 不填
overlap: 2        # 章节间重叠 2 页
reasoning: |
  1112 页 + 30 章 + 概念跨章 → 章节切分 + 重叠
  (Q2 表: 1000+ 页强制按章节切分; amber 概念跨章需 overlap)

# decide-graph.md 输出
extract_relations: true
extract_hierarchy: true
extract_evidence: false  # L3 不抽 evidence
relation_types: [contains, uses, part_of, is_a]
ontology_style: taxonomy
relation_extraction_granularity: concept  # L3 用 concept-level
reasoning: |
  L3 KB 场景: relations + hierarchy 必抽
  (手册默认关系类型: contains, uses, part_of)
  L3 不抽 evidence, 所以 granularity=concept

# decide-output.md 输出
files: [concepts.md, relations.md, hierarchy.md]
base_dir: ~/obsidian/AI/amber-agent/knowledge_base/amber24/
format: markdown
wikilinks: false
cross_links: true
reasoning: |
  L3 输出 3 文件 (per §四)
  amber-agent KB 用 markdown 不用 wiki (KB 通常不用 wikilink)
  L3 + use_case=kb → cross_links=true (KB 需要跨文档链接)
```

最终构造的 `Decision` 对象：

```python
Decision(
    level="L3",
    base_dir=Path("~/obsidian/AI/amber-agent/knowledge_base/amber24/"),
    doc_name="amber24",
    format="markdown",
    use_case="kb",
    chunks=[{"strategy": "by_chapter_with_overlap", "overlap": 2,
             "chapters": [...30 章...]}],
    relations=True,
    hierarchy=True,
    evidence=False,
)
```

---

## §4. amber-agent KB 衔接 (NEW)

**核心原则**: 检测到 amber-agent `mineru_output/<doc>/vlm/` 产物 → **优先复用，不重跑 MinerU**。

### 4.1 为什么需要衔接

amber-agent 已经把 PDF 用 MinerU 解析过，产物在：

```
mineru_output/<doc>/
├── vlm/                  ← amber-agent 改名的标准产物
│   ├── <basename>.md     # MinerU 解析后的 markdown
│   ├── content_list.json # 区块元数据
│   ├── images/           # 提取的图片
│   └── *.pdf, layout*.json, ...
└── hybrid_auto/          ← MinerU 2.5 原始子目录名 (vllm 0.13.0+)
    └── (同 vlm/ 结构)
```

`amber_agent_adapter.py` **两种命名都识别**（`vlm/` 优先 → fallback `hybrid_auto/`）。

### 4.2 Public API

```python
from skills.analyze.amber_agent_adapter import (
    detect_amber_agent_vlm_output,
    read_vlm_output,
    AmberAgentVLMNotFound,
)

# 检测
has_vlm = detect_amber_agent_vlm_output("mineru_output/amber24")
# → True (找到 vlm/ 或 hybrid_auto/)

# 读取
if has_vlm:
    markdown, metadata = read_vlm_output("mineru_output/amber24")
    # markdown: <basename>.md 的全文
    # metadata: content_list.json 解析后的 dict ({} 表示缺失)
```

**异常**:

- `AmberAgentVLMNotFound` — `vlm/` 和 `hybrid_auto/` 都不存在
- `FileNotFoundError` — 子目录存在但 `<basename>.md` 缺失

### 4.3 完整 e2e 流程示意

amber 1112 页 PDF → amber-agent KB：

```python
from pathlib import Path
from skills.analyze.amber_agent_adapter import (
    detect_amber_agent_vlm_output,
    read_vlm_output,
)
from skills.analyze.analyzer import (
    prepare_decision_framework,
    analyze_with_decision,
    Decision,
)

# [前置] 假设 amber-agent 已跑完 MinerU, 产物在:
#   mineru_output/amber24/vlm/amber24.md
#   mineru_output/amber24/vlm/content_list.json

# STEP 1: 复用 amber-agent 的解析结果
if detect_amber_agent_vlm_output("mineru_output/amber24"):
    md, meta = read_vlm_output("mineru_output/amber24")
    # md 已经是 MinerU 解析好的 markdown
else:
    raise RuntimeError("Run MinerU first (or amber-agent didn't produce output)")

# STEP 2: 读 METHODOLOGY + 跑 4 问 + 4 decision prompts
# (省略 agent 内部决策过程, 见 §2.1 8 步流程)
methodology_path = prepare_decision_framework()  # agent 读这个文件

# STEP 3: 构造 Decision (L3, KB 场景)
decision = Decision(
    level="L3",
    base_dir=Path("~/obsidian/AI/amber-agent/knowledge_base/amber24/"),
    doc_name="amber24",
    format="markdown",
    use_case="kb",
    chunks=[...],   # from decide-chunking
    relations=True,
    hierarchy=True,
    evidence=False,
)

# STEP 4: 建文件脚手架
result = analyze_with_decision(
    paper_id="amber24",
    mineru_content=md,                # amber-agent 已解析的 markdown
    decision=decision,
    output_dir=decision.base_dir,
)
# → result.files = {"concepts.md": "", "relations.md": "", "hierarchy.md": ""}

# STEP 5: agent 自己的 LLM 分块填 3 个文件 (此步不在本 skill API 范围)
```

### 4.4 与 §5 v1.0 衔接

v1.0 A/B/C 也支持 amber-agent 复用——把 `read_vlm_output()` 拿到的 markdown 喂给 `analyze_summary()` 即可。详见 [§5 v1.0 章节](#5-v10-向后兼容-仍可用)。

---

## §5. v1.0 (向后兼容, 仍可用)

> **以下 v1.0 内容** 完整保留, **仍可用, 向后兼容**。新代码推荐用 v2.0 L1-L4。

## Analysis Levels

### Level A — 基础分析 (Basic Analysis)
**Output files:**
- summary.md
- key_findings.md

**Use case:** Quick overview when you need to understand the paper's main contribution.

### Level B — 完整学术分析 (Complete Academic Analysis)
**Output files:**
- summary.md
- key_findings.md
- methodology.md
- figures.md
- related_work.md

**Use case:** Standard analysis for literature review, thesis writing, or comprehensive paper understanding.

### Level C — 深度研究分析 (Deep Research Analysis)
**Output files:** Level B files plus:
- limitations.md
- trends.md
- reproducibility.md

**Use case:** Research planning, collaboration, or when you need to critically evaluate the paper's long-term impact and feasibility.

## Analysis Prompts

### Level A Prompt

```
# 论文基础分析

## 任务
对以下论文进行基础分析，生成摘要和关键发现。

## 论文信息
- **标题**: {title}
- **作者**: {authors}
- **发布年份**: {year}
- **来源**: {source}

## 分析要求

### 1. 生成摘要 (summary.md)
```markdown
# 论文摘要

## 基本信息
- **标题**: {title}
- **作者**: {authors}
- **发布年份**: {year}
- **来源**: {source}
- **arXiv ID**: {arXiv_id}

## 摘要内容
{paper_abstract}
```

### 2. 提取关键发现 (key_findings.md)
```markdown
# 关键发现

## 发现 1: {finding_1_title}
{描述}

## 发现 2: {finding_2_title}
{描述}

## 发现 3: {finding_3_title}
{描述}
```
```

---

### Level B Prompt

```
# 论文完整学术分析

## 任务
对以下论文进行完整的学术分析，生成多维度报告。

## 论文信息
- **标题**: {title}
- **作者**: {authors}
- **发布年份**: {year}
- **来源**: {source}

## 分析要求

### 1. summary.md (同 Level A 格式)
```markdown
# 论文摘要

## 基本信息
- **标题**: {title}
- **作者**: {authors}
- **发布年份**: {year}
- **来源**: {source}
- **arXiv ID**: {arXiv_id}

## 摘要内容
{paper_abstract}
```

### 2. key_findings.md (同 Level A)
```markdown
# 关键发现

## 发现 1: {finding_1_title}
{描述}

## 发现 2: {finding_2_title}
{描述}

## 发现 3: {finding_3_title}
{描述}
```

### 3. methodology.md
```markdown
# 方法论分析

## 创新点
{论文的主要技术创新点}

## 技术路线
{方法的技术路线描述}

## 实验设计
{实验设置、数据集、评估指标}
```

### 4. figures.md
```markdown
# 图表解读

## 图1: {figure_1_title}
{图表内容描述和分析}

## 表1: {table_1_title}
{表格内容描述和分析}
```

### 5. related_work.md
```markdown
# 相关工作对比

## 核心对比
{与相关工作的主要差异和贡献}
```

---

### Level C Prompt

```
# 论文深度研究分析

## 任务
对以下论文进行深度研究分析，包括局限性评估和复现性分析。

## 论文信息
- **标题**: {title}
- **作者**: {authors}
- **发布年份**: {year}
- **来源**: {source}

## 分析要求

在 Level B 所有文件基础上，额外生成：

### 6. limitations.md
```markdown
# 论文局限性评估

## 数据局限性
{数据集相关限制}

## 方法局限性
{方法论相关限制}

## 结论局限性
{结论可推广性限制}
```

### 7. trends.md
```markdown
# 研究趋势推断

## 发展趋势
{从论文推断的未来研究方向}

## 潜在应用
{论文技术的潜在应用场景}
```

### 8. reproducibility.md
```markdown
# 复现分析

## 代码可用性
{代码/模型是否公开可用}

## 算法复现要点
{复现所需的关键要素和步骤}
```
```

## Q&A Mode

Q&A Mode provides interactive question answering after analysis generation.

### 特性
- **Temporary session:** No persistence between sessions
- **Context aware:** Uses current paper info as context
- **Direct answers:** Concise, cited responses

### Q&A Context Format
```markdown
## 当前论文
- **标题**: {title}
- **作者**: {authors}
- **年份**: {year}

## 已生成报告
- summary.md ✓
- key_findings.md ✓
- methodology.md ✓
- figures.md ✓
- related_work.md ✓
- limitations.md ✓ (Level C only)
- trends.md ✓ (Level C only)
- reproducibility.md ✓ (Level C only)

## 可用命令
- 提问: 直接输入问题
- 退出: 输入 "exit" 或 "quit"
```

### Response Requirements
- Answer based on paper content and generated reports
- Cite specific sections when relevant
- If information is not available, state clearly
- Keep responses concise and focused

## Commands

### Full Workflow
```
MinerU paper extraction → User selects analysis level → 
Generate reports → Q&A mode available
```

### Usage
```
/paper-reader analyze <paper-id>
```

### Analysis Level Selection
After paper extraction, user will be prompted to select:
- **Level A** — Quick summary + key findings (2 files)
- **Level B** — Complete academic analysis (5 files)
- **Level C** — Deep research analysis (8 files)

### Command Reference
- `analyze <paper>` — Analyze a paper at default level (Level B)
- `analyze --level a <paper>` — Analyze at Level A
- `analyze --level b <paper>` — Analyze at Level B
- `analyze --level c <paper>` — Analyze at Level C
- `analyze summary <paper>` — Generate summary only
- `analyze key-findings <paper>` — Extract key findings only
- `analyze methodology <paper>` — Analyze methodology only

---

## §6. v1.0 vs v2.0 选择指南

| 场景 | 文档特征 | 选 v1.0 | 选 v2.0 |
|---|---|---|---|
| 论文 / 快速概览 | 10-30 页论文，要摘要+关键发现 | **A** | — |
| 文献综述 / 论文深入 | 10-30 页，要全面学术分析 | **B** | — |
| 科研合作 / 批判评估 | 论文，要 limitations/trends/reproducibility | **C** | — |
| **速查表 / cheat sheet** | 1-10 页，只看概念 | — | **L1** |
| **教程 / 用户指南** | 10-200 页，要概念+关系 | — | **L2** |
| **教材 / 手册 / KB 建设** | 200-1000+ 页，要完整 ontology（amber 手册） | — | **L3** |
| **学术论文深度分析** | 10-30 页，要 evidence 追溯 | — | **L4** |

**决策口诀**:

- 用户要"摘要"/"总结"/"分析论文" → v1.0 (A/B/C)
- 用户要"提取概念"/"建 KB"/"做知识图"/"复习" → v2.0 (L1-L4)
- 用户没说清 → 默认 **v2.0 L2**（更现代，向前兼容）

详细决策树见 [METHODOLOGY.md §三 Q1](./METHODOLOGY.md#三决策四问agent-必答)。

---

## §7. 相关文档

### 方法论 & 决策框架

- [METHODOLOGY.md](./METHODOLOGY.md) — v2.0 决策框架（"宪法"）
- [output-questionnaire.md](./output-questionnaire.md) — 问用户 3 件事（format/location/level）
- [chunking-guide.md](./chunking-guide.md) — 4 切分策略 + 滑动窗口 + 章节检测

### 粒度定义（per L1-L4）

- [granularity/level-1-concepts.md](./granularity/level-1-concepts.md) — L1 概念字典
- [granularity/level-2-concepts-relations.md](./granularity/level-2-concepts-relations.md) — L2 概念+关系
- [granularity/level-3-ontology.md](./granularity/level-3-ontology.md) — L3 完整 ontology
- [granularity/level-4-full-graph.md](./granularity/level-4-full-graph.md) — L4 全文图谱

### Decision Prompts (LLM 决策 schema)

- [decision_prompts/decide-granularity.md](./decision_prompts/decide-granularity.md) — 选 L1-L4
- [decision_prompts/decide-chunking.md](./decision_prompts/decide-chunking.md) — 选切分策略
- [decision_prompts/decide-graph.md](./decision_prompts/decide-graph.md) — 选图谱深度
- [decision_prompts/decide-output.md](./decision_prompts/decide-output.md) — 选输出文件+位置

### 代码

- [analyzer.py](./analyzer.py) — `Decision` / `prepare_decision_framework` / `analyze_with_decision` / `get_output_files` / `AnalysisLevel`
- [amber_agent_adapter.py](./amber_agent_adapter.py) — `detect_amber_agent_vlm_output` / `read_vlm_output` (复用 MinerU 产物)

### Subagent 并行管理 (v2.0 Module 4)

- [subagent-decision-tree.md](./subagent-decision-tree.md) — 何时拆分子 agent (决策树)
- [subagent-concurrency-strategy.md](./subagent-concurrency-strategy.md) — IO/Compute/Mixed 并发配置
- [subagent-result-aggregation.md](./subagent-result-aggregation.md) — 结果合并策略 (Concat/Dedupe/Synthesize)
- [subagent-failure-handling.md](./subagent-failure-handling.md) — L1/L2/L3 三层验证 + 重试策略
- [subagent-granularity-patterns.md](./subagent-granularity-patterns.md) — Map-Reduce / Pipeline / ToT / Hierarchical 4 种模式
- [subagent-case-studies.md](./subagent-case-studies.md) — 5 个真实场景案例
- [subagent_policy.py](./subagent_policy.py) — SubagentPolicy 代码实现 (~250 行)
- [test_subagent_policy.py](../tests/skills/analyze/test_subagent_policy.py) — 25 个测试用例

### 质量验证与门控 (v2.0 Plan 3)

- [verification/token_estimator.py](./verification/token_estimator.py) — Token 计数触发并行模式
- [verification/levels.py](./verification/levels.py) — L1/L2/L3 验证层实现 (~350 行)
- [verification/runner.py](./verification/runner.py) — 反馈循环 + 重试逻辑 (~200 行)
- [verification/audit_checklist.md](./verification/audit_checklist.md) — 15 条验收清单
- [verification/feedback_loop.md](./verification/feedback_loop.md) — 3 层门控流程图 + 反模式
- [verification/config_*.yaml](./verification/) — 5 个 PDF 验证配置 (amber26/AlphaFold/Go/ColabFold/AMBER_Tutorials)
- [tests/skills/verification/test_verification.py](../tests/skills/analyze/verification/test_verification.py) — 45 个测试用例

### 图像嵌入 (v2.0 Plan 4)

- [image_embedder.py](./image_embedder.py) — 图像提取、元数据追踪、嵌入策略实现 (~350 行)
- [image_config.yaml](./image_config.yaml) — 嵌入配置 (大小阈值、格式、输出目录)
- [image-embedding-guide.md](./image-embedding-guide.md) — 使用指南 + 反模式
- [tests/skills/analyze/test_image_embedder.py](../tests/skills/analyze/test_image_embedder.py) — 20+ 测试用例

### E2E 集成 (v2.0 Plan 5)

- [e2e_integration.py](./e2e_integration.py) — E2E 管道编排 (PDF → VLM → 分析 → 验证 → 输出, ~450 行)
- [e2e_config.yaml](./e2e_config.yaml) — 管道配置 (阶段定义、重试策略、输出格式选项)
- [e2e-integration-guide.md](./e2e-integration-guide.md) — 使用指南 + 故障排除 + 性能考虑
- [tests/skills/analyze/test_e2e_integration.py](../tests/skills/analyze/test_e2e_integration.py) — 22 个���试用例 (全部通过)
