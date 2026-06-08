# Subagent Granularity Patterns — When to Use Each

> **Agent methodology:** Read this to understand the 4 parallelism patterns and when to apply each. This document provides structural templates, not code.

## §1 Pattern Overview

| Pattern | When to Use | Subagent Count | Merge Strategy |
|---|---|---|---|
| **Map-Reduce** | N independent tasks, results mergeable | N (one per task) | Dedupe + Organize |
| **Pipeline** | Stage dependencies, sequential | 2-4 stages | Concat |
| **Tree-of-Thought** | Multi-perspective exploration | 3-5 perspectives | Synthesize |
| **Hierarchical** | Single task too large for one LLM | 10+ workers | Synthesize |

---

## §2 Pattern 1: Map-Reduce

### 2.1 Structure

```
parent (LLM)
  ├─ subagent_1: task_1 → output_1
  ├─ subagent_2: task_2 → output_2
  ├─ ...
  └─ subagent_N: task_N → output_N
parent: collect → merge → final
```

### 2.2 When to Use

- **N ≥ 3 independent documents** that can be analyzed separately
- **Results are mergeable** — same output format
- **No cross-document dependencies** during processing
- **Parallel speedup desired** — 5 docs in ~1/5 the time

### 2.3 When NOT to Use

- Documents have cross-references requiring context
- Results depend on each other mid-process
- Too few tasks to offset coordination overhead

### 2.4 Amber-Agent Example

**Scenario:** 5 independent PDF papers → unified knowledge base

```
Task: Analyze 5 ML papers, extract concepts and relationships
Input: 5 PDF files, 30-50 pages each
Pattern: Map-Reduce (5 subagents, one per paper)
Subagents: 5 independent workers
Merge: Dedupe concepts, organize by theme
Output: Unified KB with all 5 papers' concepts
```

**Configuration:**
```yaml
mode: MAP_REDUCE
num_subagents: 5
framework: hermes_delegate_task
merge_strategy: DEDUPE_ORGANIZE
checkpoint_frequency: 1  # After each paper
```

---

## §3 Pattern 2: Pipeline

### 3.1 Structure

```
stage_1: 抽取 → concepts.json
   ↓
stage_2: 关系 (读 concepts) → relations.json
   ↓
stage_3: 嵌入 (读 relations) → kg.md
```

### 3.2 When to Use

- **Multi-stage processing** where each stage depends on previous
- **Clear phase boundaries** — concept → relation → ontology
- **Sequential dependencies** — can't skip stages

### 3.3 When NOT to Use

- Stages could run in parallel (use Map-Reduce instead)
- Single-pass analysis sufficient
- Stages have circular dependencies

### 3.4 Amber-Agent Example

**Scenario:** L3 full ontology analysis with 3 stages

```
Task: Build complete ontology from document
Input: Single document, any size
Pattern: Pipeline (3 stages)
Stage 1: Extract all concepts → concepts.json
Stage 2: Extract relationships between concepts → relations.json
Stage 3: Embed into ontology structure → kg.md
Output: Full KG with concepts + relations + metadata
```

**Configuration:**
```yaml
mode: PIPELINE
num_subagents: 3
stages:
  - name: concept_extraction
    input: raw_document
    output: concepts.json
  - name: relation_extraction
    input: concepts.json
    output: relations.json
  - name: ontology_embedding
    input: relations.json
    output: kg.md
merge_strategy: CONCAT
```

---

## §4 Pattern 3: Tree-of-Thought

### 4.1 Structure

```
parent
  ├─ subagent_1: perspective_A → result_A
  ├─ subagent_2: perspective_B → result_B
  ├─ subagent_3: perspective_C → result_C
  └─ merge: synthesize → final
```

### 4.2 When to Use

- **Multiple analytical perspectives** on same document
- **Complementary insights** from different angles
- **Quality > speed** — willing to pay extra for breadth

### 4.3 When NOT to Use

- Single perspective sufficient
- Perspectives overlap significantly (redundant work)
- Limited resources / budget

### 4.4 Amber-Agent Example

**Scenario:** amber26 manual analyzed from 3 perspectives

```
Task: Create comprehensive user manual for amber26
Input: amber26 manual (1112 pages)
Pattern: Tree-of-Thought (3 perspectives)
Perspective 1: Theory — What does each feature do, why
Perspective 2: Operation — Step-by-step procedures
Perspective 3: Troubleshooting — What can go wrong, fixes
Merge: Synthesize into coherent manual
Output: Multi-perspective manual with theory + ops + troubleshooting
```

**Configuration:**
```yaml
mode: TREE_OF_THOUGHT
num_subagents: 3
perspectives:
  - theory
  - operation
  - troubleshooting
framework: opencode_run
merge_strategy: SYNTHESIZE
```

---

## §5 Pattern 4: Hierarchical

### 5.1 Structure

```
master
  ├─ sub-master_1
  │    ├─ worker_1a: chunk_1
  │    ├─ worker_1b: chunk_2
  │    └─ worker_1c: chunk_3
  ├─ sub-master_2
  │    ├─ worker_2a: chunk_4
  │    ├─ worker_2b: chunk_5
  │    └─ worker_2c: chunk_6
  └─ sub-master_K
       └─ worker_Kx: chunk_N
master: collect → synthesize → final
```

### 5.2 When to Use

- **Single document > 500 pages** — exceeds single LLM context
- **Document has natural chunks** — chapters, sections
- **Need both parallelism AND quality** — workers process chunks, masters coordinate

### 5.3 When NOT to Use

- Document fits in single LLM context
- No natural chunk boundaries
- Coordination overhead > parallel benefit

### 5.4 Amber-Agent Example

**Scenario:** amber26 manual (1112 pages) → full knowledge graph

```
Task: Build complete KG from amber26 manual
Input: amber26 manual, 1112 pages, ~2-3M tokens
Pattern: Hierarchical (11 sub-masters)
Chunk size: 100 pages per chunk
Sub-masters: 11 (one per 100 pages)
Workers per sub-master: 3-4 (chunk subdivided)
Master: Synthesize all sub-master outputs
Output: Complete KG with all concepts and relationships
```

**Configuration:**
```yaml
mode: HIERARCHICAL
num_sub_masters: 11
workers_per_sub_master: 3-4
chunk_size: 100  # pages
framework: opencode_run
merge_strategy: SYNTHESIZE
checkpoint_frequency: 1  # After each sub-master
```

---

## §6 Pattern Selection Quick Reference

```
DECISION TREE:

Is the task a single document > 500 pages?
  YES → Hierarchical
  NO ↓

Are there 3+ independent documents?
  YES → Map-Reduce
  NO ↓

Does the task have sequential dependencies?
  YES → Pipeline
  NO ↓

Do you need multiple analytical perspectives?
  YES → Tree-of-Thought
  NO ↓

Single-pass analysis sufficient?
  YES → No subagents needed (single LLM)
```

---

## §7 Anti-Patterns to Avoid

| Anti-Pattern | What Happens | Correct Approach |
|---|---|---|
| Over-parallelization | 2 subagents for 2-page doc = slower than single | Use single LLM for small tasks |
| Under-parallelization | 10 docs processed sequentially = 10x time | Use Map-Reduce for independent docs |
| Wrong merge strategy | Use Concat for overlapping content = duplicates | Use Dedupe for Map-Reduce |
| No checkpoint | 30-min task crashes, restart from scratch | Write progress.md after each subagent |
| Ignore dependencies | Pipeline stages run in parallel = broken | Ensure sequential order for Pipeline |

**Remember:** Match pattern to task characteristics, not the other way around.