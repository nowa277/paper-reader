"""Verification runner with feedback loop and retry logic.

Based on spec §15.4-15.5:
- L1 failure: subagent immediately retries (1 time, with shuffled prompt)
- L2 failure > 20%: trigger that subagent to retry with failure samples
- L3 failure: auto-retry once → still fails then ask user
- Failed subagent artifacts: delete directly, only log in progress.md

Reference:
- skills/analyze/verification/runner.py
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import json
import time

from .levels import (
    VerificationLevel,
    VerificationReport,
    run_level_checks,
    CheckResult,
    LevelReport,
)


class RetryAction(Enum):
    """What action to take on verification failure."""
    RETRY_L1 = "retry_l1"           # L1: subagent retries with shuffled prompt
    RETRY_L2_SAMPLE = "retry_l2_sample"  # L2: retry with failure samples
    RETRY_L3 = "retry_l3"           # L3: auto-retry once
    ASK_USER = "ask_user"           # All retries exhausted
    DELETE_ARTIFACT = "delete_artifact"  # Failed artifact cleanup


@dataclass
class RetryConfig:
    """Retry configuration for each level."""
    l1_max_retries: int = 1
    l2_failure_threshold: float = 0.20  # 20% failure rate triggers retry
    l3_max_retries: int = 1
    prompt_shuffle: bool = True  # Shuffle prompt order on retry


@dataclass
class VerificationTask:
    """A single verification task."""
    task_id: str
    content: str
    file_path: Optional[Path] = None
    levels: list[VerificationLevel] = field(default_factory=lambda: [VerificationLevel.L1])
    metadata: dict = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result of a verification task."""
    task_id: str
    report: VerificationReport
    retry_count: int = 0
    final_action: RetryAction = RetryAction.ASK_USER
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class ProgressLog:
    """Progress log entry for progress.md."""
    task_id: str
    action: RetryAction
    level: Optional[VerificationLevel]
    message: str
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class VerificationRunner:
    """Runs verification with feedback loop and retry logic."""

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        progress_path: Optional[Path] = None,
    ):
        """Initialize runner.

        Args:
            config: Retry configuration. Default: standard config.
            progress_path: Path to progress.md for logging.
        """
        self.config = config or RetryConfig()
        self.progress_path = progress_path
        self._log: list[ProgressLog] = []

    def _log_progress(self, entry: ProgressLog):
        """Log a progress entry."""
        self._log.append(entry)

        # Also write to progress.md if path provided
        if self.progress_path:
            self._write_progress(entry)

    def _write_progress(self, entry: ProgressLog):
        """Append entry to progress.md."""
        line = f"{entry.timestamp} | {entry.task_id} | {entry.action.value} | {entry.level.value if entry.level else 'N/A'} | {entry.message}\n"
        self.progress_path.parent.mkdir(parents=True, exist_ok=True)

        if self.progress_path.exists():
            mode = "a"
        else:
            mode = "w"
            # Write header
            line = f"{'timestamp | task_id | action | level | message'.replace(' | ', ' | ')}\n" + line

        with open(self.progress_path, mode) as f:
            f.write(line)

    def _should_retry_l1(self, l1_report: LevelReport) -> bool:
        """Check if L1 failure should trigger retry."""
        return l1_report.failed > 0

    def _should_retry_l2(self, l2_report: LevelReport) -> bool:
        """Check if L2 failure rate exceeds threshold."""
        total = l2_report.passed + l2_report.failed
        if total == 0:
            return False
        failure_rate = l2_report.failed / total
        return failure_rate > self.config.l2_failure_threshold

    def _should_retry_l3(self, l3_report: LevelReport, current_retries: int) -> bool:
        """Check if L3 failure should trigger auto-retry."""
        if l3_report is None:
            return False
        if l3_report.failed > 0 and current_retries < self.config.l3_max_retries:
            return True
        return False

    def run_task(self, task: VerificationTask) -> TaskResult:
        """Run verification for a single task with retry logic.

        Args:
            task: VerificationTask to run

        Returns:
            TaskResult with final status
        """
        task_id = task.task_id
        retry_count = 0
        last_action = RetryAction.ASK_USER

        # Run initial verification
        report = run_full_verification(task.content, task.levels)

        # Check L1 results
        if report.l1:
            if self._should_retry_l1(report.l1):
                self._log_progress(ProgressLog(
                    task_id=task_id,
                    action=RetryAction.RETRY_L1,
                    level=VerificationLevel.L1,
                    message=f"L1 failed: {report.l1.failed} checks failed",
                ))
                retry_count += 1
                last_action = RetryAction.RETRY_L1

                # L1 retry: re-run with same content (subagent shuffles prompt)
                # In practice, this would trigger the subagent to retry
                report = run_full_verification(task.content, task.levels)

        # Check L2 results
        if report.l2 and last_action != RetryAction.ASK_USER:
            if self._should_retry_l2(report.l2):
                self._log_progress(ProgressLog(
                    task_id=task_id,
                    action=RetryAction.RETRY_L2_SAMPLE,
                    level=VerificationLevel.L2,
                    message=f"L2 failure rate {report.l2.failed / (report.l2.passed + report.l2.failed):.0%} > {self.config.l2_failure_threshold:.0%}",
                ))
                retry_count += 1
                last_action = RetryAction.RETRY_L2_SAMPLE

                # L2 retry: would include failure samples (not implemented here)
                report = run_full_verification(task.content, task.levels)

        # Check L3 results
        if report.l3 and last_action != RetryAction.ASK_USER:
            if self._should_retry_l3(report.l3, retry_count):
                self._log_progress(ProgressLog(
                    task_id=task_id,
                    action=RetryAction.RETRY_L3,
                    level=VerificationLevel.L3,
                    message=f"L3 failed: {report.l3.failed} checks, auto-retry",
                ))
                retry_count += 1
                last_action = RetryAction.RETRY_L3

                # L3 auto-retry
                report = run_full_verification(task.content, task.levels)

                # Check if L3 still fails after retry
                if self._should_retry_l3(report.l3, retry_count):
                    # All retries exhausted
                    self._log_progress(ProgressLog(
                        task_id=task_id,
                        action=RetryAction.ASK_USER,
                        level=VerificationLevel.L3,
                        message="L3 retries exhausted, need user decision",
                    ))
                    last_action = RetryAction.ASK_USER

        # If still failing after all retries, ask user
        if report.total_failed > 0 and last_action in (RetryAction.RETRY_L1, RetryAction.RETRY_L2_SAMPLE, RetryAction.RETRY_L3):
            if not self._should_retry_l3(report.l3, retry_count):
                # L3 exhausted, ask user
                self._log_progress(ProgressLog(
                    task_id=task_id,
                    action=RetryAction.ASK_USER,
                    level=VerificationLevel.L3,
                    message="All retries exhausted, need user decision",
                ))
                last_action = RetryAction.ASK_USER

        return TaskResult(
            task_id=task_id,
            report=report,
            retry_count=retry_count,
            final_action=last_action,
        )

    def run_batch(
        self,
        tasks: list[VerificationTask],
    ) -> list[TaskResult]:
        """Run verification for multiple tasks.

        Args:
            tasks: List of VerificationTask to run

        Returns:
            List of TaskResult in same order as tasks
        """
        results = []

        for task in tasks:
            result = self.run_task(task)
            results.append(result)

            # If task failed and not asking user, mark artifact for deletion
            if not result.report.all_passed and result.final_action == RetryAction.ASK_USER:
                self._log_progress(ProgressLog(
                    task_id=task.task_id,
                    action=RetryAction.DELETE_ARTIFACT,
                    level=None,
                    message="Failed subagent artifact marked for deletion",
                ))

        return results

    def get_summary(self, results: list[TaskResult]) -> dict:
        """Get summary statistics for a batch of results."""
        total = len(results)
        passed = sum(1 for r in results if r.report.all_passed)
        failed = total - passed
        retried = sum(1 for r in results if r.retry_count > 0)
        asked_user = sum(1 for r in results if r.final_action == RetryAction.ASK_USER)

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "retried": retried,
            "asked_user": asked_user,
        }


def run_full_verification(content: str, levels: list[VerificationLevel]) -> VerificationReport:
    """Run verification across specified levels.

    This is a wrapper around levels.run_full_verification for convenience.
    """
    from .levels import run_full_verification as _run
    return _run(content, levels)


# === Progress.md helpers ===

def format_progress_line(
    task_id: str,
    action: RetryAction,
    level: Optional[VerificationLevel],
    message: str,
) -> str:
    """Format a single progress.md line."""
    level_str = level.value if level else "N/A"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    return f"{timestamp} | {task_id} | {action.value} | {level_str} | {message}"