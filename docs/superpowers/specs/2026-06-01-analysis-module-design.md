# Analysis Module Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan.

**Goal:** 实现完整的 paper 分析流水线，从搜索到分析报告生成

**Architecture:** 用户搜索主题 → fetch 多源搜索 → 用户选择 → MinerU 转换 → 三级分析选择 → Markdown 多文件输出 + 临时 Q&A

**Tech Stack:** Python + MinerU + LLM (agent) + SKILL.md 提示词驱动

---

## 一、工作流程

```
1. 用户提出搜索主题
2. Agent 调用 fetch 多源搜索 (arXiv/PubMed/Semantic Scholar/CrossRef)
3. 返回结果列表供用户选择 paper(s)
4. Agent 下载选中的 paper PDF
5. Agent 调用 MinerU 转换 PDF → markdown
6. Agent 根据 SKILL.md 提示词，询问用户选择分析级别 (A/B/C)
7. Agent 基于 MinerU 输出的 markdown 内容 + 对应级别提示词生成分析
8. 输出多文件 Markdown 报告
9. 进入临时 Q&A 模式，用户可追问（无持久化）
```

---

## 二、分析级别

### Level A - 基础分析

**输出文件：**
- `summary.md` - 论文摘要
- `key_findings.md` - 关键发现

### Level B - 完整学术分析

**输出文件：**
- `summary.md` - 论文摘要
- `key_findings.md` - 关键发现
- `methodology.md` - 方法论分析
- `figures.md` - 图表解读
- `related_work.md` - 相关工作对比

### Level C - 深度研究分析

**输出文件：**
- Level B 所有文件
- `limitations.md` - 论文局限性评估
- `trends.md` - 研究趋势推断
- `reproducibility.md` - 代码/算法复现分析

---

## 三、输出目录结构

```
~/.paper-reader/outputs/<paper_id>/
├── summary.md
├── key_findings.md
├── methodology.md      # Level B+
├── figures.md          # Level B+
├── related_work.md    # Level B+
├── limitations.md     # Level C
├── trends.md          # Level C
├── reproducibility.md # Level C
└── qa_session.json    # 临时 Q&A 日志（仅本次会话）
```

---

## 四、提示词设计

### 核心原则

- 每个分析级别一个**完整复合提示词**，一次 LLM 调用生成所有输出
- 提示词在 SKILL.md 中定义，驱动 agent 执行
- 提示词包含：
  1. 分析任务描述
  2. 输入内容说明（MinerU markdown）
  3. 输出格式要求（对应级别的文件结构）
  4. 内容质量标准

### Level A 提示词结构

```
## 任务
基于以下 MinerU 输出的论文 markdown 内容，生成论文摘要和关键发现。

## 输入内容
[MinerU markdown 内容]

## 输出要求
生成两个文件：
1. summary.md - 论文摘要（300-500字）
2. key_findings.md - 3-5个关键发现

## 内容标准
- 摘要：简洁、准确概括论文核心贡献
- 关键发现：具体、可验证、与论文证据一致
```

### Level B 提示词结构

```
## 任务
基于以下 MinerU 输出的论文 markdown 内容，生成完整学术分析。

## 输入内容
[MinerU markdown 内容]

## 输出要求
生成五个文件：
1. summary.md - 论文摘要
2. key_findings.md - 关键发现（5-8个）
3. methodology.md - 方法论分析（创新点、技术路线、实验设计）
4. figures.md - 图表解读（主要图表及其意义）
5. related_work.md - 相关工作对比（与本研究最相关的工作及差异）

## 内容标准
[同上，扩展至方法论和图表分析]
```

### Level C 提示词结构

```
## 任务
基于以下 MinerU 输出的论文 markdown 内容，生成深度研究分析。

## 输入内容
[MinerU markdown 内容]

## 输出要求
生成八个文件（Level B + 以下）：
6. limitations.md - 论文局限性（数据、方法、结论的局限性）
7. trends.md - 研究趋势（基于论文推断的未来研究方向）
8. reproducibility.md - 复现分析（代码/算法可复现性评估）

## 内容标准
[同上，扩展至深度分析]
```

---

## 五、Q&A 模式

### 行为定义

- 分析完成后，agent 进入临时 Q&A 模式
- 用户可就当前论文内容追问
- agent 基于已有分析内容和 MinerU markdown 回答
- **无持久化** - 会话结束或用户选择新 paper 时清除上下文

### Q&A 提示词

```
## Q&A 上下文
当前论文：[paper_title]
已生成分析：[对应级别的文件列表]
MinerU 内容：[已分析的 markdown 内容摘要]

## 用户问题
[用户输入]

## 回答要求
- 基于已有分析内容回答
- 如需引用原文，提供具体位置
- 超出上下文范围时，明确告知用户
```

---

## 六、MinerU 调用

### 输入

- PDF 文件路径：`~/.paper-reader/downloads/<paper_id>.pdf`

### 输出

- Markdown 内容保存至：`~/.paper-reader/temp/<paper_id>_mineru.md`
- 传递给分析模块使用

### 调用方式

```python
# 使用 magic-pdf 等 MinerU 工具链
subprocess.run([
    "magic-pdf",
    "-pdf", pdf_path,
    "-o", output_dir,
    "-l", "en"  # 或 "ch" for Chinese
])
```

---

## 七、文件命名规范

| 内容 | 文件名 | 层级 |
|------|--------|------|
| 摘要 | `summary.md` | A+ |
| 关键发现 | `key_findings.md` | A+ |
| 方法论 | `methodology.md` | B+ |
| 图表解读 | `figures.md` | B+ |
| 相关工作 | `related_work.md` | B+ |
| 局限性 | `limitations.md` | C |
| 研究趋势 | `trends.md` | C |
| 复现分析 | `reproducibility.md` | C |

---

## 八、错误处理

| 场景 | 处理方式 |
|------|----------|
| MinerU 转换失败 | 提示用户，询问是否尝试原始 markdown 分析或跳过 |
| LLM 生成失败 | 重试一次，仍失败则输出部分可用内容 + 错误说明 |
| 用户中断 Q&A | 优雅退出，不保存会话 |
| 分析内容过少 | 明确告知用户内容限制，分析结果可能不完整 |

---

## 九、与其他模块的关系

```
fetch/
├── searcher.py     # 多源搜索
├── fetcher.py      # PDF 下载
└── sources/        # 各数据源实现

analyze/
├── SKILL.md        # 分析提示词定义（核心）
├── analyzer.py     # 分析执行器（TODO）
├── qa_logger.py    # Q&A 日志（已存在，临时会话）
├── cache.py        # 论文缓存（已存在）
└── parallel_evaluator.py  # 并行评估（已存在）
```

---

## 十、实现任务（预估）

### Task 1: 更新 SKILL.md 分析提示词
- 定义 Level A/B/C 完整提示词
- 定义 Q&A 模式提示词

### Task 2: 实现 analyze/analyzer.py
- `analyze_paper(paper_id, level)` 主函数
- MinerU 调用封装
- 多文件输出生成
- 临时 Q&A 模式

### Task 3: 更新 fetch 流水线
- fetch + analyze 联动
- 用户选择后的自动流程

### Task 4: 测试
- 单元测试
- 集成测试
