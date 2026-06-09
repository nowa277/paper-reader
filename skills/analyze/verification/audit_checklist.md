# Verification Audit Checklist

Based on spec §15.3 — 15 acceptance criteria items.

---

## Wiki Quality (6 items)

### 1. Wikilink Format ✓
**Check:** All wikilinks use correct syntax `[[概念]]`

**Valid patterns:**
- `[[概念名]]` — basic
- `[[概念名|显示文本]]` — with alias
- `[[#概念名]]` — anchor

**Invalid:**
- `[概念名](url)` — markdown link (not wikilink)
- `[[概念` — unclosed
- `[[]]` — empty

**Check function:** `verification.levels.check_wikilink_format()`

---

### 2. Concept Uniqueness ✓
**Check:** No duplicate concepts (dedupe, keep most complete definition)

**Method:**
1. Extract all `[[概念]]` 
2. Group by name (case-insensitive)
3. If duplicates exist, keep definition with longest text

**Check function:** `verification.levels.check_no_orphan_nodes()` (partial)

---

### 3. Concept Has Definition ✓
**Check:** Every concept has a definition (not an empty link)

**Valid patterns after first occurrence:**
- `[[概念]]: 定义内容`
- `[[概念]] — 定义内容`
- `**[[概念]]**: 定义内容`

**Invalid:**
- `[[概念]]` appearing alone with no following text

**Check function:** `verification.levels.check_concept_definitions()`

---

### 4. Backlinks Exist ✓
**Check:** Each concept is referenced at least once beyond its definition

**Method:**
- First occurrence = definition location
- Subsequent occurrences = backlinks

**Threshold:** Every concept must appear ≥2 times

**Check function:** `verification.levels.check_backlinks_exist()`

---

### 5. Heading Hierarchy ✓
**Check:** Section hierarchy is continuous (h1→h2→h3, no skips)

**Valid:** `h1 → h2 → h2 → h3`
**Invalid:** `h1 → h3` (skipped h2)

**Check function:** `verification.levels.check_hierarchy_levels()`

---

### 6. Source Citations ✓
**Check:** Key claims have source citations `[来源: §章节]`

**Pattern:** `[来源:` or `[source:` or `[cite:`

**Note:** Only required for key claims in L3/L4, optional for L1/L2

---

## KG Quality (4 items)

### 7. Node Schema Compliance ✓
**Check:** Node types match granularity level

| Level | Expected Nodes |
|-------|----------------|
| L1 | concept only |
| L2 | concept + relation |
| L3 | concept + relation + hierarchy |
| L4 | + evidence |

**Check function:** `verification.levels.check_kg_schema_compliance()`

---

### 8. Relation Type Controlled Vocabulary ✓
**Check:** All relation types come from controlled vocabulary

**Allowed relation types:**
- `contains`, `uses`, `part_of`, `is_a`, `depends_on`, `implements`
- `inherits_from`, `references`, `similar_to`, `contradicts`

**Forbidden (must be replaced):**
- "相关" / "有关系" / "有关" — too vague
- "depends" — specify direction

**Check:** KG export or content search for uncontrolled types

---

### 9. Key Relations Have Evidence ✓
**Check:** Important relations have evidence citations

**Method:**
- For each relation edge, check if evidence string exists
- Evidence format: `(source: §section, page: N)` or similar

**Threshold:** ≥50% of relations should have evidence (L4: 100%)

---

### 10. Graph Connectedness ✓
**Check:** No isolated connected components

**Method:**
- Build adjacency list from relations
- Run BFS/DFS to find connected components
- Largest component should contain ≥90% of nodes

**Check function:** `verification.levels.check_no_orphan_nodes()` (conceptually similar)

---

## Obsidian Standards (5 items)

### 11. Frontmatter YAML ✓
**Check:** YAML frontmatter exists at file top

**Required fields:**
```yaml
---
title: Concept Name
type: concept  # or: relation, hierarchy
tags: [#tag1, #tag2]
---
```

**Check function:** `verification.levels.check_frontmatter_exists()`

---

### 12. Tags Format ✓
**Check:** All tags use `#tagname` format

**Valid:** `#concept`, `#relation`, `#chapter-1`
**Invalid:** `tags: [tag1, tag2]` (YAML list, not Obsidian format)

---

### 13. Image Embedding ✓
**Check:** Images embedded with Obsidian syntax

**Valid:**
- `![[image.png]]` — obsidian embed
- `![alt](path/to/image.png)` — markdown (OK but less preferred)

**Check function:** `verification.levels.check_image_syntax()`

---

### 14. Callout Format ✓
**Check:** Obsidian callouts use correct syntax

**Valid:** `> [!note]`, `> [!warning]`, `> [!tip]`, `> [!danger]`
**Invalid:** `> Note:`, `> **Note**`

**Check function:** `verification.levels.check_callout_format()`

---

### 15. Bidirectional Links ✓
**Check:** Internal links are bidirectional

**Method:**
1. Extract all `[[链接]]` from file
2. For each link, check if target file has backlink
3. Report any unidirectional links

**Note:** Requires file system access to check target files

---

## Usage

```python
from skills.analyze.verification import run_full_verification, VerificationLevel

# Run all checks
report = run_full_verification(
    content="...",
    levels=[VerificationLevel.L1, VerificationLevel.L2, VerificationLevel.L3],
)

print(f"Passed: {report.total_passed}, Failed: {report.total_failed}")
print(f"All checks passed: {report.all_passed}")
```

## Thresholds Summary

| Check | Threshold | Level |
|-------|-----------|-------|
| Wikilink syntax | 100% | L1 |
| Concept definitions | ≥80% sampled | L2 |
| Backlinks | 100% | L2 |
| Heading hierarchy | No skips | L3 |
| Orphan nodes | 0 | L3 |
| KG schema | Per level | L2+ |
| Evidence citations | ≥50% (L4: 100%) | L3+ |
| Graph connectedness | ≥90% in largest component | L3+ |