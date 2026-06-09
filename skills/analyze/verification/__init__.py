"""Verification module for subagent output quality control.

Based on spec §15: Verification, Audit & Acceptance Criteria

Submodules:
- token_estimator: Token counting for trigger mode decision
- levels: L1/L2/L3 verification checks
- runner: Feedback loop and retry logic
"""

from .token_estimator import (
    TokenEstimator,
    TriggerMode,
    TOKEN_THRESHOLD_SINGLE,
    TOKEN_THRESHOLD_MAP_REDUCE,
    TOKEN_THRESHOLD_HIERARCHICAL,
    quick_estimate,
    should_split_subagent,
    estimate_and_decide,
    get_default_estimator,
)

from .levels import (
    VerificationLevel,
    CheckResult,
    Check,
    VerificationResult,
    LevelReport,
    VerificationReport,
    get_l1_checks,
    get_l2_checks,
    get_l3_checks,
    get_all_checks,
    run_level_checks,
    run_full_verification,
)

from .runner import (
    RetryConfig,
    RetryAction,
    VerificationTask,
    TaskResult,
    ProgressLog,
    VerificationRunner,
    format_progress_line,
    run_full_verification as run_verification,
)

__all__ = [
    # token_estimator
    "TokenEstimator",
    "TriggerMode",
    "TOKEN_THRESHOLD_SINGLE",
    "TOKEN_THRESHOLD_MAP_REDUCE",
    "TOKEN_THRESHOLD_HIERARCHICAL",
    "quick_estimate",
    "should_split_subagent",
    "estimate_and_decide",
    "get_default_estimator",
    # levels
    "VerificationLevel",
    "CheckResult",
    "Check",
    "VerificationResult",
    "LevelReport",
    "VerificationReport",
    "get_l1_checks",
    "get_l2_checks",
    "get_l3_checks",
    "get_all_checks",
    "run_level_checks",
    "run_full_verification",
    # runner
    "RetryConfig",
    "RetryAction",
    "VerificationTask",
    "TaskResult",
    "ProgressLog",
    "VerificationRunner",
    "format_progress_line",
    "run_verification",
]