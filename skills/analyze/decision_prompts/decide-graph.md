# Decision Prompt: Graph / KG Depth

## When
After Q3 用户意图 analysis, before deciding output files.

## Input Variables
- `{level}`: L1-L4
- `{user_intent}`: 用户原话
- `{use_case}`: "obsidian" | "kb" | "transient"
- `{doc_type}`: 文档类型

## Output Schema
```yaml
extract_relations: bool
extract_hierarchy: bool
extract_evidence: bool
relation_types: [string]  # 选自: contains, causes, is_a, part_of, uses, depends_on, precedes
ontology_style: "flat" | "taxonomy" | "deep"
relation_extraction_granularity: "concept" | "sentence"  # concept 即可 / sentence 才要 evidence
reasoning: string
```

## Prompt

You are the paper-reader analyze subagent. Decide graph / KG extraction depth.

**Reference**: METHODOLOGY.md §四 (L1-L4 粒度定义)

**Inputs**:
- level: {level}
- user_intent: {user_intent}
- use_case: {use_case}
- doc_type: {doc_type}

**Output** (YAML only):

```yaml
extract_relations: <bool>
extract_hierarchy: <bool>
extract_evidence: <bool>
relation_types: [...]
  # 可选: contains, causes, is_a, part_of, uses, depends_on, precedes
ontology_style: <flat|taxonomy|deep>
relation_extraction_granularity: <concept|sentence>
reasoning: |
  <为什么，引用 §四 L1-L4 定义>
```

## Validation
- [ ] 至少一个 `extract_*` 为 true
- [ ] `relation_types` 非空（若 extract_relations=true）
- [ ] `level=L1` 必 `extract_relations=false`（L1 只有概念字典）
- [ ] `level=L4` 必 `extract_evidence=true`
- [ ] `extract_evidence=true` → `relation_extraction_granularity=sentence`
- [ ] `use_case=kb` → `extract_hierarchy=true`（KB 需要分类层级）

## Default Relation Types
- 教程 / user guide: `contains`, `uses`
- 教材: `is_a`, `part_of`, `contains`
- 学术论文: `causes`, `depends_on`, `precedes`
- 手册: `contains`, `uses`, `part_of`
- 跨领域: agent 自选 + 解释

## Anti-patterns
- ❌ L1 抽出 relations → 浪费（用户不要）
- ❌ L3 不抽 hierarchy → 不够（KB 没法用）
- ❌ 学术论文抽 concept-level 而非 sentence-level → evidence 没法定位
- ❌ relation_types 给空数组（extract_relations=true 时）
