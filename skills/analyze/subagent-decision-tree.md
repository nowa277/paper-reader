# Subagent Decision Tree — When and How to Split

> **Agent methodology:** Read this before deciding to spawn subagents. This document provides the decision framework, NOT implementation code.

## §1. Decision Framework Overview

Before spawning any subagent, the agent MUST answer these 4 questions:

1. **Is parallel necessary?** — Can a single LLM handle the task?
2. **How many subagents?** — Based on document size, complexity, independence
3. **What's the dependency pattern?** — Independent / Sequential / Tree / Map-Reduce
4. **Which framework?** — Hermes delegate_task / OpenCode run / Claude Code Task

## §2. Split Decision (Q1 → Q2)

### Decision Matrix

| Condition | Split? | Subagent Count | Pattern |
|-----------|--------|----------------|---------|
| 文档 ≤ 2 AND 总页数 < 100 | ❌ No | 0 (single LLM) | — |
| 文档 ≥ 3 AND 互相独立 | ✅ Yes | N (one per doc) | Map-Reduce |
| 文档 ≥ 1 AND 有阶段依赖 | ✅ Yes | N (one per stage) | Pipeline |
| 单文档需要多视角分析 | ✅ Yes | 2-4 | Tree-of-Thought |
| 单文档 > 500 页 | ✅ Yes | ≥ 4 (by chapter) | Hierarchical |
| 跨文档需要概念关联 | ✅ Yes | N + 1 (synthesize) | Map-Reduce + Synthesize |

### Detailed Rules

**Rule 1: Don't split for small tasks**
- If total pages < 100 and documents ≤ 2 → **single LLM**
- Reasoning: Subagent overhead exceeds benefit

**Rule 2: Split by document for independent tasks**
- 3+ documents that don't reference each other → **Map-Reduce**
- Each subagent processes one document independently
- Parent merges results

**Rule 3: Split by stage for dependent tasks**
- Task has clear stages: A → B → C → D
- Each stage's output feeds the next → **Pipeline**
- Example: concept extraction → relation extraction → hierarchy building

**Rule 4: Split by perspective for complex analysis**
- Same document needs multiple viewpoints → **Tree-of-Thought**
- Example: 3 perspectives on amber26 (beginner / intermediate / expert)

**Rule 5: Split by chapter for large documents**
- Single document > 500 pages → **Hierarchical**
- First layer: sub-master per major section (e.g., 11 chapters)
- Second layer: subagents per chapter if needed

**Rule 6: Cross-document synthesis**
- Need to correlate concepts across documents → **Map-Reduce + Synthesize**
- Phase 1: Map-Reduce (each doc → local KG)
- Phase 2: Synthesize subagent (merge → global KG)

## §3. Dependency Patterns (Q3)

### Pattern 1: Map-Reduce

```
[Input: N docs] → [Subagent 1] → [Subagent 2] → ... → [Subagent N]
                     ↓              ↓                    ↓
                  [Result 1]    [Result 2]          [Result N]
                                        ↓
                              [Merge: combine all]
```

**When to use:** Documents are independent, results need aggregation
- 5 PDF papers → 5 concept extracts → merged bibliography
- N customer reviews → N sentiment analyses → overall sentiment

### Pattern 2: Pipeline

```
[Input] → [Stage A: Subagent] → [Stage B: Subagent] → [Stage C: Subagent] → [Output]
                ↓                      ↓                       ↓
           [Intermediate 1]      [Intermediate 2]       [Final]
```

**When to use:** Each stage's output feeds the next
- Concept → Relation → Hierarchy → Evidence (4 stages)
- Parse → Clean → Transform → Load

### Pattern 3: Tree-of-Thought

```
                        [Input: 1 doc]
                    /        |        \
           [Persp A]    [Persp B]    [Persp C]
               ↓            ↓            ↓
          [View A]      [View B]      [View C]
               \            |            /
                    [Synthesize]
                         ↓
                   [Unified View]
```

**When to use:** Need multiple perspectives on the same content
- Technical doc from beginner/intermediate/expert lens
- Same paper: methodology focus / results focus / limitations focus

### Pattern 4: Hierarchical

```
                    [Master Coordinator]
                   /    |    |    \    \
            [Chunk1] [Chunk2] ... [ChunkN]
                 ↓        ↓           ↓
           [Local 1]  [Local 2]   [Local N]
                 \       |        /
                    [Merge]
                     ↓
               [Final Output]
```

**When to use:** Very large document (> 500 pages)
- 1000+ page manual → split by chapter
- Each chunk processed independently
- Master coordinates and merges

## §4. Framework Selection (Q4)

### Framework Decision Table

```yaml
framework_decision:
  if concurrent <= 3 and framework == hermes:
    use: delegate_task
    note: "Hermes has rate limits, use sparingly"
  
  elif concurrent 4-10 and have_opencode:
    use: opencode_run
    note: "OpenCode handles 4-10 subagents well"
  
  elif concurrent 4-10 and have_cc:
    use: claude_code_task
    note: "Claude Code Task for parallel execution"
  
  elif concurrent > 10:
    warn_user: "需要分批或升级资源"
    fallback: queue + sequential
    note: "Exceeding 10 parallel subagents often causes resource contention"
```

### Framework Constraints (User Preference)

> **Recorded in memory:** `delegate_task` 慎用（限额）, CC/OpenCode 随便用

- **Hermes delegate_task**: Rate limited, use only when concurrent ≤ 3
- **OpenCode run**: No known limit, good for 4-10
- **Claude Code Task**: No known limit, good for 4-10
- **Sequential fallback**: If > 10, process in batches of 8

## §5. Decision Flow Diagram

```
Start: Is the task too big for single LLM?
  │
  ├─ NO (< 100 pages, ≤ 2 docs) → Use single LLM, END
  │
  └─ YES → Q2: How many independent pieces?
            │
            ├─ 1 piece, > 500 pages → Hierarchical
            │
            ├─ 1 piece, multiple perspectives → Tree-of-Thought
            │
            ├─ Multiple independent pieces → Q3: Any dependencies?
            │   │
            │   ├─ NO → Map-Reduce
            │   │
            │   └─ YES → Pipeline (if sequential) OR Map-Reduce + Synthesize (if cross-ref)
            │
            └─ Need synthesis → Map-Reduce + Synthesize
```

## §6. Anti-Patterns (Don't Do This)

| ❌ Wrong | ✅ Correct |
|----------|------------|
| Spawn subagent for 5-page PDF | Use single LLM |
| Use delegate_task for 20 subagents | Use OpenCode run with batch |
| Run all subagents in parallel without limit | Cap at 10, use queue for more |
| Skip merge step in Map-Reduce | Always merge results |
| Don't delete failed subagent artifacts | Delete immediately (see failure management) |
| Hard-code subagent count | Calculate based on document size/chapters |

## §7. Integration with Existing Modules

- **Module 1/2/3** (fetch/analyze/output): Run *inside* each subagent
- **Module 4** (this document): Orchestrates *between* subagents

```
[User Input: N docs / M pages]
       ↓
[Module 4: Decision Tree] → Choose pattern & framework
       ↓
[N subagents, each running Module 1 → 2 → 3]
       ↓
[Module 4: Merge] → Final output
```

---

## §8. Quick Reference Card

| Scenario | Pattern | Framework | Subagents |
|----------|---------|-----------|-----------|
| 5 PDF → L1/L2 overview | Map-Reduce | Hermes delegate_task | 5 |
| 1112-page manual → L3 | Hierarchical | OpenCode run | 11 sub-master |
| 1112-page manual → L4 | Tree-of-Thought + Hierarchical | OpenCode run | 33 (3 × 11) |
| Single PDF < 100p → L1/L2 | No parallel | Single LLM | 0 |
| Concept → Relation → Hierarchy | Pipeline | Single LLM | 3 stages |

**Decision mnemonic:**
- Small → single
- Independent docs → Map-Reduce
- Dependent stages → Pipeline
- One doc, many views → Tree-of-Thought
- Big doc → Hierarchical
- Cross-doc synthesis → Map-Reduce + Synthesize