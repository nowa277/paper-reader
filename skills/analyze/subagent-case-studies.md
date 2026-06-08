# Subagent Case Studies — Real-World Scenarios

> **Agent methodology:** Read these case studies to understand how to apply the 4 patterns in actual amber-agent workflows.

---

## Case Study 1: 5 Independent PDF Papers (Map-Reduce)

### Context
- **Input:** 5 ML papers, 30-50 pages each
- **Goal:** Extract concepts and build unified knowledge base
- **Constraint:** User wants results in 1 hour, not 5 hours

### Decision Process

1. **Analyze input:**
   - 5 independent documents (no cross-references)
   - Total: ~200 pages
   - Each can be analyzed separately

2. **Apply decision tree:**
   - Not a single large doc (>500 pages) → NOT Hierarchical
   - 5 independent docs → YES Map-Reduce

3. **Configuration:**
```yaml
mode: MAP_REDUCE
num_subagents: 5
framework: hermes_delegate_task
merge_strategy: DEDUPE_ORGANIZE
```

### Execution

```
Time 0:00   Launch 5 subagents in parallel
Time 0:10   Subagent 1 done, write checkpoint
Time 0:10   Subagent 2 done, write checkpoint
Time 0:12   Subagent 3 done, write checkpoint
Time 0:11   Subagent 4 done, write checkpoint
Time 0:13   Subagent 5 done, write checkpoint
Time 0:14   Parent merges: dedupe concepts, organize by theme
Time 0:15   Final output ready
```

### Result
- **Time:** ~15 minutes (vs 75 minutes sequential)
- **Quality:** All 5 papers integrated, no duplicates
- **Key learning:** Map-Reduce perfect for independent documents

---

## Case Study 2: L3 Full Ontology Pipeline

### Context
- **Input:** Single document, 200 pages
- **Goal:** Build complete knowledge graph with ontology
- **Constraint:** Must extract concepts → relations → structure

### Decision Process

1. **Analyze input:**
   - Single document (not multiple)
   - Has clear stages: extract → relate → structure
   - Sequential dependencies

2. **Apply decision tree:**
   - Not >500 pages → NOT Hierarchical
   - Not independent docs → NOT Map-Reduce
   - Has stage dependencies → YES Pipeline

3. **Configuration:**
```yaml
mode: PIPELINE
num_subagents: 3
stages:
  - concept_extraction
  - relation_extraction  
  - ontology_embedding
framework: single_llm_sequential
merge_strategy: CONCAT
```

### Execution

```
Stage 1: Extract concepts
  Input: document.md
  Output: concepts.json (150 concepts)

Stage 2: Extract relations
  Input: concepts.json
  Output: relations.json (80 relationships)

Stage 3: Embed in ontology
  Input: relations.json
  Output: kg.md (full KG)
```

### Result
- **Time:** ~20 minutes (3 sequential stages)
- **Quality:** Full ontology with all relationships
- **Key learning:** Pipeline for sequential dependencies

---

## Case Study 3: amber26 Manual Multi-Perspective (Tree-of-Thought)

### Context
- **Input:** amber26 user manual, 1112 pages
- **Goal:** Create comprehensive manual with theory + operation + troubleshooting
- **Constraint:** User needs complete picture, not just features

### Decision Process

1. **Analyze input:**
   - Single massive document (1112 pages = 2-3M tokens)
   - Need multiple analytical perspectives
   - Quality more important than speed

2. **Apply decision tree:**
   - Single doc >500 pages → Could use Hierarchical
   - BUT: need different perspectives, not chunking
   - → YES Tree-of-Thought

3. **Configuration:**
```yaml
mode: TREE_OF_THOUGHT
num_subagents: 3
perspectives:
  - theory: What does each feature do?
  - operation: How do you use each feature?
  - troubleshooting: What can go wrong?
framework: opencode_run
merge_strategy: SYNTHESIZE
```

### Execution

```
Perspective 1 (Theory):
  Analyze all 1112 pages for feature descriptions
  Output: theory.md (500 lines)

Perspective 2 (Operation):
  Analyze all 1112 pages for procedures
  Output: operation.md (600 lines)

Perspective 3 (Troubleshooting):
  Analyze all 1112 pages for failure modes
  Output: troubleshooting.md (300 lines)

Synthesize:
  Merge into single manual with 3 sections
```

### Result
- **Time:** ~45 minutes (3 parallel perspectives + synthesis)
- **Quality:** Comprehensive manual covering all angles
- **Key learning:** Tree-of-Thought for multi-perspective analysis

---

## Case Study 4: Super-Large Document (Hierarchical)

### Context
- **Input:** Very large technical specification, 2000+ pages
- **Goal:** Extract all concepts, relationships, build KG
- **Constraint:** No single LLM can handle this in one pass

### Decision Process

1. **Analyze input:**
   - Single document, 2000+ pages
   - Exceeds any single LLM context window
   - Has natural chapters (20 chapters, 100 pages each)

2. **Apply decision tree:**
   - Single doc >500 pages → YES Hierarchical
   - Natural chunk boundaries = chapters

3. **Configuration:**
```yaml
mode: HIERARCHICAL
num_sub_masters: 20
workers_per_sub_master: 4
chunk_size: 50  # pages per worker
framework: opencode_run
merge_strategy: SYNTHESIZE
checkpoint_frequency: 1
```

### Execution

```
Master coordinates:
  ├─ Sub-master 1 (chapters 1-4)
  │    ├─ Worker 1a: ch 1-2 (50 pages)
  │    ├─ Worker 1b: ch 2-3 (50 pages)
  │    ├─ Worker 1c: ch 3-4 (50 pages)
  │    └─ Worker 1d: ch 4-5 (50 pages)
  │
  ├─ Sub-master 2 (chapters 5-8)
  │    └─ ...
  │
  └─ Sub-master 20 (chapters 77-80)

Each sub-master synthesizes its workers
Master synthesizes all sub-masters
```

### Result
- **Time:** ~2 hours (parallel across 20 sub-masters)
- **Quality:** Complete KG of entire specification
- **Key learning:** Hierarchical for super-large documents

---

## Case Study 5: Small Task (No Subagents)

### Context
- **Input:** Single short paper, 20 pages
- **Goal:** Quick summary extraction
- **Constraint:** Fast turnaround needed

### Decision Process

1. **Analyze input:**
   - Single document, <100 pages
   - 1 document, not multiple
   - Simple task, no complex dependencies

2. **Apply decision tree:**
   - Total pages <100 AND docs ≤2 → NO subagents

3. **Configuration:**
```yaml
mode: NONE
num_subagents: 1
framework: single_llm
```

### Result
- **Time:** ~2 minutes
- **Quality:** Direct output, no coordination overhead
- **Key learning:** Don't over-engineer small tasks

---

## Summary: Pattern Selection by Scenario

| Scenario | Pattern | Why |
|---|---|---|
| 5 independent papers | Map-Reduce | Independent processing, mergeable results |
| Single doc with stages | Pipeline | Sequential dependencies |
| One doc, multiple angles | Tree-of-Thought | Complementary perspectives |
| Very large single doc | Hierarchical | Exceeds LLM context |
| Small/simple task | None | No overhead needed |

**Remember:** Match pattern to task, not vice versa.