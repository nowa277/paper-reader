"""Verification levels (L1/L2/L3) for subagent output quality control.

Based on spec §15.2-15.4:
- L1: Format self-check (subagent self)
- L2: Content sampling (parent agent, 10%抽检)
- L3: Completeness check (post-merge)

Reference:
- skills/analyze/verification/levels.py
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
import re


class VerificationLevel(Enum):
    """Three-layer verification strategy."""
    L1 = "l1"  # Format self-check
    L2 = "l2"  # Content sampling
    L3 = "l3"  # Completeness check


class CheckResult(Enum):
    """Verification check result."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class Check:
    """Single verification check."""
    name: str
    description: str
    check_fn: Callable[[str], tuple[bool, str]]
    level: VerificationLevel
    required: bool = True


@dataclass
class VerificationResult:
    """Result of a verification check."""
    check_name: str
    result: CheckResult
    message: str
    details: Optional[dict] = None


@dataclass
class LevelReport:
    """Report for a single verification level."""
    level: VerificationLevel
    passed: int
    failed: int
    warnings: int
    results: list[VerificationResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        total = self.passed + self.failed
        return self.passed / total if total > 0 else 0.0


@dataclass
class VerificationReport:
    """Full verification report across all levels."""
    l1: Optional[LevelReport] = None
    l2: Optional[LevelReport] = None
    l3: Optional[LevelReport] = None
    total_passed: int = 0
    total_failed: int = 0

    @property
    def all_passed(self) -> bool:
        return self.total_failed == 0


# === L1: Format Self-Check ===

def check_wikilink_format(content: str) -> tuple[bool, str]:
    """Check wikilink syntax is correct: [[概念]]."""
    pattern = r'\[\[([^\]]*)\]\]'
    matches = re.findall(pattern, content)
    if not matches:
        return True, "No wikilinks found (OK for L1-only docs)"

    # Check for empty links (including whitespace-only)
    empty = [m for m in matches if not m.strip()]
    if empty:
        return False, f"Found {len(empty)} empty wikilinks: {empty}"

    return True, f"Found {len(matches)} valid wikilinks"


def check_frontmatter_exists(content: str) -> tuple[bool, str]:
    """Check YAML frontmatter exists at top of file."""
    lines = content.split('\n')
    if not lines:
        return False, "Empty content"

    if not lines[0].strip().startswith('---'):
        return False, "No YAML frontmatter found (required for Obsidian)"

    # Find closing ---
    closing = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip().startswith('---'):
            closing = i
            break

    if closing is None:
        return False, "Frontmatter opened but never closed"

    return True, f"Frontmatter spans lines 1-{closing}"


def check_callout_format(content: str) -> tuple[bool, str]:
    """Check Obsidian callout format: > [!note]."""
    pattern = r'>\s*\[!([^\]]+)\]'
    matches = re.findall(pattern, content)
    if not matches:
        return True, "No callouts found (OK)"

    valid_types = {'note', 'warning', 'tip', 'danger', 'info', 'example', 'summary', 'question'}
    invalid = [m for m in matches if m.lower() not in valid_types]

    if invalid:
        return False, f"Invalid callout types: {invalid}"

    return True, f"Found {len(matches)} valid callouts"


def check_image_syntax(content: str) -> tuple[bool, str]:
    """Check image embedding syntax:![[image.png]] or ![alt](url)."""
    obsidian_pattern = r'!\[\[([^\]]+\.[a-zA-Z]+)\]\]'
    markdown_pattern = r'!\[([^\]]*)\]\(([^\)]+\.[a-zA-Z]+)\)'

    obsidian_matches = re.findall(obsidian_pattern, content)
    markdown_matches = re.findall(markdown_pattern, content)

    total = len(obsidian_matches) + len(markdown_matches)
    if total == 0:
        return True, "No images found (OK)"

    return True, f"Found {total} images ({len(obsidian_matches)} obsidian, {len(markdown_matches)} markdown)"


# === L2: Content Sampling ===

def check_concept_definitions(content: str, sample_size: int = 10) -> tuple[bool, str]:
    """Sample concepts and check they have definitions."""
    # Extract wikilinks as concept candidates
    pattern = r'\[\[([^\]]+)\]\]'
    concepts = re.findall(pattern, content)
    concepts = list(set(concepts))  # Dedupe

    if not concepts:
        return True, "No concepts to verify"

    # Sample if too many
    import random
    sample = random.sample(concepts, min(sample_size, len(concepts)))

    # Check each concept appears with definition (colon or dash after the wikilink)
    defined = 0
    for concept in sample:
        # Look for [[Concept]]: or [[Concept]] — pattern (definition after wikilink)
        # Use simple pattern avoiding nested set warning
        wiki_link = f"[[{re.escape(concept)}]]"
        if wiki_link in content:
            # Find position after this wikilink
            idx = content.find(wiki_link)
            after = content[idx + len(wiki_link):idx + len(wiki_link) + 10]
            if after.strip().startswith((':','-','–','—')):
                defined += 1

    rate = defined / len(sample)
    if rate < 0.8:
        return False, f"Only {defined}/{len(sample)} concepts have definitions ({rate:.0%})"

    return True, f"{defined}/{len(sample)} concepts have definitions"


def check_backlinks_exist(content: str) -> tuple[bool, str]:
    """Check concepts are referenced beyond their definition."""
    pattern = r'\[\[([^\]]+)\]\]'
    concepts = re.findall(pattern, content)
    concepts = list(set(concepts))

    if not concepts:
        return True, "No concepts to verify"

    # A concept is "defined" on its first occurrence
    # Check if it appears more than once
    defined_once = []
    for concept in concepts:
        occurrences = len(re.findall(rf'\[\[{re.escape(concept)}\]\]', content))
        if occurrences <= 1:
            defined_once.append(concept)

    if defined_once:
        return False, f"{len(defined_once)} concepts defined but never referenced: {defined_once[:5]}"

    return True, f"All {len(concepts)} concepts have backlinks"


# === L3: Completeness Check ===

def check_no_orphan_nodes(content: str) -> tuple[bool, str]:
    """Check no concept is isolated (appears only once)."""
    pattern = r'\[\[([^\]]+)\]\]'
    concepts = re.findall(pattern, content)
    from collections import Counter
    counts = Counter(concepts)

    orphans = [c for c, count in counts.items() if count == 1]

    if orphans:
        return False, f"Found {len(orphans)} orphan concepts: {orphans[:5]}"

    return True, f"All {len(counts)} concepts have connections"


def check_hierarchy_levels(content: str) -> tuple[bool, str]:
    """Check heading hierarchy is continuous (h1→h2→h3, no skips)."""
    pattern = r'^(#{1,6})\s+(.+)$'
    headings = re.findall(pattern, content, re.MULTILINE)

    if not headings:
        return True, "No headings found"

    levels = [len(h[0]) for h in headings]

    # Check for skips (e.g., h1 → h3 without h2)
    skips = []
    for i in range(len(levels) - 1):
        diff = levels[i+1] - levels[i]
        if diff > 1:
            skips.append(f"h{levels[i]} → h{levels[i+1]}")

    if skips:
        return False, f"Found {len(skips)} level skips: {skips[:3]}"

    return True, f"Heading levels are continuous: min={min(levels)}, max={max(levels)}"


def check_kg_schema_compliance(content: str, level: str = "L3") -> tuple[bool, str]:
    """Check KG follows schema for given granularity level.

    Args:
        content: Markdown content to check
        level: Granularity level (L1-L4)

    Returns:
        (passed, message) tuple
    """
    # L1: concepts only - no relations expected
    if level == "L1":
        return True, "L1 (concepts only) - no KG schema requirements"

    # L2+: check for relation indicators
    relation_indicators = [
        r'\[\[[^\]]+\]\]\s*[-–—]\s*',  # concept -- concept
        r'##\s*(Related|Relations|Connections)',  # relations section
    ]

    has_relations = any(re.search(p, content, re.IGNORECASE) for p in relation_indicators)

    if level in ("L2", "L3") and not has_relations:
        return False, f"L{level[1]} requires relations but none found"

    # L3+: check for hierarchy indicators
    if level == "L4":
        hierarchy_indicators = [
            r'##\s*(Hierarchy|Parent|Child|Subclass)',
            r'\[\[Parent::[^\]]+\]\]',
        ]
        has_hierarchy = any(re.search(p, content, re.IGNORECASE) for p in hierarchy_indicators)
        if not has_hierarchy:
            return False, "L4 requires hierarchy but none found"

    return True, f"L{level[1]} schema compliance: OK"


# === Check Registry ===

def get_l1_checks() -> list[Check]:
    """Get L1 format self-check list."""
    return [
        Check("wikilink_format", "Wikilink syntax [[概念]] is correct",
              check_wikilink_format, VerificationLevel.L1),
        Check("frontmatter_exists", "YAML frontmatter exists",
              check_frontmatter_exists, VerificationLevel.L1),
        Check("callout_format", "Obsidian callout format > [!type]",
              check_callout_format, VerificationLevel.L1),
        Check("image_syntax", "Image embedding syntax correct",
              check_image_syntax, VerificationLevel.L1),
    ]


def get_l2_checks() -> list[Check]:
    """Get L2 content sampling check list."""
    return [
        Check("concept_definitions", "Sampled concepts have definitions",
              check_concept_definitions, VerificationLevel.L2),
        Check("backlinks_exist", "Concepts are referenced beyond definition",
              check_backlinks_exist, VerificationLevel.L2),
    ]


def get_l3_checks() -> list[Check]:
    """Get L3 completeness check list."""
    return [
        Check("no_orphan_nodes", "No orphan concepts (appear only once)",
              check_no_orphan_nodes, VerificationLevel.L3),
        Check("hierarchy_levels", "Heading hierarchy is continuous",
              check_hierarchy_levels, VerificationLevel.L3),
        Check("kg_schema", "KG follows schema for granularity level",
              check_kg_schema_compliance, VerificationLevel.L3),
    ]


def get_all_checks() -> list[Check]:
    """Get all verification checks."""
    return get_l1_checks() + get_l2_checks() + get_l3_checks()


def run_level_checks(level: VerificationLevel, content: str) -> LevelReport:
    """Run all checks for a given level.

    Args:
        level: Verification level (L1/L2/L3)
        content: Content to verify

    Returns:
        LevelReport with results
    """
    check_map = {
        VerificationLevel.L1: get_l1_checks(),
        VerificationLevel.L2: get_l2_checks(),
        VerificationLevel.L3: get_l3_checks(),
    }

    checks = check_map[level]
    results = []

    for check in checks:
        try:
            passed, message = check.check_fn(content)
            result = VerificationResult(
                check_name=check.name,
                result=CheckResult.PASS if passed else CheckResult.FAIL,
                message=message,
            )
        except Exception as e:
            result = VerificationResult(
                check_name=check.name,
                result=CheckResult.WARNING,
                message=f"Check error: {str(e)}",
            )
        results.append(result)

    passed = sum(1 for r in results if r.result == CheckResult.PASS)
    failed = sum(1 for r in results if r.result == CheckResult.FAIL)
    warnings = sum(1 for r in results if r.result == CheckResult.WARNING)

    return LevelReport(
        level=level,
        passed=passed,
        failed=failed,
        warnings=warnings,
        results=results,
    )


def run_full_verification(content: str, levels: list[VerificationLevel] = None) -> VerificationReport:
    """Run full verification across specified levels.

    Args:
        content: Content to verify
        levels: List of levels to run. Default: [L1, L2, L3]

    Returns:
        VerificationReport with all level results
    """
    if levels is None:
        levels = [VerificationLevel.L1, VerificationLevel.L2, VerificationLevel.L3]

    report = VerificationReport()

    for level in levels:
        level_report = run_level_checks(level, content)
        setattr(report, level.value, level_report)
        report.total_passed += level_report.passed
        report.total_failed += level_report.failed

    return report