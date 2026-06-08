# Subagent Result Aggregation — Merge, Dedupe, and Resolve Conflicts

> **Agent methodology:** Read this after subagents complete their work. This document provides the strategy for combining multiple subagent outputs into a unified result.

## §1 Overview

When multiple subagents produce outputs (MD files, KG JSON, annotations), these must be aggregated into a coherent whole. The aggregation strategy affects quality, completeness, and token cost.

**Three aggregation strategies:**
1. **Concat** — Simple concatenation, minimal processing
2. **Dedupe + Organize** — Remove duplicates, group by theme
3. **Synthesize** — LLM-powered synthesis for cross-subagent insights

## §2 When to Use Each Strategy

| Scenario | Recommended Strategy | Rationale |
|---|---|---|
| Subtasks split cleanly with no overlap | Concat | No deduplication needed, fastest |
| Same concepts covered by multiple subagents | Dedupe + Organize | Prevent duplication, maintain uniqueness |
| Cross-subagent insight required | Synthesize | LLM combines for new understanding |
| Map-Reduce pattern | Dedupe + Organize | Default for parallel subagents |
| Hierarchical pattern | Synthesize | Master synthesizes sub-master outputs |
| Pipeline pattern | Concat | Sequential stages output in order |

**Default mappings:**
- Map-Reduce → Dedupe + Organize
- Hierarchical → Synthesize  
- Pipeline → Concat
- Tree-of-Thought → Synthesize

## §3 Deduplication Rules

### 3.1 Concept Deduplication

When multiple subagents define the same concept (wikilink `[[Concept]]`):

**Priority order (highest wins):**
1. Most detailed definition (longest `:: Description` content)
2. If same length, first in alphabetical order
3. Keep all unique relationships/edges even if concept deduplicated

**Process:**
```
1. Extract all concepts across all subagent outputs
2. Group by normalized concept name (case-insensitive)
3. For each group, keep the entry with longest definition
4. Preserve all unique relationship edges from all entries
```

### 3.2 Wikilink Deduplication

If `[[Concept A]]` appears in multiple outputs:
- Keep first occurrence
- Mark subsequent as `#duplicate` in merge log (not in output)

### 3.3 Frontmatter Deduplication

If multiple outputs have frontmatter with same `tags:` or `aliases:`:
- Union all tags (dedupe)
- Union all aliases (dedupe)
- Keep `created:`, `updated:` from the earliest

## §4 Conflict Resolution

### 4.1 Definition Conflicts

**Scenario:** Subagent 1 says "X is a Y", Subagent 2 says "X is a Z"

**Resolution rules:**
1. If both have evidence citations → keep both, mark as **conflicting_definition**
2. If only one has evidence → keep that one
3. If neither has evidence → keep longer description, mark as **unverified_conflict**

### 4.2 Relationship Conflicts

**Scenario:** Subagent 1 says "A → B (type: causes)", Subagent 2 says "A → B (type: prevents)"

**Resolution rules:**
1. Keep both edges with different relationship types
2. Mark with `conflict_resolved: false` for human review
3. In KG output, add `confidence: 0.5` to conflicting edges

### 4.3 Metadata Conflicts

**Scenario:** Different `level:` assignments, different `granularity:` tags

**Resolution rules:**
- Keep highest granularity level specified
- Union all `tags:`

## §5 Alignment Procedures

### 5.1 Wikilink Normalization

Before merging, normalize all wikilinks:
```
1. Trim whitespace: [[ Concept ]] → [[Concept]]
2. Case normalize: [[CONCEPT]] → [[concept]]
3. Anchor removal: [[Concept#Section]] → [[Concept]]
4. Alias resolution: If [[alias]] maps to [[canonical]], replace
```

### 5.2 Reference Consistency

Ensure cross-references point to correct destinations:
- Check each wikilink targets an existing concept
- If target missing, either create stub or remove with warning
- Log all broken references in `aggregation_warnings.md`

### 5.3 Temporal Ordering

If subagent outputs have ordering implications:
- Use frontmatter `created:` timestamps to order
- If timestamps unavailable, use subagent launch order
- Preserve order in final output where semantically important

## §6 Synthesize Pattern (LLM-Powered)

### 6.1 When to Synthesize

Use Synthesize when:
- Cross-subagent concepts need integration
- Subagent outputs have complementary insights
- Quality > speed (willing to pay extra LLM tokens)

### 6.2 Synthesis Prompt Template

```markdown
# Synthesize Subagent Outputs

You are merging outputs from N subagents that analyzed the same document(s) from different angles.

## Subagent Outputs
<insert outputs here>

## Task
1. Identify concepts that appear in multiple outputs - merge definitions
2. Identify relationships that span subagents - consolidate
3. Identify conflicts - flag for human review
4. Produce a unified output with:
   - All unique concepts (deduplicated)
   - All unique relationships (no duplicates)
   - Clear provenance annotations

## Output Format
- Start with synthesis summary
- Include conflict note if any unresolved
- Mark derived relationships clearly
```

### 6.3 Synthesis Quality Checks

After synthesis, run:
- [ ] All original concepts present (no loss)
- [ ] All relationships preserved (check edge count)
- [ ] No introduced contradictions
- [ ] Wikilinks still valid

## §7 Aggregation Output Artifacts

### 7.1 Required Outputs

After aggregation completes, produce:
1. **Merged MD/JSON** — The unified output
2. **dedupe_log.md** — What was deduplicated, why
3. **conflict_report.md** — Unresolved conflicts (if any)
4. **aggregation_summary.md** — Statistics (N concepts, M edges, K conflicts)

### 7.2 Logging Requirements

Log format for deduplication:
```markdown
## Deduplication Log

### Concepts Deduped
| Original | Kept | Reason |
|---|---|---|
| [[RNA]] (subagent 1) | [[RNA]] (subagent 3) | Longer definition (423 vs 156 chars) |

### Relationships Merged
| Edge | Sources | Action |
|---|---|---|
| A→B (causes) | sub1, sub3 | Kept both (different types) |
```

## §8 Quick Reference Table

| Input Type | Merge Strategy | Output |
|---|---|---|
| 3 independent PDF analyses | Concat | Combined MD |
| 11 chunks of same document | Dedupe + Organize | Unified MD + KG |
| Multi-perspective analysis | Synthesize | LLM-merged MD |
| Pipeline stages | Concat | Sequential MD |

**Remember:** Default to Dedupe + Organize for Map-Reduce, Synthesize for Hierarchical.