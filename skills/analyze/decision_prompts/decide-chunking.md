# Decision Prompt: Chunking Strategy

## When
After Q2 规模+结构 analysis, before invoking `analyze_with_decision()`.

## Input Variables
- `{page_count}`: 整数
- `{has_chapters}`: 布尔
- `{chapter_count}`: 整数 (若 has_chapters=true)
- `{density}`: "low" | "medium" | "high" (公式/表密度估算)
- `{level}`: 来自 decide-granularity 的 L1-L4

## Output Schema
```yaml
strategy: "none" | "by_chapter" | "by_page" | "by_chapter_with_overlap"
chunk_size: int | null  # 仅 by_page 必填 (页数)
overlap: int | null  # 仅 by_page 必填 (页数)
reasoning: string  # 引用 Q2 决策表依据
```

## Prompt

You are the paper-reader analyze subagent. Decide the chunking strategy.

**Reference**: METHODOLOGY.md §三 Q2 (决策表) + `chunking-guide.md`

**Inputs**:
- page_count: {page_count}
- has_chapters: {has_chapters}
- chapter_count: {chapter_count}
- density: {density}
- level: {level}

**Output** (YAML only):

```yaml
strategy: <none|by_chapter|by_page|by_chapter_with_overlap>
chunk_size: <int or null>  # 仅 by_page 必填
overlap: <int or null>     # 仅 by_page 必填
reasoning: |
  <为什么选这个策略，引用 Q2 决策表的具体行>
```

## Validation
- [ ] `strategy` 在 4 个之一
- [ ] `strategy=by_page` 时 `chunk_size` 和 `overlap` 必填
- [ ] `strategy=none` 时 `chunk_size=null` 且 `overlap=null`
- [ ] `level=L3|L4` 时 `strategy` 不能是 `none`（必须分块）
- [ ] `page_count >= 1000` 时 `strategy` 不能是 `none`
- [ ] `reasoning` 引用 Q2 决策表

## Default Sizing (when by_page)
- chunk_size: 20 页（密度 low）/ 10 页（medium）/ 5 页（high）
- overlap: chunk_size × 0.2 (20%)

## Anti-patterns
- ❌ 1000+ 页选 `none` → 必失败（超 LLM context）
- ❌ 章节清晰但选 `by_page` → 浪费（按章节更准）
- ❌ chunk_size 太大 (>50) → 单次 LLM 输出可能超 token
- ❌ overlap=0 → 跨页概念断裂
