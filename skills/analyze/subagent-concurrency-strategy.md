# Subagent Concurrency Strategy — Workload-Based Configuration

> **Agent methodology:** Read this to configure subagent execution based on workload type. Different workloads (IO-bound, Compute-bound, Mixed) require different concurrency settings.

## §1. Workload Classification

Every subagent task falls into one of three categories:

| Type | Characteristics | Examples |
|------|-----------------|----------|
| **IO-bound** | Waiting for external I/O: network, disk, API calls | Fetch PDF from URL, call LLM API, read file from disk |
| **Compute-bound** | CPU-intensive processing: parsing, computation, analysis | Parse PDF structure, extract entities, run algorithms |
| **Mixed** | Alternates between IO and compute | LLM analysis (API call → compute → API call → compute) |

### How to Classify Your Task

**IO-bound signs:**
- Most time spent waiting (network latency, disk I/O)
- Little CPU usage during wait
- Example: Fetching 10 PDFs from URLs concurrently

**Compute-bound signs:**
- CPU stays busy (> 80% utilization)
- No external API calls
- Example: Running NER on 1000 paragraphs

**Mixed signs:**
- Alternates between waiting and computing
- Example: LLM inference (send prompt → wait → receive → process → send next)

## §2. Concurrency Configuration by Workload

### 2.1 IO-Bound Configuration

**Use case:** Network requests, file I/O, API calls

| Setting | Value | Rationale |
|---------|-------|-----------|
| Max concurrent | 10-20 | IO等待时不耗CPU,可高并发 |
| Batch size | 20 | Group requests to reduce overhead |
| Timeout per task | 60s | Network calls need generous timeout |
| Retry strategy | Exponential backoff | Handle transient network failures |

**Example: Fetch 50 PDFs from URLs**

```yaml
config:
  type: io_bound
  max_concurrent: 15
  batch_size: 20
  timeout_per_task: 60
  retry:
    max_attempts: 3
    backoff_multiplier: 2
    initial_delay: 1s
```

### 2.2 Compute-Bound Configuration

**Use case:** CPU-intensive tasks: parsing, NER, algorithm execution

| Setting | Value | Rationale |
|---------|-------|-----------|
| Max concurrent | CPU cores - 2 | Leave headroom for system |
| Batch size | CPU cores | Match parallelism to cores |
| Timeout per task | 300s | Compute tasks take longer |
| Retry strategy | Simple retry | Failures usually not transient |

**Example: Extract entities from 100 documents**

```yaml
config:
  type: compute_bound
  max_concurrent: 6  # Assuming 8 CPU cores
  batch_size: 6
  timeout_per_task: 300
  retry:
    max_attempts: 2
    backoff_multiplier: 1
```

### 2.3 Mixed Configuration

**Use case:** LLM analysis (IO for API calls, compute for processing)

| Setting | Value | Rationale |
|---------|-------|-----------|
| Max concurrent | 5-8 | LLM API has rate limits |
| Batch size | 8 | Balance throughput vs. rate limits |
| Timeout per task | 120s | LLM calls vary in latency |
| Retry strategy | Aggressive retry | Transient API errors common |

**Example: Analyze 20 papers with LLM**

```yaml
config:
  type: mixed
  max_concurrent: 5
  batch_size: 8
  timeout_per_task: 120
  retry:
    max_attempts: 5
    backoff_multiplier: 1.5
    initial_delay: 2s
```

## §3. Concurrency Patterns

### Pattern A: Parallel Fire (all at once)

```
[T1] ─┐
[T2] ─┼─→ All complete → Merge
[T3] ─┘
```

**Best for:** Independent tasks, IO-bound
**Pros:** Maximum parallelism
**Cons:** Resource spike, no early failure detection

### Pattern B: Pipeline (stage by stage)

```
[Stage A] → [Stage B] → [Stage C]
     ↓           ↓           ↓
  [Done A]  [Done B]   [Done C]
```

**Best for:** Dependent tasks, each stage feeds next
**Pros:** Memory efficient, early failure stops pipeline
**Cons:** Slower than parallel if stages are imbalanced

### Pattern C: Chunked Parallel (batched)

```
Batch 1: [T1][T2][T3][T4] → [Merge 1]
Batch 2: [T5][T6][T7][T8] → [Merge 2]
Batch 3: [T9][T10]        → [Merge 3]
         ↓
    [Final Merge]
```

**Best for:** Large number of tasks (> 20), resource-constrained
**Pros:** Predictable resource usage, graceful degradation
**Cons:** Slower overall, complex merge logic

### Pattern D: Priority Queue

```
High Priority: [T1][T2] → [Process First]
Low Priority:  [T3][T4][T5] → [Process After]
```

**Best for:** Mixed priority workloads
**Pros:** Critical tasks complete first
**Cons:** Starvation possible for low priority

## §4. Resource Management

### 4.1 CPU Management

```python
import os

def get_safe_concurrency(compute_bound: bool) -> int:
    """Calculate safe max concurrent tasks."""
    cpu_count = os.cpu_count() or 4
    
    if compute_bound:
        # Leave 2 cores for system
        return max(1, cpu_count - 2)
    else:
        # IO-bound can go higher
        return min(20, cpu_count * 2)
```

### 4.2 Memory Management

| Workload | Memory per Task | Max Tasks (16GB RAM) |
|----------|-----------------|---------------------|
| IO-bound | ~50MB | 300 |
| Compute-bound | ~500MB | 30 |
| Mixed (LLM) | ~1GB | 12 |

**Rule of thumb:** Keep total memory < 80% of available RAM

### 4.3 Rate Limit Handling

| Service | Limit | Strategy |
|---------|-------|----------|
| OpenAI API | 5000 TPM / 500 RPM | Queue + 200ms delay |
| Anthropic | 1000 TPM | Queue + 1s delay |
| Hermes delegate_task | Unknown (use sparingly) | Cap at 3 |
| File system | Depends on FS | Sequential if NFS |

## §5. Configuration Decision Flow

```
What type of task?
  │
  ├─ IO-bound (network, file I/O)
  │   └─ Use Config A: max_concurrent=10-20, timeout=60s
  │
  ├─ Compute-bound (CPU parsing, algorithms)
  │   └─ Use Config B: max_concurrent=CPU-2, timeout=300s
  │
  └─ Mixed (LLM analysis)
      └─ Use Config C: max_concurrent=5-8, timeout=120s

How many tasks?
  │
  ├─ < 10 → All at once (Pattern A)
  │
  ├─ 10-50 → Chunked (Pattern C), batch_size=10
  │
  └─ > 50 → Priority Queue (Pattern D), batches of 20
```

## §6. Anti-Patterns

| ❌ Wrong | ✅ Correct |
|----------|------------|
| Run 50 LLM calls simultaneously | Cap at 5, use queue |
| Use compute-bound config for IO | Use IO-bound config (higher concurrency) |
| Ignore rate limits | Add delays, queue requests |
| No memory calculation | Estimate memory × tasks < 80% RAM |
| Hard-code concurrency | Calculate based on system resources |

## §7. Quick Reference Table

| Scenario | Workload | Max Concurrent | Pattern | Timeout |
|----------|----------|----------------|---------|---------|
| Fetch 50 PDFs | IO | 15 | Chunked | 60s |
| Parse 100 PDFs | Compute | 6 | Parallel | 300s |
| Analyze 20 papers (LLM) | Mixed | 5 | Pipeline | 120s |
| 5 independent docs → L1 | Mixed | 5 | Map-Reduce | 120s |
| 1112p manual → L3 | Mixed | 11 | Hierarchical | 180s |