# Subagent Failure Handling — Retry, Recovery, and Escalation

> **Agent methodology:** Read this when subagents fail. This document provides the failure handling strategy including retry policies, checkpoint recovery, and escalation rules.

## §1 Failure Management Overview

Long-running subagent tasks can fail. This document provides a systematic approach to:
1. Detect failure at appropriate granularity (L1/L2/L3 verification)
2. Apply appropriate retry policy
3. Recover from checkpoints without restarting from scratch
4. Escalate to human when auto-recovery exhausted

**Core principle:** Fail fast, recover faster. Don't block long tasks on transient failures.

## §2 Three-Layer Verification & Retry

### 2.1 L1: Format Self-Check (Subagent Self)

**What:** Subagent verifies its own output before returning
- File exists and is readable
- Required fields present in frontmatter
- Wikilink syntax valid (`[[concept]]` format)
- No obvious structural issues

**Failure action:** Subagent immediately retries **once** with same or improved prompt
- No human notification
- Max 1 automatic retry
- If still fails → mark as L1_FAILED, proceed to parent

### 2.2 L2: Content Sampling (Parent Agent)

**What:** Parent agent samples 10% of subagent outputs for quality check
- Concept definitions present and non-empty
- Backlinks exist for key concepts
- References traceable (citations valid)

**Failure trigger:** If >20% of sampled items fail → trigger retry for that subagent

**Failure action:**
- Mark subagent for retry with different prompt order
- Do NOT reuse failed prompt (avoid same mistakes)
- If retry fails → L2_FAILED, include in aggregation with warning flag

### 2.3 L3: Completeness Check (Post-Merge)

**What:** After aggregation, run full integrity check
- No duplicate concepts (after dedupe)
- No orphaned nodes in KG
- Obsidian format compliance
- All wikilinks resolve to existing concepts

**Failure action:**
- Auto-retry synthesis once
- If still fails → ESCALATE to user with options:
  - Continue with partial results
  - Retry specific subagents
  - Abort and restart with different strategy

## §3 Retry Policy Specification

### 3.1 Retry Rules Matrix

| Failure Type | Retry Count | Retry Strategy | On Exhaustion |
|---|---|---|---|
| L1 format fail | 1 | Same subagent, same prompt | Mark L1_FAILED, continue |
| L2 content fail (rate >20%) | 1 | Same subagent, **different prompt order** | Mark L2_FAILED, continue with warning |
| L3 synthesis fail | 1 | Re-run synthesis with modified prompt | ESCALATE to user |
| Timeout (no output 10min) | 1 | Restart subagent | Mark TIMEOUT_FAILED |
| Network/connection fail | 2 | Wait 30s, retry | Mark CONNECTION_FAILED |

### 3.2 Prompt Modification on Retry

**Critical rule:** When retrying a failed subagent, MODIFY the prompt:
- **Don't:** Re-run with identical prompt (will likely fail same way)
- **Do:** Shuffle prompt sections, re-order instructions, add examples

```python
# Example: Shuffle prompt order on retry
def modify_prompt_for_retry(original_prompt: str, attempt: int) -> str:
    sections = original_prompt.split("## ")
    if attempt == 1 and len(sections) > 2:
        # Reorder sections: put analysis instructions first
        reordered = ["## " + sections[1], "## " + sections[0]] + sections[2:]
        return "\n## ".join(reordered)
    return original_prompt
```

### 3.3 Failed Subagent Artifacts

**Policy:** Delete failed subagent outputs immediately. Do NOT keep failed/ directory.

```bash
# When subagent fails (after exhausting retries):
rm -rf <subagent_output_dir>/    # Immediate deletion
# Do NOT create failed/ or archive/ directories
# Logs already capture failure reason
```

Rationale: Failed artifacts pollute the workspace and create confusion about what's valid.

## §4 Checkpoint & Recovery

### 4.1 Checkpoint Frequency

**Rule:** Write checkpoint after **every single subagent completes**
- File: `progress.md` in working directory
- Records: which subagents completed, their outputs, any warnings

### 4.2 Progress.md Format

```markdown
# Progress: <Task Name>

## Completed Subagents
- [x] subagent_01 (chunk 1-100) - SUCCESS
- [x] subagent_02 (chunk 101-200) - SUCCESS  
- [x] subagent_03 (chunk 201-300) - L1_FAILED (auto-retry succeeded)

## In Progress
- [ ] subagent_04 (chunk 301-400) - RUNNING

## Failed (Exhausted Retries)
- [ ] subagent_05 (chunk 401-500) - L3_FAILED (escalated to user)

## Last Updated
2026-06-08T14:32:00Z
```

### 4.3 Recovery from Checkpoint

When task resumes after interruption:

```python
def recover_from_checkpoint(progress_path: str) -> list[str]:
    """Return list of subagent IDs still to run."""
    completed = []
    with open(progress_path) as f:
        for line in f:
            if line.startswith("- [x] subagent_"):
                # Extract subagent ID
                subagent_id = line.split()[2]  # subagent_XX
                completed.append(subagent_id)
    
    # Return remaining subagent IDs
    return [s for s in all_subagent_ids if s not in completed]
```

**Recovery options for user:**
1. **Resume** — Continue from checkpoint (default)
2. **Modify** — Change strategy, restart with new plan
3. **Partial** — Accept completed subagents only, abort remaining

### 4.4 Context Recovery

When recovering, parent agent must:
1. Load `progress.md` to see completed work
2. Load the last completed subagent's output (if needed for context)
3. Resume with remaining subagents
4. **Do NOT re-run completed subagents** (waste of tokens)

## §5 Escalation Rules

### 5.1 When to Escalate

Escalate to user when:
- L3 retry exhausted (synthesis failed twice)
- >50% subagents failed in a single batch
- Checkpoint corrupted/unreadable
- User decision required (continue/modify/abort)

### 5.2 Escalation Message Template

```markdown
## ⚠️ Subagent Task Requires Attention

**Task:** <name>
**Status:** <N>/<M> subagents completed, <K> failed

**Failed subagents:**
- subagent_03: L3 synthesis failed (auto-retry exhausted)
- subagent_07: Timeout (10min no output)

**Options:**
1. **[R]esume** — Continue from checkpoint, skip failed
2. **[M]odify** — Change strategy, restart with different approach
3. **[P]artial** — Accept completed results, abort remaining
4. **[A]bort** — Stop entirely, discard all outputs

**Your choice?**
```

### 5.3 Auto-Escalation Triggers

- 3 consecutive L3 failures
- Total failure rate > 30%
- Any unhandled exception in parent orchestration

## §6 Anti-Patterns

### 6.1 Don't Do These

| Anti-Pattern | Why It's Bad | Correct Approach |
|---|---|---|
| Retry with identical prompt | Will likely fail same way | Shuffle prompt order |
| Keep failed artifacts | Pollutes workspace, confuses | Delete immediately |
| Block on L1/L2 failures | Defeats parallel purpose | Auto-retry, continue |
| Manual restart from scratch | Waste of completed work | Use checkpoint recovery |
| Hide failures from user | Erodes trust | Escalate transparently |

### 6.2 Don't Wait For

- Perfect convergence (80% quality is often enough)
- All subagents to succeed (failure is normal)
- User to notice problems (escalate proactively)

## §7 Quick Reference

```
FAILURE HANDLING FLOW:

Subagent completes
    ↓
L1 Check (self) → FAIL → retry once → success? → continue
    ↓ (fail)
L2 Check (parent 10%) → >20% fail → retry once → success? → continue  
    ↓ (fail)
L3 Check (post-merge) → fail → auto-retry once → success? → continue
    ↓ (fail)
ESCALATE to user with options

CHECKPOINT: Write progress.md after EVERY subagent
RECOVERY: Load progress.md, skip completed, resume remaining
FAILED ARTIFACTS: Delete immediately, no archive
```

**Remember:** Fail fast, retry smart, recover from checkpoint, escalate transparently.