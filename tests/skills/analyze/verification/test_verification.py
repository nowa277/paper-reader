"""Tests for verification module.

Tests for:
- token_estimator.py
- levels.py (L1/L2/L3 checks)
- runner.py (feedback loop)
"""

import pytest
from skills.analyze.verification.token_estimator import (
    TokenEstimator,
    TriggerMode,
    TOKEN_THRESHOLD_SINGLE,
    TOKEN_THRESHOLD_MAP_REDUCE,
    TOKEN_THRESHOLD_HIERARCHICAL,
    quick_estimate,
    should_split_subagent,
    estimate_and_decide,
)


class TestTokenEstimator:
    """Tests for TokenEstimator class."""

    def test_estimator_initialization(self):
        """Test estimator can be initialized."""
        estimator = TokenEstimator()
        assert estimator._model == "cl100k_base"

    def test_estimate_empty_string(self):
        """Test estimation of empty string."""
        estimator = TokenEstimator()
        tokens = estimator.estimate("")
        assert tokens == 0

    def test_estimate_simple_text(self):
        """Test estimation of simple text."""
        estimator = TokenEstimator()
        text = "This is a test."
        tokens = estimator.estimate(text)
        assert tokens > 0

    def test_single_mode_under_threshold(self):
        """Test SINGLE trigger mode for small text."""
        estimator = TokenEstimator()
        text = "short text"
        tokens = estimator.estimate(text)
        mode = estimator.get_trigger_mode(tokens)
        assert mode == TriggerMode.SINGLE

    def test_map_reduce_mode(self):
        """Test MAP_REDUCE trigger mode for mid-range tokens."""
        estimator = TokenEstimator()
        # Use get_trigger_mode directly with known threshold values
        mode = estimator.get_trigger_mode(100_000)  # Between 50K-200K
        assert mode == TriggerMode.MAP_REDUCE

    def test_hierarchical_mode_over_threshold(self):
        """Test HIERARCHICAL trigger mode for large text."""
        estimator = TokenEstimator()
        # Use get_trigger_mode directly - over 500K
        mode = estimator.get_trigger_mode(600_000)
        assert mode == TriggerMode.HIERARCHICAL

    def test_get_chunk_count_single(self):
        """Test chunk count for small content."""
        estimator = TokenEstimator()
        chunks = estimator.get_chunk_count(50000)
        assert chunks == 1

    def test_get_chunk_count_multiple(self):
        """Test chunk count for large content."""
        estimator = TokenEstimator()
        chunks = estimator.get_chunk_count(250000)
        assert chunks == 3  # 250K / 100K = 2.5 → 3

    def test_quick_estimate(self):
        """Test quick word-based estimation."""
        text = "one two three four five"
        tokens = quick_estimate(text)
        # 5 words → ~6-7 tokens
        assert 5 <= tokens <= 10

    def test_should_split_subagent(self):
        """Test subagent split decision."""
        # Small: should not split
        assert should_split_subagent(30000) == False

        # Large: should split
        assert should_split_subagent(300000) == True

    def test_estimate_and_decide(self):
        """Test one-shot estimation and decision."""
        text = "test content"
        tokens, mode, chunks = estimate_and_decide(text)
        assert tokens > 0
        assert isinstance(mode, TriggerMode)
        assert chunks >= 1


class TestTriggerModeEnum:
    """Tests for TriggerMode enum values."""

    def test_all_modes_exist(self):
        """Test all expected modes are defined."""
        assert TriggerMode.SINGLE.value == "single"
        assert TriggerMode.MAP_REDUCE.value == "map_reduce"
        assert TriggerMode.MAP_REDUCE_OR_HIERARCHICAL.value == "map_reduce_or_hierarchical"
        assert TriggerMode.HIERARCHICAL.value == "hierarchical"

    def test_threshold_constants(self):
        """Test token threshold constants."""
        assert TOKEN_THRESHOLD_SINGLE == 50_000
        assert TOKEN_THRESHOLD_MAP_REDUCE == 200_000
        assert TOKEN_THRESHOLD_HIERARCHICAL == 500_000


# === Tests for levels.py ===

from skills.analyze.verification.levels import (
    check_wikilink_format,
    check_frontmatter_exists,
    check_callout_format,
    check_image_syntax,
    check_concept_definitions,
    check_backlinks_exist,
    check_no_orphan_nodes,
    check_hierarchy_levels,
    check_kg_schema_compliance,
    get_l1_checks,
    get_l2_checks,
    get_l3_checks,
    run_level_checks,
    run_full_verification,
    VerificationLevel,
    CheckResult,
)


class TestL1Checks:
    """Tests for L1 format self-check functions."""

    def test_wikilink_valid(self):
        """Test valid wikilinks pass."""
        content = "See [[ConceptName]] for details."
        passed, msg = check_wikilink_format(content)
        assert passed == True

    def test_wikilink_empty(self):
        """Test empty wikilink fails."""
        content = "Link to [[]] is invalid."
        passed, msg = check_wikilink_format(content)
        assert passed == False

    def test_wikilink_with_alias(self):
        """Test wikilink with alias passes."""
        content = "See [[Concept|Display Text]] for more."
        passed, msg = check_wikilink_format(content)
        assert passed == True

    def test_frontmatter_exists_valid(self):
        """Test valid frontmatter passes."""
        content = """---
title: Test
tags: [test]
---
# Content
"""
        passed, msg = check_frontmatter_exists(content)
        assert passed == True

    def test_frontmatter_missing(self):
        """Test missing frontmatter fails."""
        content = "# Just a heading"
        passed, msg = check_frontmatter_exists(content)
        assert passed == False

    def test_frontmatter_unclosed(self):
        """Test unclosed frontmatter fails."""
        content = """---
title: Test
# No closing ---
# Content
"""
        passed, msg = check_frontmatter_exists(content)
        assert passed == False

    def test_callout_valid(self):
        """Test valid callouts pass."""
        content = """> [!note]
> This is a note.
"""
        passed, msg = check_callout_format(content)
        assert passed == True

    def test_callout_invalid_type(self):
        """Test invalid callout type fails."""
        content = """> [!invalid_type]
> This is invalid.
"""
        passed, msg = check_callout_format(content)
        assert passed == False

    def test_image_syntax_obsidian(self):
        """Test Obsidian image syntax passes."""
        content = "See ![[image.png]] for details."
        passed, msg = check_image_syntax(content)
        assert passed == True

    def test_image_syntax_markdown(self):
        """Test markdown image syntax passes."""
        content = "See ![alt](image.png) for details."
        passed, msg = check_image_syntax(content)
        assert passed == True

    def test_get_l1_checks_count(self):
        """Test L1 returns expected number of checks."""
        checks = get_l1_checks()
        assert len(checks) == 4


class TestL2Checks:
    """Tests for L2 content sampling functions."""

    def test_concept_definitions_valid(self):
        """Test concepts with definitions pass."""
        content = """
# Concepts

[[Protein]]: A large molecule
[[DNA]]: Deoxyribonucleic acid
[[RNA]]: Ribonucleic acid

See also [[Protein]] and [[DNA]].
"""
        passed, msg = check_concept_definitions(content)
        assert passed == True

    def test_backlinks_exist_valid(self):
        """Test concepts with backlinks pass."""
        content = """
[[Concept]] is defined here.

See [[Concept]] for more details.
"""
        passed, msg = check_backlinks_exist(content)
        assert passed == True

    def test_get_l2_checks_count(self):
        """Test L2 returns expected number of checks."""
        checks = get_l2_checks()
        assert len(checks) == 2


class TestL3Checks:
    """Tests for L3 completeness check functions."""

    def test_no_orphan_nodes_valid(self):
        """Test content with no orphan nodes passes."""
        content = """
[[Concept A]] is defined here.
See also [[Concept A]] and [[Concept B]].
[[Concept B]] is another concept.
[[Concept A]] appears multiple times.
"""
        passed, msg = check_no_orphan_nodes(content)
        assert passed == True

    def test_no_orphan_nodes_fails(self):
        """Test content with orphan nodes fails."""
        content = """
[[Orphan Concept]] appears only once.
"""
        passed, msg = check_no_orphan_nodes(content)
        assert passed == False

    def test_hierarchy_levels_valid(self):
        """Test valid heading hierarchy passes."""
        content = """
# Title (h1)
## Section (h2)
### Subsection (h3)
## Another Section (h2)
"""
        passed, msg = check_hierarchy_levels(content)
        assert passed == True

    def test_hierarchy_levels_invalid(self):
        """Test invalid heading hierarchy (skip) fails."""
        content = """
# Title (h1)
### Subsection (h3) - skipped h2!
"""
        passed, msg = check_hierarchy_levels(content)
        assert passed == False

    def test_kg_schema_l1(self):
        """Test L1 schema compliance."""
        content = "# Concepts\n[[Concept A]]"
        passed, msg = check_kg_schema_compliance(content, level="L1")
        assert passed == True

    def test_kg_schema_l2_with_relations(self):
        """Test L2 schema with relations passes."""
        content = """
# Concepts
[[Concept A]]: Definition

# Relations
[[Concept A]] -- [[Concept B]]
"""
        passed, msg = check_kg_schema_compliance(content, level="L2")
        assert passed == True

    def test_get_l3_checks_count(self):
        """Test L3 returns expected number of checks."""
        checks = get_l3_checks()
        assert len(checks) == 3


class TestRunVerification:
    """Tests for running verification."""

    def test_run_l1_level(self):
        """Test running L1 verification."""
        content = """---
title: Test
---
# Content
See [[Concept]].
"""
        report = run_level_checks(VerificationLevel.L1, content)
        assert report.level == VerificationLevel.L1
        assert report.passed >= 0
        assert report.failed >= 0

    def test_run_full_verification(self):
        """Test running full verification across all levels."""
        content = """---
title: Test
tags: [test]
---
# Concepts

[[Protein]]: A large molecule
[[DNA]]: Deoxyribonucleic acid

See also [[Protein]] and [[DNA]].
"""
        report = run_full_verification(
            content,
            levels=[VerificationLevel.L1, VerificationLevel.L2, VerificationLevel.L3]
        )
        assert report.l1 is not None
        assert report.l2 is not None
        assert report.l3 is not None


# === Tests for runner.py ===

from skills.analyze.verification.runner import (
    RetryConfig,
    VerificationTask,
    VerificationRunner,
    RetryAction,
    run_full_verification,
)


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_default_config(self):
        """Test default retry config values."""
        config = RetryConfig()
        assert config.l1_max_retries == 1
        assert config.l2_failure_threshold == 0.20
        assert config.l3_max_retries == 1
        assert config.prompt_shuffle == True

    def test_custom_config(self):
        """Test custom retry config."""
        config = RetryConfig(
            l1_max_retries=2,
            l2_failure_threshold=0.30,
            l3_max_retries=2,
        )
        assert config.l1_max_retries == 2
        assert config.l2_failure_threshold == 0.30
        assert config.l3_max_retries == 2


class TestVerificationTask:
    """Tests for VerificationTask dataclass."""

    def test_task_creation(self):
        """Test creating a verification task."""
        task = VerificationTask(
            task_id="test_001",
            content="# Test content",
            levels=[VerificationLevel.L1],
        )
        assert task.task_id == "test_001"
        assert task.content == "# Test content"
        assert task.levels == [VerificationLevel.L1]


class TestVerificationRunner:
    """Tests for VerificationRunner class."""

    def test_runner_initialization(self):
        """Test runner can be initialized."""
        runner = VerificationRunner()
        assert runner.config is not None
        assert runner._log == []

    def test_run_task_pass(self):
        """Test running a task that passes all checks."""
        runner = VerificationRunner()
        task = VerificationTask(
            task_id="pass_001",
            content="""---
title: Test
tags: [test]
---
# Concepts
[[Concept]]: Definition here
See [[Concept]] for more.
""",
            levels=[VerificationLevel.L1],
        )
        result = runner.run_task(task)
        assert result.task_id == "pass_001"
        assert result.retry_count >= 0

    def test_run_task_fail_l1(self):
        """Test running a task that fails L1."""
        runner = VerificationRunner()
        task = VerificationTask(
            task_id="fail_001",
            content="# No frontmatter",
            levels=[VerificationLevel.L1],
        )
        result = runner.run_task(task)
        assert result.task_id == "fail_001"

    def test_run_batch(self):
        """Test running batch of tasks."""
        runner = VerificationRunner()
        tasks = [
            VerificationTask(task_id="batch_001", content="""---
title: Test
---
# Content
[[Concept]] here.
""", levels=[VerificationLevel.L1]),
            VerificationTask(task_id="batch_002", content="# Empty", levels=[VerificationLevel.L1]),
        ]
        results = runner.run_batch(tasks)
        assert len(results) == 2

    def test_get_summary(self):
        """Test getting batch summary."""
        runner = VerificationRunner()
        tasks = [
            VerificationTask(task_id="sum_001", content="""---
title: Test
---
[[Concept]]: def
[[Concept]] ref
""", levels=[VerificationLevel.L1]),
            VerificationTask(task_id="sum_002", content="# Empty", levels=[VerificationLevel.L1]),
        ]
        results = runner.run_batch(tasks)
        summary = runner.get_summary(results)
        assert "total" in summary
        assert "passed" in summary
        assert "failed" in summary


class TestRetryAction:
    """Tests for RetryAction enum."""

    def test_all_actions_defined(self):
        """Test all retry actions are defined."""
        assert RetryAction.RETRY_L1.value == "retry_l1"
        assert RetryAction.RETRY_L2_SAMPLE.value == "retry_l2_sample"
        assert RetryAction.RETRY_L3.value == "retry_l3"
        assert RetryAction.ASK_USER.value == "ask_user"
        assert RetryAction.DELETE_ARTIFACT.value == "delete_artifact"