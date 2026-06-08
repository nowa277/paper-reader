# Chunking Guide

## 为什么需要切分
LLM context window 有限。amber 1112 页 PDF 一次性喂 LLM 必失败（超 token）。切分让每块独立可处理。

## 4 种切分策略

### 1. `none` — 不切分
- **适用**: < 50 页 + 章节清晰
- **例子**: 27 页 AlphaFold user guide
- **风险**: 输出可能不完整（agent 只读 1/2 文档就停了）

### 2. `by_chapter` — 按章节切分
- **适用**: 50-200 页 / 200+ 页 + 章节清晰
- **例子**: amber 1112 页按 §1-§30 切 30 块
- **风险**: 章节长度不均（一章 5 页 vs 一章 100 页）

### 3. `by_page` — 按页切分
- **适用**: 200+ 页 + 无结构 / 全是表 / 公式密
- **例子**: API reference 1000 页按 20 页/块
- **风险**: 跨页概念断裂（处理用 overlap 缓解）

### 4. `by_chapter_with_overlap` — 章节切分 + 块间重叠
- **适用**: 1000+ 页 + 章节清晰 + 概念跨章
- **例子**: amber 手册切分后每块前后加 2 页重叠
- **风险**: 总 token 涨 20%

## 决策要点（来自 decide-chunking.md）

```yaml
strategy: by_chapter | by_page | by_chapter_with_overlap | none
chunk_size: <int pages>  # 仅 by_page
overlap: <int pages>     # 仅 by_page
```

## 检测章节结构

### 章节识别规则
1. Markdown heading 级别: `#`/`##`/`###` → 章节
2. PDF outline (bookmark): MinerU 解析的 `content_list.json` 里有 `[type: heading]`
3. 页眉/页脚模式: "Chapter X" / "第 X 章"
4. 章节开头大字号: 视觉检测（agent 看 PDF layout）

### 章节缺失 fallback
- 没有任何章节标识 → `by_page`
- 章节数量 < 3 → `by_page`（章节太少不切）

## 滑动窗口参数

### chunk_size 默认
- 密度 low: 20 页/块
- 密度 medium: 10 页/块
- 密度 high: 5 页/块

### overlap 默认
- `chunk_size × 0.2`（20% 重叠）
- min 1 页
- max 5 页

### 调优指南
- chunk_size 太大 (>50) → 单次 LLM 输出可能超 token
- overlap=0 → 跨块概念断裂
- overlap 太大 (>50%) → 浪费 token

## 边界处理

### 表格
- 整表保留在一块内（不跨块切分）
- agent 检测 `|---|` 或 `<table>` 标记
- 强制边界: 表格在 chunk 边界前则整表移入下一块

### 图片
- 图片说明文字绑同一块
- 大图（> 1 页）单独成块
- 跨页图（image 标注 + 跨页续）: 标 `[跨页图: 需人工合并]`

### 公式
- 公式不跨块切分
- 公式密集块用 `by_chapter` 或缩小 chunk_size

### 引用 / 参考文献
- 参考文献区单独成块（不混入正文）
- 引用密集文档 → 提取到 `references.md` 单独处理

## 验证

### L1 (subagent 自检)
- 每块 token 数 < 80% 模型 context
- 章节首尾完整（不在章节中间切）
- 关键概念至少出现 1 次（不漏提取）

### L2 (parent 抽 10% 检)
- 抽样块与原文对比：覆盖率 ≥ 95%
- 块间无重复内容（overlap 合理）

### L3 (合并后完整性)
- 整文档去重后字数 vs 原文 ≥ 95%
- 关键概念在所有相关块都被提及

## 反模式
- ❌ 1000+ 页不切分 → 必失败
- ❌ 章节清晰但选 by_page → 浪费（按章节更准）
- ❌ chunk_size 太大 (>50) → 失败
- ❌ overlap=0 → 跨块断裂
- ❌ 公式 / 表格跨块切分 → 内容失真
- ❌ 一次性生成所有块 → 失败（必须串行或并行 subagent）

## 与 subagent 并行的关系
切分是 subagent 并行的前提：
- 单块 ≤ 50 页 → 可 1 subagent 1 块
- 单块 > 50 页 → 拆 subagent 内部再切
- 并行度 ≤ 3（来自 subagent 限制）
- 块数 > 10 → 警告用户

详见 spec §14 subagent 并行与管理。
