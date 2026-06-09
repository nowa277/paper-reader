"""End-to-end integration module for amber-agent paper analysis pipeline.

This module orchestrates the complete pipeline:
    PDF → VLM (MinerU) → subagent analysis → verification → output

It handles:
- Token-aware trigger decisions for parallel vs sequential processing
- Multi-level verification (L1/L2/L3) with retry logic
- Image embedding with multiple strategies
- Configuration-driven pipeline stages

Supported PDF configurations (from Plan 3):
- amber26: 1112 pages, 2-3M tokens, L3/L4 target
- alphafold: 27 pages, ~60K tokens, L1/L2 target
- colabfold: 50 pages, ~100K tokens, L2 target
- amber_tutorials: 150 pages, ~300K tokens, L2/L3 target
- go_best_practices: 80 pages, ~200K tokens, L2 target
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import yaml
import time


# Import existing modules
from .amber_agent_adapter import (
    detect_amber_agent_vlm_output,
    read_vlm_output,
    AmberAgentVLMNotFound,
)
from .analyzer import (
    AnalysisLevel,
    Decision,
    analyze_with_decision,
    get_output_files,
)
from .verification.levels import (
    VerificationLevel,
    VerificationReport,
    run_full_verification,
    CheckResult,
)
from .verification.runner import (
    VerificationRunner,
    VerificationTask,
    RetryConfig,
    RetryAction,
)
from .verification.token_estimator import quick_estimate
from .image_embedder import (
    ImageEmbedder,
    ImageEmbedConfig,
    EmbeddingStrategy,
)


class PipelineStage(Enum):
    """Pipeline execution stages."""
    DETECT = "detect"              # Detect VLM output
    PARSE = "parse"                # Read VLM content + metadata
    DECIDE = "decide"              # Make chunking/granularity decision
    ANALYZE = "analyze"            # Run subagent analysis
    VERIFY = "verify"              # Run L1/L2/L3 verification
    EMBED_IMAGES = "embed_images"  # Embed images with strategy
    OUTPUT = "output"              # Write final output files


class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some stages completed with warnings


@dataclass
class PDFConfig:
    """Configuration for a specific PDF/document."""
    name: str
    pages: int
    estimated_tokens: int
    doc_type: str  # "manual", "user_guide", "paper", "tutorial"
    target_level: str  # "L1", "L2", "L3", "L4"
    trigger_mode: str  # "SINGLE", "HIERARCHICAL", "MAP_REDUCE"
    l1_enabled: bool = True
    l2_enabled: bool = False
    l3_enabled: bool = False
    l2_sample_rate: float = 0.10
    l3_auto_retry: int = 1

    @classmethod
    def from_yaml(cls, path: Path) -> "PDFConfig":
        """Load PDF config from YAML file."""
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        doc_info = data.get("document_info", {})
        trigger = data.get("trigger_configuration", {})
        levels = data.get("verification_levels", {})

        return cls(
            name=doc_info.get("name", ""),
            pages=doc_info.get("pages", 0),
            estimated_tokens=trigger.get("token_count", 0),
            doc_type=doc_info.get("type", "user_guide"),
            target_level=doc_info.get("target_level", "L2"),
            trigger_mode=trigger.get("trigger_mode", "SINGLE"),
            l1_enabled=levels.get("L1", {}).get("enabled", True),
            l2_enabled=levels.get("L2", {}).get("enabled", False),
            l3_enabled=levels.get("L3", {}).get("enabled", False),
            l2_sample_rate=0.05 if "AlphaFold" in doc_info.get("name", "") else 0.10,
            l3_auto_retry=1,
        )


@dataclass
class StageResult:
    """Result of a single pipeline stage."""
    stage: PipelineStage
    status: PipelineStatus
    duration_seconds: float = 0.0
    message: str = ""
    data: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class PipelineResult:
    """Result of the full E2E pipeline."""
    paper_id: str
    config: PDFConfig
    status: PipelineStatus
    stages: list[StageResult] = field(default_factory=list)
    output_dir: Optional[Path] = None
    output_files: dict[str, str] = field(default_factory=dict)
    verification_report: Optional[VerificationReport] = None
    total_duration_seconds: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.status == PipelineStatus.COMPLETED


@dataclass
class E2EConfig:
    """E2E pipeline configuration."""
    default_output_dir: Path = field(default_factory=lambda: Path("output"))
    enable_verification: bool = True
    enable_image_embedding: bool = True
    default_verification_levels: list[VerificationLevel] = field(
        default_factory=lambda: [VerificationLevel.L1, VerificationLevel.L2, VerificationLevel.L3]
    )
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    image_config: ImageEmbedConfig = field(default_factory=ImageEmbedConfig)
    checkpoint_enabled: bool = True
    progress_log_path: Optional[Path] = None


class E2EIntegration:
    """End-to-end integration orchestrator for amber-agent pipeline."""

    def __init__(self, config: Optional[E2EConfig] = None):
        """Initialize the E2E integration.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or E2EConfig()
        self._verification_runner: Optional[VerificationRunner] = None
        self._image_embedder: Optional[ImageEmbedder] = None

    @property
    def verification_runner(self) -> VerificationRunner:
        """Lazy-load verification runner."""
        if self._verification_runner is None:
            self._verification_runner = VerificationRunner(
                config=self.config.retry_config,
                progress_path=self.config.progress_log_path,
            )
        return self._verification_runner

    @property
    def image_embedder(self) -> ImageEmbedder:
        """Lazy-load image embedder."""
        if self._image_embedder is None:
            self._image_embedder = ImageEmbedder(config=self.config.image_config)
        return self._image_embedder

    def run_pipeline(
        self,
        paper_id: str,
        vlm_path: str | Path,
        decision: Decision,
        output_dir: Optional[Path] = None,
        config: Optional[PDFConfig] = None,
    ) -> PipelineResult:
        """Run the complete E2E pipeline.

        Args:
            paper_id: Unique identifier for the paper/document.
            vlm_path: Path to amber-agent VLM output directory.
            decision: Decision object from the agent.
            output_dir: Optional output directory. Uses config default if not provided.
            config: Optional PDF-specific configuration.

        Returns:
            PipelineResult with execution details.
        """
        start_time = time.time()
        stages_results: list[StageResult] = []

        output_dir = output_dir or self.config.default_output_dir / paper_id

        # Default config based on decision level
        if config is None:
            config = self._infer_config(decision)

        # Stage 1: Detect VLM output
        stage_result = self._run_detect_stage(vlm_path)
        stages_results.append(stage_result)

        if stage_result.status == PipelineStatus.FAILED:
            return self._create_failed_result(
                paper_id, config, stages_results, start_time, stage_result.error
            )

        # Stage 2: Parse VLM content
        stage_result = self._run_parse_stage(vlm_path)
        stages_results.append(stage_result)

        if stage_result.status == PipelineStatus.FAILED:
            return self._create_failed_result(
                paper_id, config, stages_results, start_time, stage_result.error
            )

        vlm_content = stage_result.data.get("content", "")
        vlm_metadata = stage_result.data.get("metadata", {})

        # Stage 3: Decide (already done by agent, just validate)
        stage_result = self._run_decide_stage(decision, config)
        stages_results.append(stage_result)

        # Stage 4: Analyze (scaffold generation)
        stage_result = self._run_analyze_stage(paper_id, vlm_content, decision, output_dir)
        stages_results.append(stage_result)

        if stage_result.status == PipelineStatus.FAILED:
            return self._create_failed_result(
                paper_id, config, stages_results, start_time, stage_result.error
            )

        output_files = stage_result.data.get("files", {})

        # Stage 5: Verify (if enabled)
        if self.config.enable_verification:
            stage_result = self._run_verify_stage(
                vlm_content, config, decision.level
            )
            stages_results.append(stage_result)

            verification_report = stage_result.data.get("report")

            # Handle verification failures with retry
            if verification_report and not verification_report.all_passed:
                # Run verification tasks with retry logic
                retry_result = self._handle_verification_failure(
                    paper_id, vlm_content, config, decision.level
                )
                stages_results.extend(retry_result.stages)
                if retry_result.verification_report:
                    verification_report = retry_result.verification_report
        else:
            verification_report = None

        # Stage 6: Embed images (if enabled)
        if self.config.enable_image_embedding:
            stage_result = self._run_embed_images_stage(
                vlm_content, vlm_metadata, output_dir, paper_id
            )
            stages_results.append(stage_result)

        # Stage 7: Output (finalize)
        stage_result = self._run_output_stage(output_dir, output_files)
        stages_results.append(stage_result)

        # Determine final status
        failed_stages = [s for s in stages_results if s.status == PipelineStatus.FAILED]
        if failed_stages:
            final_status = PipelineStatus.FAILED
        elif any(s for s in stages_results if s.status == PipelineStatus.PARTIAL):
            final_status = PipelineStatus.PARTIAL
        else:
            final_status = PipelineStatus.COMPLETED

        return PipelineResult(
            paper_id=paper_id,
            config=config,
            status=final_status,
            stages=stages_results,
            output_dir=output_dir,
            output_files=output_files,
            verification_report=verification_report,
            total_duration_seconds=time.time() - start_time,
        )

    def _run_detect_stage(self, vlm_path: str | Path) -> StageResult:
        """Run detection stage."""
        start = time.time()
        try:
            detected = detect_amber_agent_vlm_output(vlm_path)
            return StageResult(
                stage=PipelineStage.DETECT,
                status=PipelineStatus.COMPLETED if detected else PipelineStatus.FAILED,
                duration_seconds=time.time() - start,
                message=f"VLM output {'found' if detected else 'not found'} at {vlm_path}",
                data={"detected": detected},
            )
        except Exception as e:
            return StageResult(
                stage=PipelineStage.DETECT,
                status=PipelineStatus.FAILED,
                duration_seconds=time.time() - start,
                error=str(e),
            )

    def _run_parse_stage(self, vlm_path: str | Path) -> StageResult:
        """Run parsing stage."""
        start = time.time()
        try:
            content, metadata = read_vlm_output(vlm_path)
            return StageResult(
                stage=PipelineStage.PARSE,
                status=PipelineStatus.COMPLETED,
                duration_seconds=time.time() - start,
                message=f"Parsed {len(content)} chars, {len(metadata)} metadata keys",
                data={"content": content, "metadata": metadata},
            )
        except AmberAgentVLMNotFound as e:
            return StageResult(
                stage=PipelineStage.PARSE,
                status=PipelineStatus.FAILED,
                duration_seconds=time.time() - start,
                error=str(e),
            )
        except Exception as e:
            return StageResult(
                stage=PipelineStage.PARSE,
                status=PipelineStatus.FAILED,
                duration_seconds=time.time() - start,
                error=str(e),
            )

    def _run_decide_stage(self, decision: Decision, config: PDFConfig) -> StageResult:
        """Run decision validation stage."""
        start = time.time()

        # Validate decision consistency with config
        issues = []

        if decision.level not in ("L1", "L2", "L3", "L4", "A", "B", "C"):
            issues.append(f"Invalid level: {decision.level}")

        # Check token-based trigger alignment
        if config.trigger_mode == "HIERARCHICAL" and config.estimated_tokens > 500_000:
            if decision.level not in ("L3", "L4"):
                issues.append(f"Large doc ({config.estimated_tokens} tokens) should use L3/L4")

        if issues:
            return StageResult(
                stage=PipelineStage.DECIDE,
                status=PipelineStatus.PARTIAL,
                duration_seconds=time.time() - start,
                message=f"Decision has warnings: {', '.join(issues)}",
                data={"decision": decision.__dict__, "config": config.__dict__},
            )

        return StageResult(
            stage=PipelineStage.DECIDE,
            status=PipelineStatus.COMPLETED,
            duration_seconds=time.time() - start,
            message=f"Decision validated for level {decision.level}",
            data={"decision": decision.__dict__},
        )

    def _run_analyze_stage(
        self,
        paper_id: str,
        mineru_content: str,
        decision: Decision,
        output_dir: Path,
    ) -> StageResult:
        """Run analysis/scaffold stage."""
        start = time.time()
        try:
            result = analyze_with_decision(
                paper_id=paper_id,
                mineru_content=mineru_content,
                decision=decision,
                output_dir=output_dir,
            )

            return StageResult(
                stage=PipelineStage.ANALYZE,
                status=PipelineStatus.COMPLETED,
                duration_seconds=time.time() - start,
                message=f"Generated {len(result.files)} output files",
                data={"files": result.files, "level": result.level.value},
            )
        except Exception as e:
            return StageResult(
                stage=PipelineStage.ANALYZE,
                status=PipelineStatus.FAILED,
                duration_seconds=time.time() - start,
                error=str(e),
            )

    def _run_verify_stage(
        self,
        content: str,
        config: PDFConfig,
        decision_level: str,
    ) -> StageResult:
        """Run verification stage."""
        start = time.time()

        # Determine which levels to run based on config
        levels_to_run = []
        if config.l1_enabled:
            levels_to_run.append(VerificationLevel.L1)
        if config.l2_enabled:
            levels_to_run.append(VerificationLevel.L2)
        if config.l3_enabled:
            levels_to_run.append(VerificationLevel.L3)

        # Default to L1 if nothing configured
        if not levels_to_run:
            levels_to_run = [VerificationLevel.L1]

        try:
            report = run_full_verification(content, levels_to_run)

            return StageResult(
                stage=PipelineStage.VERIFY,
                status=PipelineStatus.COMPLETED if report.all_passed else PipelineStatus.PARTIAL,
                duration_seconds=time.time() - start,
                message=f"Verification: {report.total_passed} passed, {report.total_failed} failed",
                data={"report": report},
            )
        except Exception as e:
            return StageResult(
                stage=PipelineStage.VERIFY,
                status=PipelineStatus.PARTIAL,
                duration_seconds=time.time() - start,
                message=f"Verification error (continuing): {str(e)}",
                data={"report": None},
            )

    def _handle_verification_failure(
        self,
        paper_id: str,
        content: str,
        config: PDFConfig,
        level: str,
    ) -> PipelineResult:
        """Handle verification failure with retry logic."""
        start = time.time()
        stages: list[StageResult] = []

        # Create verification task
        levels = []
        if config.l1_enabled:
            levels.append(VerificationLevel.L1)
        if config.l2_enabled:
            levels.append(VerificationLevel.L2)
        if config.l3_enabled:
            levels.append(VerificationLevel.L3)

        task = VerificationTask(
            task_id=f"{paper_id}_verify",
            content=content,
            levels=levels,
        )

        # Run with retry
        result = self.verification_runner.run_task(task)

        stages.append(StageResult(
            stage=PipelineStage.VERIFY,
            status=PipelineStatus.COMPLETED if result.report.all_passed else PipelineStatus.PARTIAL,
            duration_seconds=time.time() - start,
            message=f"Retry {result.retry_count}x, final action: {result.final_action.value}",
            data={"report": result.report, "retry_count": result.retry_count},
        ))

        return PipelineResult(
            paper_id=paper_id,
            config=config,
            status=PipelineStatus.COMPLETED if result.report.all_passed else PipelineStatus.PARTIAL,
            stages=stages,
            verification_report=result.report,
            total_duration_seconds=time.time() - start,
        )

    def _run_embed_images_stage(
        self,
        vlm_content: str,
        vlm_metadata: dict,
        output_dir: Path,
        paper_id: str,
    ) -> StageResult:
        """Run image embedding stage."""
        start = time.time()

        try:
            # Detect images from VLM output
            images = self.image_embedder.detect_images_from_vlm_output(vlm_content)

            # Also check metadata for images
            if vlm_metadata:
                metadata_images = self.image_embedder.detect_images_from_content_list(vlm_metadata)
                images.extend(metadata_images)

            if not images:
                return StageResult(
                    stage=PipelineStage.EMBED_IMAGES,
                    status=PipelineStatus.COMPLETED,
                    duration_seconds=time.time() - start,
                    message="No images to embed",
                    data={"images_found": 0},
                )

            # Embed images
            embedded = self.image_embedder.embed_images_batch(
                images, output_dir / "images", paper_id
            )

            return StageResult(
                stage=PipelineStage.EMBED_IMAGES,
                status=PipelineStatus.COMPLETED,
                duration_seconds=time.time() - start,
                message=f"Embedded {len(embedded)} images",
                data={
                    "images_found": len(images),
                    "images_embedded": len(embedded),
                },
            )
        except Exception as e:
            return StageResult(
                stage=PipelineStage.EMBED_IMAGES,
                status=PipelineStatus.PARTIAL,
                duration_seconds=time.time() - start,
                message=f"Image embedding error (continuing): {str(e)}",
                data={"images_found": 0},
            )

    def _run_output_stage(
        self,
        output_dir: Path,
        output_files: dict[str, str],
    ) -> StageResult:
        """Run output stage."""
        start = time.time()

        # Write final output files
        for filename, content in output_files.items():
            path = output_dir / filename
            path.write_text(content, encoding="utf-8")

        return StageResult(
            stage=PipelineStage.OUTPUT,
            status=PipelineStatus.COMPLETED,
            duration_seconds=time.time() - start,
            message=f"Wrote {len(output_files)} files to {output_dir}",
            data={"files_written": list(output_files.keys())},
        )

    def _infer_config(self, decision: Decision) -> PDFConfig:
        """Infer PDF config from decision."""
        # Estimate tokens based on content size (rough approximation)
        # In real use, this would come from token_estimator
        estimated_tokens = 100_000  # Default assumption

        return PDFConfig(
            name=decision.doc_name or "unknown",
            pages=0,
            estimated_tokens=estimated_tokens,
            doc_type="unknown",
            target_level=decision.level,
            trigger_mode="SINGLE" if estimated_tokens < 500_000 else "HIERARCHICAL",
        )

    def _create_failed_result(
        self,
        paper_id: str,
        config: PDFConfig,
        stages: list[StageResult],
        start_time: float,
        error: Optional[str],
    ) -> PipelineResult:
        """Create a failed pipeline result."""
        return PipelineResult(
            paper_id=paper_id,
            config=config,
            status=PipelineStatus.FAILED,
            stages=stages,
            total_duration_seconds=time.time() - start_time,
            error=error,
        )

    def load_pdf_config(self, config_path: Path) -> PDFConfig:
        """Load PDF configuration from YAML file.

        Args:
            config_path: Path to the YAML config file.

        Returns:
            PDFConfig instance.
        """
        return PDFConfig.from_yaml(config_path)

    def run_for_config(
        self,
        paper_id: str,
        vlm_path: str | Path,
        config_path: Path,
        decision: Decision,
        output_dir: Optional[Path] = None,
    ) -> PipelineResult:
        """Run pipeline with a specific PDF configuration file.

        Args:
            paper_id: Unique identifier for the paper.
            vlm_path: Path to amber-agent VLM output.
            config_path: Path to PDF config YAML file.
            decision: Decision object from the agent.
            output_dir: Optional output directory.

        Returns:
            PipelineResult with execution details.
        """
        config = self.load_pdf_config(config_path)
        return self.run_pipeline(paper_id, vlm_path, decision, output_dir, config)


# === Convenience functions ===

def create_e2e_integration(
    output_dir: Optional[Path] = None,
    enable_verification: bool = True,
    enable_image_embedding: bool = True,
) -> E2EIntegration:
    """Create an E2EIntegration with common defaults.

    Args:
        output_dir: Default output directory.
        enable_verification: Whether to run L1/L2/L3 verification.
        enable_image_embedding: Whether to embed images.

    Returns:
        Configured E2EIntegration instance.
    """
    config = E2EConfig(
        default_output_dir=output_dir or Path("output"),
        enable_verification=enable_verification,
        enable_image_embedding=enable_image_embedding,
    )
    return E2EIntegration(config)


def run_full_pipeline(
    paper_id: str,
    vlm_path: str | Path,
    level: str = "L2",
    output_dir: Optional[Path] = None,
    config_path: Optional[Path] = None,
) -> PipelineResult:
    """Run the full E2E pipeline with minimal configuration.

    This is a convenience function for common use cases.

    Args:
        paper_id: Unique identifier for the paper.
        vlm_path: Path to amber-agent VLM output.
        level: Analysis level (L1, L2, L3, L4).
        output_dir: Optional output directory.
        config_path: Optional path to PDF config YAML.

    Returns:
        PipelineResult with execution details.
    """
    e2e = create_e2e_integration(output_dir=output_dir)

    # Create basic decision
    decision = Decision(
        level=level,
        base_dir=output_dir or Path("output"),
        doc_name=paper_id,
        format="markdown",
        use_case="kb",
    )

    # Load config if provided
    config = None
    if config_path and config_path.exists():
        config = e2e.load_pdf_config(config_path)

    return e2e.run_pipeline(paper_id, vlm_path, decision, output_dir, config)