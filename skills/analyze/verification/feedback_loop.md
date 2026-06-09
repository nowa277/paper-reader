# Feedback Loop — 3-Layer Verification Flow

Based on spec §15.4 — feedback loop diagram and failure handling.

---

## 3-Layer Verification Flow

```
                    ┌─────────────────────┐
                    │  Subagent Output    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   L1: Format Check   │ ← subagent self-check
                    │  (wikilink, front-   │
                    │   matter, callout)   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
       ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
       │   PASS      │  │   FAIL      │  │   WARN      │
       └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
              │                │                │
              │        ┌───────▼───────┐        │
              │        │ Retry L1 (1x) │        │
              │        │ Shuffle prompt│        │
              │        └───────┬───────┘        │
              │                │                │
              │        ┌───────▼───────┐        │
              │        │ Re-run L1     │        │
              │        └───────┬───────┘        │
              │                │                │
       ┌──────▼──────┐  ┌──────▼──────┐         │
       │    L2:      │◄─┤   Continue  │─────────┘
       │  Sampling   │  │   to L2     │
       │   (10%)     │  └─────────────┘
       └──────┬──────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼───┐ ┌──▼──┐ ┌───▼───┐
│ PASS  │ │FAIL │ │ WARN  │
└───┬───┘ └──┬──┘ └───┬───┘
    │        │        │
    │   ┌────▼────┐   │
    │   │ >20%    │   │
    │   │ failure │   │
    │   │ rate?   │   │
    │   └────┬────┘   │
    │        │        │
    │   ┌───▼────┐    │
    │   │Retry   │    │
    │   │L2 with │    │
    │   │failure │    │
    │   │samples │    │
    │   └───┬────┘    │
    │        │        │
    │   ┌───▼────┐    │
    │   │Re-run  │    │
    │   │L2      │────┘
    │   └───┬────┘
    │        │
┌───▼───────▼────┐
│   L3:         │
│ Completeness  │
│   Check       │
└───────┬───────┘
        │
   ┌────┴────┐
   │         │
┌──���──┐ ┌───▼───┐
│FAIL │ │ PASS  │
└┬┬──┘ └───┬───┘
 ││        │
 ││   ┌────▼────┐
 ││   │ Final   │
 ││   │ Output  │
 ││   └─────────┘
 ││
 ││   ┌────────────────┐
 │└──►│ Auto-retry (1x)│
 │    └───────┬────────┘
 │            │
 │      ┌─────▼─────┐
 │      │ Re-run L3 │
 │      └─────┬─────┘
 │            │
 │      ┌─────▼─────┐
 │      │ Still     │──Yes──► [ASK USER]
 │      │ fails?    │
 │      └─────┬─────┘
 │            │ No
 │      ┌─────▼─────┐
 └─────►│  Final    │
        │  Output   │
        └───────────┘
```

---

## Failure Handling Rules

### L1: Format Self-Check (subagent self)

| Condition | Action |
|-----------|--------|
| Any check fails | **Immediate retry** (1x) |
| After retry still fails | Move to L2, log in progress.md |

**Retry behavior:**
- Subagent retries with **same content**
- **Shuffle prompt order** — don't read previous failure
- Log: `<task_id>: L1 failed @ <timestamp>, retried with shuffled prompt`

---

### L2: Content Sampling (parent agent, 10%)

| Condition | Action |
|-----------|--------|
| Failure rate ≤ 20% | Pass (acceptable variance) |
| Failure rate > 20% | **Trigger that subagent retry** with failure samples |

**Retry behavior:**
- Parent agent collects failure samples (which wikilinks wrong, which concepts empty)
- Feeds failure samples back to subagent
- Subagent re-runs with failure context
- Log: `<task_id>: L2 failure rate {rate:.0%} > 20%, triggered retry with samples`

---

### L3: Completeness Check (post-merge)

| Condition | Action |
|-----------|--------|
| Any check fails | **Auto-retry once** (avoid false positive from small sample) |
| After auto-retry still fails | **Ask user** — continue / abort / partial result |

**Retry behavior:**
- Parent agent auto-re-runs L3 checks
- No prompt shuffle needed (different issue from L1)
- Log: `<task_id>: L3 failed @ <timestamp>, auto-retry initiated`

---

## Failed Artifact Handling

### Spec §15.4 Rule: "Failed subagent artifacts are directly deleted"

| Stage | Action |
|-------|--------|
| L1 retry fails | Continue to L2 |
| L2 retry fails | Continue to L3 |
| L3 auto-retry fails | **Ask user** |
| User decides to abort | Delete artifact, log only in progress.md |

**Deletion rules:**
- ❌ Do NOT keep `failed/<subagent_id>/` directory
- ❌ Do NOT archive failed outputs
- ✅ DO log one line in `progress.md`: `<task_id>: L<N> failed @ <timestamp>, deleted`

**Rationale:**
- Reduces disk usage
- Reduces review burden (no need to review failures)
- progress.md already captures failure info

---

## Progress.md Log Format

```
timestamp | task_id | action | level | message
```

**Examples:**
```
2026-06-09 10:23:45 | subagent_001 | retry_l1 | L1 | wikilink format error, shuffled prompt
2026-06-09 10:24:12 | subagent_002 | retry_l2_sample | L2 | 25% failure rate > 20%, with failure samples
2026-06-09 10:25:33 | subagent_003 | retry_l3 | L3 | auto-retry initiated
2026-06-09 10:26:01 | subagent_003 | ask_user | L3 | retries exhausted, need user decision
2026-06-09 10:26:15 | subagent_004 | delete_artifact | N/A | L3 failed after all retries, deleted
```

---

## Anti-Patterns

### ❌ Don't retry more than configured
- L1: max 1 retry (spec §15.4)
- L2: retry only when > 20% failure rate
- L3: max 1 auto-retry

### ❌ Don't keep failed artifacts
- Direct delete, no `failed/` subdirectory
- Only progress.md log entry

### ❌ Don't block on L1/L2 failures
- These are "auto-recovery" (不阻塞)
- Only L3 exhaustion triggers user prompt

### ❌ Don't retry with same prompt order
- L1 retry: shuffle prompt order to avoid same mistake
- L2 retry: include failure samples (different from L1)

---

## Integration with subagent_policy.py

The `FailurePolicy` from `subagent_policy.py` maps to verification layers:

| FailurePolicy field | Verification Layer |
|---------------------|--------------------|
| `l1_retries` | L1 retry count (default: 1) |
| `l2_retries` | L2 retry trigger (failure rate > 20%) |
| `l3_retries` | L3 auto-retry count (default: 1) |

```python
from skills.analyze.subagent_policy import create_failure_policy
from skills.analyze.verification.runner import VerificationRunner

# Use subagent_policy config
policy = create_failure_policy(l1_retries=1, l2_retries=1, l3_retries=1)
runner = VerificationRunner(
    config=RetryConfig(
        l1_max_retries=policy.l1_retries,
        l2_failure_threshold=0.20,
        l3_max_retries=policy.l3_retries,
    )
)
```

---

## Summary

| Layer | Trigger | Retry | Log |
|-------|---------|-------|-----|
| L1 | subagent self | 1x, shuffled prompt | progress.md |
| L2 | parent (10% sample) | If >20% fail, with samples | progress.md |
| L3 | post-merge | 1x auto-retry | progress.md → ask user |
| Artifact | all retries exhausted | N/A | Delete + log only |