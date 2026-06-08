# Decision Prompt: Granularity (L1-L4)

## When
After Q1 文档类型 analysis, before reading `granularity/level-X-*.md`.

## Input Variables
- `{doc_type}`: 文档类型字符串 (e.g. "user guide", "academic paper", "manual", "cheat sheet")
- `{page_count}`: 整数
- `{has_chapters}`: 布尔
- `{user_intent}`: 用户原话或关键词

## Output Schema
```yaml
level: "L1" | "L2" | "L3" | "L4"
reasoning: string  # ≥ 50 chars, 引用 Q1 决策表依据
alternative: string  # 备选档 + 具体的升级/降级条件
```

## Prompt

You are the paper-reader analyze subagent. Decide the granularity level for this document.

**Reference**: METHODOLOGY.md §三 Q1 (决策表)

**Inputs**:
- doc_type: {doc_type}
- page_count: {page_count}
- has_chapters: {has_chapters}
- user_intent: {user_intent}

**Output** (YAML only, no extra text):

```yaml
level: <L1|L2|L3|L4>
reasoning: |
  <2-3 句话解释为什么选这一档，引用 Q1 决策表的具体行>
alternative: |
  <备选档 + 何时升级/降级到备选，给出具体条件（不能是"看情况"）>
```

## Validation
- [ ] `level` 必须是 4 个之一
- [ ] `reasoning` 引用 Q1 决策表依据 ≥ 2 条
- [ ] `alternative` 必须给出具体条件（不能是"看情况"）
- [ ] `reasoning` 长度 ≥ 50 字符

## Anti-patterns
- ❌ 默认 L2 但 user_intent 明确说"深度" → 选 L2 就错了
- ❌ 选 L3 但 doc_type 是 cheat sheet → 过度
- ❌ 选 L4 但 user_intent 是"概览" → 过度
