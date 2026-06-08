# Paper Reader Analyze — 方法论 (v2.0)

> **强制**: Agent 在调用 `analyze_with_decision()` 之前必须读完本文件

## 一、定位

本方法论文档是 `paper-reader` 的 `analyze` 子技能 v2.0 的"宪法"——它**不是脚本**，是给 LLM agent 的**决策框架**。Agent 拿到用户请求后，必须按本文档的决策树 / 反模式走。

**核心原则**：
- Skill = 方法论 + 决策框架
- Agent = 拿方法论做判断的执行者
- 代码 = 只在 agent 决策后才介入的轻量工具

v1.1 的"3 档死板枚举"已废弃。v2.0 的 L1-L4 是**档位参考**，不是**唯一选择**——agent 看完文档后可向用户提议**混合档**（如 L2 默认 + 关键章节升 L4）。

## 二、何时触发

满足以下任一条件 → 必须走本方法论：
1. 用户给 PDF 路径 / URL / 已解析 MD 路径
2. 用户说"分析"/"总结"/"提取概念"/"建知识图"/"做 wiki"/"做复习笔记"等动词
3. amber-agent 或其他 skill 调用本技能

## 三、决策四问（agent 必答）

### Q1. 文档是什么类型？

| 文档类型 | 典型规模 | 首选档 | 理由 |
|---|---|---|---|
| 用户指南 (user guide) | 10-200 页 | L2 | 概念+关系足够 |
| 教材 / 教科书 | 200-1000 页 | L3 | 需要 hierarchy |
| 大型手册 (amber 1112 页) | 500+ 页 | L3 | 同上 |
| 学术论文 | 10-30 页 | L4 | 需要 evidence |
| API 文档 | 50-500 页 | L2-L3 | 看深度 |
| 速查表 / cheat sheet | 1-10 页 | L1 | 概念字典足够 |

**自检**：
- 用户没明确说要 KG → 默认 L2
- 明确说"深度"/"详细"/"做 KB" → 升 L3
- 明确说"论文"/"原文"/"逐句" → L4
- 明确说"快"/"概览" → L1

### Q2. 文档多大 / 结构化程度？

| 规模 + 结构 | 切分策略 |
|---|---|
| < 50 页 + 章节清晰 | **不切分** |
| 50-200 页 + 章节清晰 | **按章节切分** |
| 200+ 页 + 有明确章节 | **按章节切分**（不按 token） |
| 200+ 页 + 无结构 / 全是表 / 公式密 | **按页切分 + 滑动窗口重叠** |
| 1000+ 页 | **强制按章节切分**（不切分不可能 1 次过） |

详细见 `chunking-guide.md`。

### Q3. 产 Wiki 还是裸 MD？要不要 KG？

| 用户说法 | 输出 |
|---|---|
| "做笔记"/"复习" | Obsidian Wiki (md + wikilinks) |
| "建图"/"建 KG" | MD + 关系表 (relations.md) |
| "提取概念" | 纯概念字典 (concepts.md) |
| "分析论文" | concepts + relations + hierarchy + evidence (L4 全套) |

**不规定格式**——根据用户意图走。

### Q4. 存哪里？

**必须问用户**。不允许默认写 `~/.paper-reader/`。常见选项：
- amber-agent KB（`knowledge_base/<doc>/`）
- Obsidian Vault（用户 vault 路径）
- 临时目录（`/tmp/<doc>/`）

## 四、4 档粒度定义

### L1 — 概念字典

- **目标**：快速了解文档讲了什么
- **输出文件**：`concepts.md`
- **内容**：概念名 + 1-2 句话定义 + 出现章节
- **适用**：速查表、API 概览、入门了解
- **耗时**：< 1k tokens
- **不切分要求**：可直接一次过

### L2 — 概念 + 关系

- **目标**：建立小型知识图
- **输出文件**：`concepts.md` + `relations.md`
- **新增**：概念间关系（"X 包含 Y"/"X 导致 Y"/"X 是 Y 的子类"）
- **适用**：用户指南、教程
- **耗时**：~2-5k tokens
- **不切分要求**：≤ 200 页可一次过

### L3 — 完整 ontology

- **目标**：支持 amber-agent KB 长期使用
- **输出文件**：`concepts.md` + `relations.md` + `hierarchy.md`
- **新增**：分类层级（is-a / part-of / uses）
- **适用**：教材、手册、大型 reference
- **耗时**：~10-50k tokens（分块生成）
- **不切分要求**：必须分块（按章节 / 按页）

### L4 — 全文图谱

- **目标**：学术论文深度分析
- **输出文件**：`concepts.md` + `relations.md` + `hierarchy.md` + `evidence.md`
- **新增**：原文证据片段（句子级引用 + 章节定位）
- **适用**：科研论文
- **耗时**：~50-200k tokens
- **不切分要求**：必须分块，且 evidence 不可合并丢失

## 五、amber-agent KB 衔接条款

**核心**：本技能是 amber-agent KB 构建的**上游工具**。

### 5.1 输入衔接

**检测到 amber-agent `mineru_output/<doc>/vlm/` 产物 → 优先复用，不重跑 MinerU。**

vlm/ 标准结构：

```
mineru_output/<doc>/vlm/
├── <basename>.md           # MinerU 解析后的 markdown
├── content_list.json       # MinerU 区块元数据
├── images/                 # 提取的图片
├── *.pdf, layout*.json, ...  # 其他元数据
```

**MinerU 2.5 实际产物子目录是 `hybrid_auto/`**（不是 `vlm/`），已被重命名 `vlm/` 以保持外观。**适配器两种命名都识别**。

### 5.2 输出衔接

analyze 产物的**去向**：
1. amber-agent KB（`knowledge_base/<doc>/`）—— 知识图谱
2. Obsidian Wiki（用户指定路径）—— 复习笔记
3. 临时目录（用户指定）—— 一次性分析

**默认推荐** amber-agent KB 路径，但**不写死**——问用户。

## 六、反模式（不要做）

| ❌ 反模式 | ✅ 正确做法 |
|---|---|
| 把所有 level 全跑一遍再让用户选 | agent 自己选 1 档，让用户审 |
| 硬编码输出到 `~/.paper-reader/` | 问用户 output_prefs |
| 1k+ 页 PDF 不切分就喂 LLM | 强制按章节切分 |
| 没读本文件直接调 LLM | 强制先读 METHODOLOGY |
| 没问用户 output_prefs 就生成文件 | 问 3 件事再动 |
| 把图谱生成路径写死到某个软件 | 只做 MD 嵌入，用户自选 |
| 切分策略写死 (e.g. 永远按页) | 写"何时用 A 何时用 B"的判断 |
| 失败重试无限循环 | L1 重做 1 次 / L2 失败率 20% 触发重做 / L3 自动重试 1 次 |
| 把图谱输出存到 paper-reader 自己的目录 | 让用户选 |
| 假设用户一定用 obsidian | 让用户选 |

## 七、强制流程（agent 必走 8 步）

```
[1] 读本文件 (METHODOLOGY.md)
    ↓
[2] 读对应 granularity/level-X-*.md (X = Q1 决策的档位)
    ↓
[3] 读 chunking-guide.md → 决策切分策略
    ↓
[4] 调 output-questionnaire.md → 问用户 3 件事
    ↓
[5] 调 decision_prompts/decide_*.md → 4 个 LLM 决策 prompt
    ↓
[6] 构造 Decision 对象
    ↓
[7] 调 analyze_with_decision(decision) → 生成文件脚手架
    ↓
[8] agent 自己的 LLM 填文件内容
```

**禁止跳过任何一步**。特别是 [1] 和 [4]。

## 八、失败管理

| 层级 | 失败处理 |
|---|---|
| L1 (subagent 自检) | 失败立即重做 1 次 |
| L2 (parent 抽 10% 检) | 失败率 ≥ 20% 触发整批重做 |
| L3 (合并后完整性) | 自动重试 1 次，仍失败才问用户 |
| 失败产物 | **直接删除**，不保留 |

## 九、版本

- v2.0: 方法论驱动（当前）
- v1.1: 3 档死板枚举（废弃）
- v1.0: 初始版

---

**参考文档**：
- `granularity/level-1-concepts.md` ~ `granularity/level-4-full-graph.md`
- `chunking-guide.md`
- `output-questionnaire.md`
- `decision_prompts/decide-granularity.md` ~ `decision_prompts/decide-output.md`

**相关 skill**：
- amber-agent（KB 消费者）
- obsidian-cli / obsidian-bases（Obsidian 输出目标）
- medbook-wiki-converter（医学生教材场景参考）
