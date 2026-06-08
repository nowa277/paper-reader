"""Tests for analyzer v2.0 decision-driven API (TDD red phase).

These tests target the v2.0 analyzer API which is NOT YET IMPLEMENTED.
They are expected to FAIL with ImportError or AttributeError until
the green phase lands in skills/analyze/analyzer.py.

Style: TestXxx classes, one assertion per test, clear docstrings.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# TestDecision (dataclass)
# ---------------------------------------------------------------------------


class TestDecision:
    """Decision dataclass contract for v2.0 analyzer API."""

    def test_decision_has_required_fields(self):
        """Decision dataclass exposes all v2.0 decision fields."""
        from skills.analyze.analyzer import Decision

        fields = {f.name for f in dataclasses.fields(Decision)}
        expected = {
            "level",
            "base_dir",
            "doc_name",
            "format",
            "use_case",
            "chunks",
            "relations",
            "hierarchy",
            "evidence",
        }
        assert expected.issubset(fields)

    def test_decision_is_dataclass(self):
        """Decision is decorated with @dataclasses.dataclass."""
        from skills.analyze import analyzer

        assert dataclasses.is_dataclass(analyzer.Decision)

    def test_decision_optional_fields_have_defaults(self):
        """Optional Decision fields have default values (caller supplies minimum)."""
        from skills.analyze.analyzer import Decision

        fields = {f.name: f for f in dataclasses.fields(Decision)}
        # level / base_dir / doc_name / format / use_case are the
        # "minimum required" subset — at least these must have defaults
        # so callers can construct with only the core fields populated.
        for name in ("level", "base_dir", "doc_name", "format", "use_case"):
            assert fields[name].default is not dataclasses.MISSING, (
                f"field {name!r} has no default"
            )


# ---------------------------------------------------------------------------
# TestPrepareDecisionFramework
# ---------------------------------------------------------------------------


class TestPrepareDecisionFramework:
    """prepare_decision_framework() — methodology file path resolver."""

    def test_prepare_returns_path_to_methodology(self, tmp_path):
        """prepare_decision_framework() returns a Path to METHODOLOGY.md.

        Returned file must exist and contain the '决策四问' section header
        (the decision framework's first mandatory step per spec §4.1).
        """
        from skills.analyze.analyzer import prepare_decision_framework

        result = prepare_decision_framework()

        # Return type is Path (per the v2.0 spec — not a dict)
        assert isinstance(result, Path)

        # File exists on disk
        assert result.exists(), f"methodology file not found at {result}"

        # Content carries the decision-framework signature phrase
        text = result.read_text(encoding="utf-8")
        assert "决策四问" in text


# ---------------------------------------------------------------------------
# TestAnalyzeWithDecision
# ---------------------------------------------------------------------------


class TestAnalyzeWithDecision:
    """analyze_with_decision() — file scaffold generator (no LLM)."""

    def test_analyze_with_decision_creates_output_dir(self, tmp_path):
        """analyze_with_decision() creates the output_dir on disk."""
        from skills.analyze.analyzer import Decision, analyze_with_decision

        out = tmp_path / "out"
        decision = Decision(
            level="L1",
            base_dir=tmp_path,
            doc_name="paper-x",
            format="markdown",
            use_case="quick",
        )
        analyze_with_decision(
            paper_id="paper-x",
            mineru_content="# Paper X",
            decision=decision,
            output_dir=out,
        )
        assert out.exists()
        assert out.is_dir()

    def test_analyze_with_decision_creates_files_for_level(self, tmp_path):
        """L2 decision produces concepts.md and relations.md on disk."""
        from skills.analyze.analyzer import Decision, analyze_with_decision

        out = tmp_path / "out_l2"
        decision = Decision(
            level="L2",
            base_dir=tmp_path,
            doc_name="paper-y",
            format="markdown",
            use_case="guide",
        )
        analyze_with_decision(
            paper_id="paper-y",
            mineru_content="# Paper Y",
            decision=decision,
            output_dir=out,
        )
        assert (out / "concepts.md").exists()
        assert (out / "relations.md").exists()

    def test_analyze_with_decision_returns_analysis_result(self, tmp_path):
        """Return type is AnalysisResult carrying the decision and files."""
        from skills.analyze.analyzer import (
            AnalysisResult,
            Decision,
            analyze_with_decision,
        )

        out = tmp_path / "out"
        decision = Decision(
            level="L1",
            base_dir=tmp_path,
            doc_name="paper-z",
            format="markdown",
            use_case="quick",
        )
        result = analyze_with_decision(
            paper_id="paper-z",
            mineru_content="# Paper Z",
            decision=decision,
            output_dir=out,
        )
        assert isinstance(result, AnalysisResult)

    def test_analyze_with_decision_does_not_call_llm(self, tmp_path, monkeypatch):
        """No LLM / network call — pure file scaffold. No sockets opened."""
        import socket

        from skills.analyze.analyzer import Decision, analyze_with_decision

        # Track socket creations inside the call
        creations: list[tuple] = []
        original_socket = socket.socket

        def tracking_socket(*args, **kwargs):
            creations.append((args, kwargs))
            return original_socket(*args, **kwargs)

        monkeypatch.setattr(socket, "socket", tracking_socket)

        out = tmp_path / "out"
        decision = Decision(
            level="L1",
            base_dir=tmp_path,
            doc_name="paper-w",
            format="markdown",
            use_case="quick",
        )
        analyze_with_decision(
            paper_id="paper-w",
            mineru_content="# Paper W",
            decision=decision,
            output_dir=out,
        )
        # No new sockets should have been opened — the function is
        # a pure file scaffold and must never touch the network.
        assert creations == []


# ---------------------------------------------------------------------------
# TestGranularityAPI (v2.0 L1–L4 — coexist with v1.0 A/B/C)
# ---------------------------------------------------------------------------


class TestGranularityAPI:
    """v2.0 L1–L4 levels extend the v1.0 AnalysisLevel enum."""

    def test_analysis_level_has_l1_through_l4(self):
        """AnalysisLevel enum exposes L1, L2, L3, L4 in addition to A/B/C."""
        from skills.analyze.analyzer import AnalysisLevel

        members = {m.name for m in AnalysisLevel}
        for name in ("L1", "L2", "L3", "L4"):
            assert name in members, f"AnalysisLevel missing {name!r}"

    def test_get_output_files_l1_returns_concepts_only(self):
        """L1 → only concepts.md."""
        from skills.analyze.analyzer import AnalysisLevel, get_output_files

        files = get_output_files(AnalysisLevel.L1)
        assert "concepts.md" in files

    def test_get_output_files_l2_returns_concepts_relations(self):
        """L2 → concepts.md + relations.md."""
        from skills.analyze.analyzer import AnalysisLevel, get_output_files

        files = get_output_files(AnalysisLevel.L2)
        assert "concepts.md" in files
        assert "relations.md" in files

    def test_get_output_files_l3_adds_hierarchy(self):
        """L3 → concepts + relations + hierarchy."""
        from skills.analyze.analyzer import AnalysisLevel, get_output_files

        files = get_output_files(AnalysisLevel.L3)
        assert "concepts.md" in files
        assert "relations.md" in files
        assert "hierarchy.md" in files

    def test_get_output_files_l4_adds_evidence(self):
        """L4 → concepts + relations + hierarchy + evidence."""
        from skills.analyze.analyzer import AnalysisLevel, get_output_files

        files = get_output_files(AnalysisLevel.L4)
        assert "concepts.md" in files
        assert "relations.md" in files
        assert "hierarchy.md" in files
        assert "evidence.md" in files

    def test_get_output_files_v1_levels_still_work(self):
        """v1.0 A/B/C levels still return the legacy file list (backward compat)."""
        from skills.analyze.analyzer import AnalysisLevel, get_output_files

        # Level A: summary + key_findings
        a_files = get_output_files(AnalysisLevel.A)
        assert "summary.md" in a_files
        assert "key_findings.md" in a_files

        # Level B: includes methodology
        b_files = get_output_files(AnalysisLevel.B)
        assert "methodology.md" in b_files

        # Level C: includes limitations / trends / reproducibility
        c_files = get_output_files(AnalysisLevel.C)
        assert "limitations.md" in c_files
        assert "trends.md" in c_files
        assert "reproducibility.md" in c_files


# ---------------------------------------------------------------------------
# TestAmberAgentAdapterImport
# ---------------------------------------------------------------------------


class TestAmberAgentAdapterImport:
    """amber-agent adapter module is importable and exposes its public API."""

    def test_amber_adapter_module_imports(self):
        """The adapter module imports without error."""
        from skills.analyze import amber_agent_adapter  # noqa: F401

        assert amber_agent_adapter is not None

    def test_detect_amber_agent_vlm_output_import(self):
        """detect_amber_agent_vlm_output is importable from the adapter."""
        from skills.analyze.amber_agent_adapter import detect_amber_agent_vlm_output  # noqa: F401

        assert callable(detect_amber_agent_vlm_output)

    def test_read_vlm_output_import(self):
        """read_vlm_output is importable from the adapter."""
        from skills.analyze.amber_agent_adapter import read_vlm_output  # noqa: F401

        assert callable(read_vlm_output)

    def test_amber_agent_vlm_not_found_is_exception(self):
        """AmberAgentVLMNotFound is a subclass of Exception."""
        from skills.analyze.amber_agent_adapter import AmberAgentVLMNotFound

        assert issubclass(AmberAgentVLMNotFound, Exception)
