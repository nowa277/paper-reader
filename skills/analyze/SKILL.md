# Analyze Sub-Skill

Handles paper analysis, summarization, and insight extraction.

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
