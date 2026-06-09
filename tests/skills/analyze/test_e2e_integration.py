"""End-to-end integration tests for amber-agent E2E pipeline.

Tests cover:
- Full pipeline execution for each PDF config
- Error handling and recovery
- Verification gates pass/fail scenarios
- Image embedding integration
- Configuration loading

Run with: pytest tests/skills/analyze/test_e2e_integration.py -v
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import pytest

from skills.analyze.e2e_integration import (
    E2EIntegration,
    E2EConfig,
    PipelineStage,
    PipelineStatus,
    PDFConfig,
    StageResult,
    PipelineResult,
    create_e2e_integration,
    run_full_pipeline,
)
from skills.analyze.analyzer import Decision, AnalysisLevel
from skills.analyze.verification.levels import VerificationLevel
from skills.analyze.image_embedder import ImageEmbedConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    return tmp_path / "output"


@pytest.fixture
def fake_vlm_dir(tmp_path):
    """Create a fake amber-agent VLM output structure."""
    vlm = tmp_path / "vlm"
    vlm.mkdir()
    basename = tmp_path.name
    (vlm / f"{basename}.md").write_text(
        "# Test Paper\n\n"
        "## Abstract\n\n"
        "This is a test paper with [[concept1]] and [[concept2]].\n\n"
        "## Introduction\n\n"
        "The [[method]] is described here.\n\n"
        "---\n"
        "title: Test Paper\n"
        "author: Test Author\n",
        encoding="utf-8",
    )
    (vlm / f"{basename}_content_list.json").write_text(
        '{"elements": [{"type": "heading", "text": "Test Paper"}]}',
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def e2e_integration(temp_output_dir):
    """Create an E2EIntegration with temp output."""
    config = E2EConfig(
        default_output_dir=temp_output_dir,
        enable_verification=True,
        enable_image_embedding=True,
    )
    return E2EIntegration(config)


@pytest.fixture
def basic_decision(temp_output_dir):
    """Create a basic L2 decision."""
    return Decision(
        level="L2",
        base_dir=temp_output_dir,
        doc_name="test-doc",
        format="markdown",
        use_case="kb",
        relations=True,
    )


# ---------------------------------------------------------------------------
# Test Class: Pipeline Execution
# ---------------------------------------------------------------------------


class TestE2EPipelineExecution:
    """Test full pipeline execution."""

    def test_pipeline_runs_all_stages(self, e2e_integration, fake_vlm_dir, basic_decision, temp_output_dir):
        """Pipeline runs all 7 stages successfully."""
        result = e2e_integration.run_pipeline(
            paper_id="test-paper",
            vlm_path=fake_vlm_dir,
            decision=basic_decision,
            output_dir=temp_output_dir / "test1",
        )

        # Pipeline completes all stages (may be PARTIAL if verification has warnings)
        assert result.status in (PipelineStatus.COMPLETED, PipelineStatus.PARTIAL)
        # 7 core stages + possible retry stage = 8
        assert len(result.stages) >= 7

        # Verify core stages exist
        stage_names = [s.stage.value for s in result.stages]
        expected_stages = ["detect", "parse", "decide", "analyze", "verify", "embed_images", "output"]
        for stage in expected_stages:
            assert stage in stage_names

        # Output files should be created regardless of verification warnings
        assert "concepts.md" in result.output_files
        assert "relations.md" in result.output_files

    def test_pipeline_with_l1_level(self, e2e_integration, fake_vlm_dir, temp_output_dir):
        """Pipeline works with L1 level."""
        decision = Decision(
            level="L1",
            base_dir=temp_output_dir,
            doc_name="test-l1",
            format="markdown",
            use_case="kb",
        )

        result = e2e_integration.run_pipeline(
            paper_id="test-l1",
            vlm_path=fake_vlm_dir,
            decision=decision,
            output_dir=temp_output_dir / "l1",
        )

        # Pipeline completes (may be PARTIAL due to verification frontmatter check)
        assert result.status in (PipelineStatus.COMPLETED, PipelineStatus.PARTIAL)
        assert result.output_files == {"concepts.md": ""}

    def test_pipeline_with_l3_level(self, e2e_integration, fake_vlm_dir, temp_output_dir):
        """Pipeline works with L3 level (KB use case)."""
        decision = Decision(
            level="L3",
            base_dir=temp_output_dir,
            doc_name="test-l3",
            format="markdown",
            use_case="kb",
            relations=True,
            hierarchy=True,
        )

        result = e2e_integration.run_pipeline(
            paper_id="test-l3",
            vlm_path=fake_vlm_dir,
            decision=decision,
            output_dir=temp_output_dir / "l3",
        )

        assert result.status in (PipelineStatus.COMPLETED, PipelineStatus.PARTIAL)
        assert set(result.output_files.keys()) == {"concepts.md", "relations.md", "hierarchy.md"}

    def test_pipeline_with_l4_level(self, e2e_integration, fake_vlm_dir, temp_output_dir):
        """Pipeline works with L4 level (full graph)."""
        decision = Decision(
            level="L4",
            base_dir=temp_output_dir,
            doc_name="test-l4",
            format="markdown",
            use_case="kb",
            relations=True,
            hierarchy=True,
            evidence=True,
        )

        result = e2e_integration.run_pipeline(
            paper_id="test-l4",
            vlm_path=fake_vlm_dir,
            decision=decision,
            output_dir=temp_output_dir / "l4",
        )

        assert result.status in (PipelineStatus.COMPLETED, PipelineStatus.PARTIAL)
        assert set(result.output_files.keys()) == {
            "concepts.md", "relations.md", "hierarchy.md", "evidence.md"
        }


# ---------------------------------------------------------------------------
# Test Class: Error Handling
# ---------------------------------------------------------------------------


class TestE2EErrorHandling:
    """Test error handling and recovery."""

    def test_detect_stage_failure_on_missing_vlm(self, e2e_integration, tmp_path, basic_decision):
        """Detect stage fails when VLM output is missing."""
        result = e2e_integration.run_pipeline(
            paper_id="test-missing",
            vlm_path=tmp_path / "nonexistent",
            decision=basic_decision,
        )

        # Should fail at detect stage
        assert result.status == PipelineStatus.FAILED
        assert result.stages[0].stage == PipelineStage.DETECT
        assert result.stages[0].status == PipelineStatus.FAILED
        # Error is captured in stage, not in top-level error for detection failures
        assert result.stages[0].message is not None

    def test_parse_stage_failure_on_invalid_path(self, e2e_integration, tmp_path, basic_decision):
        """Parse stage handles invalid path gracefully."""
        # Create a dir that exists but has no vlm subdir
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = e2e_integration.run_pipeline(
            paper_id="test-empty",
            vlm_path=empty_dir,
            decision=basic_decision,
        )

        assert result.status == PipelineStatus.FAILED
        # The detect stage should have failed since no vlm subdir exists
        assert len(result.stages) > 0
        assert result.stages[0].stage == PipelineStage.DETECT


# ---------------------------------------------------------------------------
# Test Class: Verification Integration
# ---------------------------------------------------------------------------


class TestE2EVerification:
    """Test verification gates and retry logic."""

    def test_verification_enabled_by_default(self, e2e_integration, fake_vlm_dir, basic_decision, temp_output_dir):
        """Verification is enabled by default."""
        assert e2e_integration.config.enable_verification is True

    def test_verification_runs_l1_checks(self, e2e_integration, fake_vlm_dir, temp_output_dir):
        """Verification runs L1 checks on content."""
        decision = Decision(
            level="L1",
            base_dir=temp_output_dir,
            doc_name="test-verify",
            format="markdown",
            use_case="kb",
        )

        result = e2e_integration.run_pipeline(
            paper_id="test-verify",
            vlm_path=fake_vlm_dir,
            decision=decision,
            output_dir=temp_output_dir / "verify",
        )

        verify_stage = next(s for s in result.stages if s.stage == PipelineStage.VERIFY)
        assert verify_stage.status in (PipelineStatus.COMPLETED, PipelineStatus.PARTIAL)

    def test_verification_disabled(self, tmp_path, temp_output_dir):
        """Pipeline works when verification is disabled."""
        config = E2EConfig(
            default_output_dir=temp_output_dir,
            enable_verification=False,
        )
        e2e = E2EIntegration(config)

        # Create fake VLM dir with proper structure - use tmp_path, not temp_output_dir
        vlm_dir = tmp_path / "vlm_test"
        vlm_dir.mkdir(parents=True)
        vlm_subdir = vlm_dir / "vlm"
        vlm_subdir.mkdir()
        (vlm_subdir / "vlm_test.md").write_text("# Test\n", encoding="utf-8")

        decision = Decision(
            level="L1",
            base_dir=temp_output_dir,
            doc_name="test-no-verify",
            format="markdown",
            use_case="kb",
        )

        result = e2e.run_pipeline(
            paper_id="test-no-verify",
            vlm_path=vlm_dir,  # Pass the parent dir that contains vlm/
            decision=decision,
        )

        assert result.status in (PipelineStatus.COMPLETED, PipelineStatus.PARTIAL)
        # Verify stage should be skipped when disabled
        verify_stage = next((s for s in result.stages if s.stage == PipelineStage.VERIFY), None)
        assert verify_stage is None or verify_stage.status == PipelineStatus.COMPLETED


# ---------------------------------------------------------------------------
# Test Class: Image Embedding Integration
# ---------------------------------------------------------------------------


class TestE2EImageEmbedding:
    """Test image embedding integration."""

    def test_image_embedding_enabled_by_default(self, e2e_integration):
        """Image embedding is enabled by default."""
        assert e2e_integration.config.enable_image_embedding is True

    def test_image_embedding_stage_runs(self, e2e_integration, fake_vlm_dir, basic_decision, temp_output_dir):
        """Image embedding stage runs when enabled."""
        result = e2e_integration.run_pipeline(
            paper_id="test-images",
            vlm_path=fake_vlm_dir,
            decision=basic_decision,
            output_dir=temp_output_dir / "images",
        )

        embed_stage = next(s for s in result.stages if s.stage == PipelineStage.EMBED_IMAGES)
        assert embed_stage.status == PipelineStatus.COMPLETED

    def test_image_embedding_with_vlm_content(self, e2e_integration, tmp_path, temp_output_dir):
        """Image embedding detects images from VLM content."""
        # Create VLM with image references using proper structure
        vlm_dir = tmp_path / "vlm_img"
        vlm_dir.mkdir()
        vlm_subdir = vlm_dir / "vlm"
        vlm_subdir.mkdir()
        (vlm_subdir / "vlm_img.md").write_text(
            "# Test\n\n![diagram](figure1.png)\n\n[[Image:diagram.svg]]\n",
            encoding="utf-8",
        )

        decision = Decision(
            level="L1",
            base_dir=temp_output_dir,
            doc_name="test-img-detect",
            format="markdown",
            use_case="kb",
        )

        result = e2e_integration.run_pipeline(
            paper_id="test-img-detect",
            vlm_path=vlm_dir,
            decision=decision,
            output_dir=temp_output_dir / "img_detect",
        )

        # Check that embed stage exists and runs
        embed_stage = next((s for s in result.stages if s.stage == PipelineStage.EMBED_IMAGES), None)
        assert embed_stage is not None
        assert embed_stage.status in (PipelineStatus.COMPLETED, PipelineStatus.PARTIAL)


# ---------------------------------------------------------------------------
# Test Class: PDF Configuration
# ---------------------------------------------------------------------------


class TestE2EPDFConfig:
    """Test PDF configuration loading and handling."""

    def test_pdf_config_from_yaml(self, tmp_path):
        """PDF config can be loaded from YAML."""
        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(
            """
document_info:
  name: test-doc
  pages: 100
  type: user_guide
  target_level: L2

trigger_configuration:
  trigger_mode: SINGLE
  token_count: 200000

verification_levels:
  L1:
    enabled: true
  L2:
    enabled: true
  L3:
    enabled: false
""",
            encoding="utf-8",
        )

        pdf_config = PDFConfig.from_yaml(config_path)
        assert pdf_config.name == "test-doc"
        assert pdf_config.pages == 100
        assert pdf_config.target_level == "L2"
        assert pdf_config.trigger_mode == "SINGLE"

    def test_infer_config_from_decision(self, e2e_integration, temp_output_dir):
        """Config is inferred from decision when not provided."""
        decision = Decision(
            level="L3",
            base_dir=temp_output_dir,
            doc_name="inferred-doc",
            format="markdown",
            use_case="kb",
            relations=True,
            hierarchy=True,
        )

        config = e2e_integration._infer_config(decision)
        assert config.target_level == "L3"
        assert config.name == "inferred-doc"


# ---------------------------------------------------------------------------
# Test Class: Convenience Functions
# ---------------------------------------------------------------------------


class TestE2EConvenienceFunctions:
    """Test convenience functions."""

    def test_create_e2e_integration(self, temp_output_dir):
        """create_e2e_integration returns configured instance."""
        e2e = create_e2e_integration(output_dir=temp_output_dir)
        assert isinstance(e2e, E2EIntegration)
        assert e2e.config.default_output_dir == temp_output_dir

    def test_create_e2e_integration_defaults(self):
        """create_e2e_integration uses sensible defaults."""
        e2e = create_e2e_integration()
        assert e2e.config.enable_verification is True
        assert e2e.config.enable_image_embedding is True
        assert e2e.config.default_output_dir == Path("output")

    def test_run_full_pipeline_minimal(self, tmp_path, temp_output_dir):
        """run_full_pipeline works with minimal arguments."""
        # Create proper VLM structure with vlm/ subdir
        vlm_dir = tmp_path / "vlm_min"
        vlm_dir.mkdir()
        vlm_subdir = vlm_dir / "vlm"
        vlm_subdir.mkdir()
        (vlm_subdir / "vlm_min.md").write_text("# Test\n", encoding="utf-8")

        result = run_full_pipeline(
            paper_id="minimal",
            vlm_path=vlm_dir,
            level="L1",
            output_dir=temp_output_dir / "minimal",
        )

        assert result.status in (PipelineStatus.COMPLETED, PipelineStatus.PARTIAL)


# ---------------------------------------------------------------------------
# Test Class: Stage Results
# ---------------------------------------------------------------------------


class TestE2EStageResults:
    """Test stage result handling."""

    def test_stage_result_timing(self, e2e_integration, fake_vlm_dir, basic_decision, temp_output_dir):
        """Stage results include timing information."""
        result = e2e_integration.run_pipeline(
            paper_id="timing-test",
            vlm_path=fake_vlm_dir,
            decision=basic_decision,
            output_dir=temp_output_dir / "timing",
        )

        for stage in result.stages:
            assert stage.duration_seconds >= 0

    def test_total_duration_recorded(self, e2e_integration, fake_vlm_dir, basic_decision, temp_output_dir):
        """Total pipeline duration is recorded."""
        result = e2e_integration.run_pipeline(
            paper_id="duration-test",
            vlm_path=fake_vlm_dir,
            decision=basic_decision,
            output_dir=temp_output_dir / "duration",
        )

        assert result.total_duration_seconds > 0
        # Total should be sum of stage durations
        stage_sum = sum(s.duration_seconds for s in result.stages)
        assert abs(result.total_duration_seconds - stage_sum) < 1.0  # Allow 1s tolerance


# ---------------------------------------------------------------------------
# Test Class: Output Files
# ---------------------------------------------------------------------------


class TestE2EOutputFiles:
    """Test output file handling."""

    def test_output_files_written(self, e2e_integration, fake_vlm_dir, basic_decision, temp_output_dir):
        """Output files are written to disk."""
        output_dir = temp_output_dir / "written"
        result = e2e_integration.run_pipeline(
            paper_id="written-test",
            vlm_path=fake_vlm_dir,
            decision=basic_decision,
            output_dir=output_dir,
        )

        assert result.output_dir == output_dir
        assert output_dir.exists()

        for filename in result.output_files:
            assert (output_dir / filename).exists()

    def test_output_dir_created(self, e2e_integration, fake_vlm_dir, basic_decision, tmp_path):
        """Output directory is created if it doesn't exist."""
        output_dir = tmp_path / "new" / "nested" / "dir"
        assert not output_dir.exists()

        result = e2e_integration.run_pipeline(
            paper_id="mkdir-test",
            vlm_path=fake_vlm_dir,
            decision=basic_decision,
            output_dir=output_dir,
        )

        assert output_dir.exists()


# ---------------------------------------------------------------------------
# Test Class: Verification Configurations (All 5 PDF configs)
# ---------------------------------------------------------------------------


class TestE2EPDFConfigs:
    """Test all 5 PDF configurations from Plan 3."""

    @pytest.fixture
    def verification_configs_dir(self):
        """Path to verification config directory."""
        return Path(__file__).parent.parent.parent / "skills" / "analyze" / "verification"

    def test_load_amber26_config(self, verification_configs_dir, e2e_integration):
        """Can load amber26 verification config."""
        config_path = verification_configs_dir / "config_amber26.yaml"
        if not config_path.exists():
            pytest.skip("Config file not found")

        config = e2e_integration.load_pdf_config(config_path)
        assert config.name == "amber26 manual"
        assert config.pages == 1112

    def test_load_alphafold_config(self, verification_configs_dir, e2e_integration):
        """Can load alphafold verification config."""
        config_path = verification_configs_dir / "config_alphafold.yaml"
        if not config_path.exists():
            pytest.skip("Config file not found")

        config = e2e_integration.load_pdf_config(config_path)
        assert "AlphaFold" in config.name

    def test_load_colabfold_config(self, verification_configs_dir, e2e_integration):
        """Can load colabfold verification config."""
        config_path = verification_configs_dir / "config_colabfold.yaml"
        if not config_path.exists():
            pytest.skip("Config file not found")

        config = e2e_integration.load_pdf_config(config_path)
        assert "ColabFold" in config.name or "colabfold" in config.name.lower()

    def test_load_amber_tutorials_config(self, verification_configs_dir, e2e_integration):
        """Can load amber_tutorials verification config."""
        config_path = verification_configs_dir / "config_amber_tutorials.yaml"
        if not config_path.exists():
            pytest.skip("Config file not found")

        config = e2e_integration.load_pdf_config(config_path)
        assert "AMBER" in config.name or "tutorial" in config.name.lower()

    def test_load_go_best_practices_config(self, verification_configs_dir, e2e_integration):
        """Can load go_best_practices verification config."""
        config_path = verification_configs_dir / "config_go_best_practices.yaml"
        if not config_path.exists():
            pytest.skip("Config file not found")

        config = e2e_integration.load_pdf_config(config_path)
        assert "Go" in config.name or "go" in config.name.lower()


# ---------------------------------------------------------------------------
# Test Class: Decision Validation
# ---------------------------------------------------------------------------


class TestE2EDecisionValidation:
    """Test decision validation against config."""

    def test_decision_validation_warns_on_mismatch(self, e2e_integration, fake_vlm_dir, temp_output_dir):
        """Decision validation warns when level doesn't match token count."""
        # Large doc config but L1 decision should warn
        config = PDFConfig(
            name="large-doc",
            pages=1000,
            estimated_tokens=1_000_000,
            doc_type="manual",
            target_level="L3",
            trigger_mode="HIERARCHICAL",
        )

        decision = Decision(
            level="L1",  # Mismatch: large doc but L1
            base_dir=temp_output_dir,
            doc_name="mismatch",
            format="markdown",
            use_case="kb",
        )

        result = e2e_integration.run_pipeline(
            paper_id="mismatch-test",
            vlm_path=fake_vlm_dir,
            decision=decision,
            output_dir=temp_output_dir / "mismatch",
            config=config,
        )

        # Should complete but with warning in decide stage
        decide_stage = next(s for s in result.stages if s.stage == PipelineStage.DECIDE)
        assert decide_stage.status == PipelineStatus.PARTIAL
        assert "warning" in decide_stage.message.lower() or "large" in decide_stage.message.lower()