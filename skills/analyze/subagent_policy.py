"""Subagent policy module — orchestrating multiple subagents.

Provides decision logic for:
- When to split a task across subagents (should_split, get_subagent_pattern)
- Concurrency configuration by workload type (get_concurrency_config)
- Result aggregation strategy by pattern (get_aggregation_strategy)
- Failure handling and retry policies (create_failure_policy)

References:
- skills/analyze/subagent-decision-tree.md
- skills/analyze/subagent-concurrency-strategy.md
- skills/analyze/subagent-result-aggregation.md
- skills/analyze/subagent-failure-handling.md
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

# Threshold constants from decision tree methodology
PAGES_THRESHOLD_SMALL = 100  # Don't split if < 100 pages
DOCS_THRESHOLD_SMALL = 2     # Don't split if <= 2 docs
PAGES_THRESHOLD_LARGE = 500  # Split if > 500 pages


class SubagentPattern(Enum):
    """Dependency pattern for subagent execution.

    Maps to decision tree patterns from subagent-decision-tree.md.
    """
    SINGLE = "single"           # No splitting - single LLM
    MAP_REDUCE = "map_reduce"   # Independent documents processed in parallel
    PIPELINE = "pipeline"       # Sequential stages (output feeds next)
    TREE_OF_THOUGHT = "tree_of_thought"  # Multiple perspectives on same content
    HIERARCHICAL = "hierarchical"  # Large document split by chapter


class WorkloadType(Enum):
    """Classification of task workload type.

    Determines concurrency configuration from subagent-concurrency-strategy.md.
    """
    IO_BOUND = "io_bound"       # Network, disk, API calls
    COMPUTE_BOUND = "compute_bound"  # CPU-intensive: parsing, NER, algorithms
    MIXED = "mixed"             # Alternates IO and compute (e.g., LLM inference)


class AggregationStrategy(Enum):
    """Strategy for merging subagent outputs.

    Maps to patterns from subagent-result-aggregation.md.
    """
    CONCAT = "concat"                   # Simple concatenation (Pipeline default)
    DEDUPE_ORGANIZE = "dedupe_organize"  # Remove duplicates, group by theme (Map-Reduce default)
    SYNTHESIZE = "synthesize"           # LLM-powered synthesis (Hierarchical/Tree-of-Thought default)


@dataclass
class ConcurrencyConfig:
    """Configuration for subagent concurrency.

    Values based on workload type from subagent-concurrency-strategy.md §2.
    """
    max_concurrent: int
    batch_size: int
    timeout_per_task: int
    retry_max_attempts: int = 3
    retry_backoff_multiplier: float = 2.0


@dataclass
class FailurePolicy:
    """Retry and recovery policy for subagent failures.

    L1/L2/L3 retry counts from subagent-failure-handling.md §3.1.
    """
    l1_retries: int = 1      # L1: Format self-check (subagent self)
    l2_retries: int = 1      # L2: Content sampling (parent agent)
    l3_retries: int = 1      # L3: Completeness check (post-merge)
    l1_timeout: int = 60     # L1 retry timeout in seconds
    l2_timeout: int = 120    # L2 retry timeout in seconds
    l3_timeout: int = 180    # L3 retry timeout in seconds


def should_split(num_docs: int, total_pages: int) -> bool:
    """Determine whether a task should be split across subagents.

    Decision based on decision tree from subagent-decision-tree.md §2.
    Returns False for small tasks (< 100 pages, <= 2 docs).
    Returns True for larger tasks that benefit from parallelization.
    """
    if num_docs <= DOCS_THRESHOLD_SMALL and total_pages < PAGES_THRESHOLD_SMALL:
        return False
    return True


def get_subagent_pattern(
    num_docs: int,
    total_pages: int,
    has_sequential_dependencies: bool = False,
    has_multiple_perspectives: bool = False,
) -> SubagentPattern:
    """Determine the subagent execution pattern based on task characteristics.

    Decision matrix from subagent-decision-tree.md §2 (Decision Matrix).
    """
    # Rule 1: Small task - no splitting
    if num_docs <= DOCS_THRESHOLD_SMALL and total_pages < PAGES_THRESHOLD_SMALL:
        return SubagentPattern.SINGLE

    # Rule 5: Large document (>500 pages) - hierarchical
    if num_docs == 1 and total_pages > PAGES_THRESHOLD_LARGE:
        return SubagentPattern.HIERARCHICAL

    # Rule 4: Multiple perspectives - tree-of-thought
    if has_multiple_perspectives:
        return SubagentPattern.TREE_OF_THOUGHT

    # Rule 3: Sequential dependencies - pipeline
    if has_sequential_dependencies:
        return SubagentPattern.PIPELINE

    # Rule 2: Multiple independent documents - map-reduce
    if num_docs > 1:
        return SubagentPattern.MAP_REDUCE

    # Default: treat as single
    return SubagentPattern.SINGLE


def get_concurrency_config(workload_type: WorkloadType) -> ConcurrencyConfig:
    """Get concurrency configuration based on workload type.

    Values from subagent-concurrency-strategy.md §2 (Concurrency Configuration).
    """
    config_map = {
        WorkloadType.IO_BOUND: ConcurrencyConfig(
            max_concurrent=15,
            batch_size=20,
            timeout_per_task=60,
            retry_max_attempts=3,
            retry_backoff_multiplier=2.0,
        ),
        WorkloadType.COMPUTE_BOUND: ConcurrencyConfig(
            max_concurrent=6,  # Assuming 8 CPU cores, leave 2 for system
            batch_size=6,
            timeout_per_task=300,
            retry_max_attempts=2,
            retry_backoff_multiplier=1.0,
        ),
        WorkloadType.MIXED: ConcurrencyConfig(
            max_concurrent=5,
            batch_size=8,
            timeout_per_task=120,
            retry_max_attempts=5,
            retry_backoff_multiplier=1.5,
        ),
    }
    return config_map[workload_type]


def get_aggregation_strategy(pattern: SubagentPattern) -> AggregationStrategy:
    """Get the appropriate aggregation strategy for a given pattern.

    Default mappings from subagent-result-aggregation.md §2.
    """
    strategy_map = {
        SubagentPattern.SINGLE: AggregationStrategy.CONCAT,
        SubagentPattern.MAP_REDUCE: AggregationStrategy.DEDUPE_ORGANIZE,
        SubagentPattern.PIPELINE: AggregationStrategy.CONCAT,
        SubagentPattern.TREE_OF_THOUGHT: AggregationStrategy.SYNTHESIZE,
        SubagentPattern.HIERARCHICAL: AggregationStrategy.SYNTHESIZE,
    }
    return strategy_map[pattern]


def create_failure_policy(
    l1_retries: int = 1,
    l2_retries: int = 1,
    l3_retries: int = 1,
) -> FailurePolicy:
    """Create a FailurePolicy with specified retry counts.

    Default values from subagent-failure-handling.md §3.1 (Retry Rules Matrix).
    """
    return FailurePolicy(
        l1_retries=l1_retries,
        l2_retries=l2_retries,
        l3_retries=l3_retries,
    )


def classify_workload(is_io_bound: bool, is_compute_bound: bool) -> WorkloadType:
    """Classify the workload type based on task characteristics.

    This is a helper for users to determine which WorkloadType to use.
    """
    if is_io_bound and not is_compute_bound:
        return WorkloadType.IO_BOUND
    elif is_compute_bound and not is_io_bound:
        return WorkloadType.COMPUTE_BOUND
    else:
        return WorkloadType.MIXED