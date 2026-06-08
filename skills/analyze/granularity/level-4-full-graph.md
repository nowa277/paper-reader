# Level 4: 全文图谱

## 何时用
参考 METHODOLOGY.md §三 Q1。

**典型场景**:
- 学术论文 (10-30 页)
- 用户问"深度分析"/"逐句"
- 综述类材料
- 需 evidence 追溯

**Token 预算**: ~50-200k tokens (分块生成)

**必须分块**: L4 永远不能一次过。

## 核心提取内容
L3 全部 + 原文证据 (句子级)。

**新增**:
- evidence: 句子级原文引用 + 章节定位

## 输出文件
- `concepts.md` (同 L1)
- `relations.md` (同 L2)
- `hierarchy.md` (同 L3)
- `evidence.md` (新增)

### `evidence.md` 格式

```markdown
# <doc_name> 证据索引 (L4)

> 自动生成 by paper-reader analyze v2.0 | 档位: L4 | 日期: <date>

## 格式约定

每条 evidence:
- `concept`: 涉及的概念
- `relation` (可选): 涉及的关系，格式 `[源] 关系 [目标]`
- `quote`: 原文句子 (≤ 200 chars)
- `location`: 章节/页码定位
- `context` (可选): 上下文 1-2 句

## 证据列表

### 概念: AMBER
- quote: "AMBER is a suite of biomolecular simulation programs."
- location: §1.1, page 1
- context: null

### 概念: pmemd
- quote: "PMEMD (Particle Mesh Ewald Molecular Dynamics) is a highly optimized MD engine."
- location: §1.2, page 2

### 关系: [sander] uses [prmtop]
- quote: "sander reads parameter and coordinate files in prmtop and inpcrd format."
- location: §1.5, page 5
- concept: sander
- relation_target: prmtop

### 关系: [high_temperature] causes [simulation_instability]
- quote: "Temperatures above 500 K frequently lead to simulation instability due to bond breaking."
- location: §5.4, page 87
- context: "Users should monitor temperature carefully. ..."
- concept: high_temperature
- relation_target: simulation_instability

## 证据统计
- 概念 evidence: 28
- 关系 evidence: 12
- 总 evidence: 40
- 引用概念覆盖率: 95% (38/40)

## 元信息
- 文档: <doc_name>
- 关系类型: <从 decide-graph 决策>
- 提取时间: <iso timestamp>
```

## 决策要点

### 引用粒度
- 句子级 (default): 整句引用, ≤ 200 chars
- 段落级 (fallback): 长句拆不开时用整段
- ❌ 章节级 (too coarse)

### 引用准确性
- 原文必须 verbatim (可 OCR 容错 1-2 字)
- 章节/页码定位必须准确
- 上下文 1-2 句（不超过 2 句，避免 context pollution）

### 分块策略
- 按章节切分（最常见）
- 每块生成 evidence 子列表
- 最后 agent 合并 + 排序（按章节顺序）

### relation_extraction_granularity
- L4 必 `sentence`（evidence 必须 sentence-level）

## 反模式
- ❌ evidence 漏掉关键概念 → 覆盖率 < 80%
- ❌ quote 长度 > 300 chars → 引用过粗
- ❌ quote 改写 (paraphrase) → 不是 evidence
- ❌ location 模糊 ("文中" / "大概") → 不可定位
- ❌ 一次性生成不分块 → 必失败
- ❌ 概念有 evidence 但关系没 evidence → 关系不可信
- ❌ 引用 concept 不在 concepts.md 里 → 悬空

## 自检
- [ ] L3 全部自检通过
- [ ] evidence.md 引用概念覆盖率 ≥ 80%
- [ ] 引用概念覆盖率 ≥ 关系覆盖率
- [ ] quote 平均长度 ≤ 200 chars
- [ ] 所有 location 都有具体章节/页码
- [ ] 分块生成的 evidence 可按章节排序合并
- [ ] 引用的 concept 都在 concepts.md 里
