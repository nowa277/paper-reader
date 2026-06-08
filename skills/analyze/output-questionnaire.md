# Output Questionnaire

## 何时用
**agent 必走流程的第 4 步**。在读完 METHODOLOGY + granularity + chunking-guide 后，**生成文件前必问用户 3 件事**。

## 3 件事

### Q1. 格式 (format)
- `wiki` (Obsidian Wiki, md + wikilinks)
- `md` (普通 markdown, 无 wikilinks)
- `json` (结构化, 适合程序消费)

**默认推荐**: `wiki` (obsidian 用户), `md` (KB 用户)

### Q2. 位置 (location)
常见选项:
- amber-agent KB: `~/obsidian/AI/amber-agent/knowledge_base/<doc>/`
- Obsidian Vault: 用户 vault 根目录
- 临时目录: `/tmp/<doc>/` 或 `~/Desktop/<doc>/`
- paper-reader 默认: **禁用** (要问)

**agent 应给的建议**（基于 use_case 推断）:
- use_case=obsidian → 推到 Obsidian Vault 子目录
- use_case=kb → 推到 amber-agent KB
- use_case=transient → 临时目录

### Q3. 图谱深度 (graph_depth)
- `L1`: 概念字典（默认）
- `L2`: + 关系
- `L3`: + 层级（KB 推荐）
- `L4`: + 证据（论文推荐）

**agent 应给的建议**（基于文档类型 + 规模）:
- 速查表 → L1
- 用户指南 → L2
- 教材/手册 → L3
- 学术论文 → L4

## 询问模板

agent 应这样问（**简洁、不啰嗦**）:

```
准备分析 <doc_name>（<page_count> 页）。
3 个问题：

1. 格式: wiki (Obsidian) / md (普通) / json?
2. 位置: 推到哪里？（建议: <agent 推荐>）
3. 图谱深度: L1 / L2 / L3 / L4?（建议: <agent 推荐>）

回答示例: "wiki, ~/obsidian/AI/<vault>/, L2"
```

## 用户回答解析

接受以下格式:
- 顺序回答: "wiki, ~/obsidian/AI/md/, L2"
- JSON: `{"format": "wiki", "location": "~/obsidian/AI/md/", "level": "L2"}`
- 简写: "w, md, l2"（首字母）
- 跳过某些: 跳过项用默认值

## 默认值（用户没指定时）

| 字段 | 默认 |
|---|---|
| format | `md` (中性) |
| location | `~/Desktop/<doc_name>_paper_reader/` (临时但可见) |
| level | 来自 decide-granularity 决策 |

## 反模式
- ❌ 不问用户就生成文件 → 写到用户不要的地方
- ❌ 默认写 `~/.paper-reader/` → 用户找不到
- ❌ 问 > 5 个问题 → 用户烦
- ❌ 不给推荐 → 用户决策成本高
- ❌ 假设用 obsidian → 用户可能用 Logseq / 别的

## 集成到 decide-output.md

output-questionnaire 收集的 3 个答案 → 喂给 decide-output.md 的 4 个输入变量:
- `{use_case}` ← 推断 (obsidian/kb/transient)
- `{location}` ← Q2 答案
- `{level}` ← Q3 答案
- `{doc_name}` ← agent 自取

## 边角案例

### 用户说"随便"/"你定"
- 全部用默认值
- agent 显式告知选了哪 3 个默认值

### 用户说"和上次一样"
- agent 记住上次 3 个答案
- 用相同配置

### 用户说"先试一个"
- use_case=transient
- location=/tmp
- level=L1（最快）

## 完整流程

```
[1-3] 已读 METHODOLOGY + granularity + chunking-guide
[4]   调 output-questionnaire.md → 问 3 件事
      ↓ (用户回答)
[5]   调 decision_prompts/decide-*.md → 4 个 LLM 决策
[6]   构造 Decision 对象
[7]   调 analyze_with_decision(decision)
[8]   agent 自己的 LLM 填内容
```
