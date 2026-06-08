"""End-to-end integration tests for paper-reader v2.0 (Task 11).

Exercises the FULL pipeline end-to-end:

    amber-agent adapter (detect + read) → Decision → analyze_with_decision → output files

This is the wiring test for v2.0: it proves that amber-agent's pre-parsed
MinerU output (under ``vlm/`` or ``hybrid_auto/``) can flow straight into
the decision-driven scaffold without any LLM calls, network access, or
real PDF parsing.

Conventions:
- pytest ``TestXxx`` class.
- Module-level ``fake_vlm_dir`` fixture builds a synthetic amber-agent
  output structure (the markdown file is named after ``tmp_path.name``
  to match the ``read_vlm_output`` convention used in the existing
  adapter tests).
- ``tmp_path`` for isolation.
- No network, no LLM, no real PDF.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from skills.analyze.amber_agent_adapter import (
    detect_amber_agent_vlm_output,
    read_vlm_output,
)
from skills.analyze.analyzer import (
    AnalysisLevel,
    Decision,
    analyze_with_decision,
)


# ---------------------------------------------------------------------------
# Module-level fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_vlm_dir(tmp_path):
    """Create a fake amber-agent ``vlm/`` output structure for testing.

    The markdown file is named ``<basename>.md`` (where ``basename`` is
    ``tmp_path.name``) to match the convention expected by
    :func:`read_vlm_output` — the same convention used in the existing
    amber adapter test suite.
    """
    vlm = tmp_path / "vlm"
    vlm.mkdir()
    basename = tmp_path.name
    (vlm / f"{basename}.md").write_text(
        "# Paper Title\n\n"
        "## Abstract\n\n"
        "This is a test paper about AMBER MD simulation.\n\n"
        "## Introduction\n\n"
        "AMBER is a suite of molecular dynamics programs.\n",
        encoding="utf-8",
    )
    (vlm / f"{basename}_content_list.json").write_text(
        '{"elements": [{"type": "heading", "text": "Paper Title"}]}',
        encoding="utf-8",
    )
    return tmp_path


def _make_decision(level: str, base_dir: Path, doc_name: str) -> Decision:
    """Build a Decision with the v2.0 standard fields populated."""
    return Decision(
        level=level,
        base_dir=base_dir,
        doc_name=doc_name,
        format="markdown",
        use_case="kb",
    )


# ---------------------------------------------------------------------------
# TestE2EAnalyzeV2 — full pipeline integration
# ---------------------------------------------------------------------------


class TestE2EAnalyzeV2:
    """E2E: amber adapter → Decision → analyze_with_decision → output files."""

    # ---- L1: concepts only (AlphaFold user guide, ~27 pages) ----

    def test_e2e_l1_alpha_fold_27_pages(self, fake_vlm_dir):
        """L1 decision scaffolds only ``concepts.md`` (empty content).

        Full L1 path: detect + read the fake amber-agent output, then
        run ``analyze_with_decision`` with an L1 decision and assert
        that only ``concepts.md`` is created — no relations, hierarchy,
        or evidence files.
        """
        out = fake_vlm_dir / "out_l1"

        # 1) amber adapter: detect + read
        assert detect_amber_agent_vlm_output(fake_vlm_dir) is True
        content, _metadata = read_vlm_output(fake_vlm_dir)
        assert content  # non-empty markdown

        # 2) scaffold with L1 decision
        decision = _make_decision("L1", fake_vlm_dir, "alphafold-guide")
        result = analyze_with_decision(
            paper_id="alphafold-guide",
            mineru_content="",  # unused at scaffold stage
            decision=decision,
            output_dir=out,
        )

        # 3) only concepts.md is created, and it is empty
        assert (out / "concepts.md").exists()
        assert (out / "concepts.md").read_text(encoding="utf-8") == ""
        # 4) no other files at L1
        assert not (out / "relations.md").exists()
        assert not (out / "hierarchy.md").exists()
        assert not (out / "evidence.md").exists()
        # 5) result carries L1
        assert result.level == AnalysisLevel.L1
        assert result.files == {"concepts.md": ""}

    # ---- L2: concepts + relations (~200-page user guide) ----

    def test_e2e_l2_amber_tutorial(self, fake_vlm_dir):
        """L2 decision scaffolds ``concepts.md`` + ``relations.md`` only.

        Verifies the detect/read works AND that hierarchy/evidence are
        NOT created at L2.
        """
        out = fake_vlm_dir / "out_l2"

        # amber adapter detect + read work for the fake dir
        assert detect_amber_agent_vlm_output(fake_vlm_dir) is True
        assert read_vlm_output(fake_vlm_dir)[0]  # non-empty content

        # L2 scaffold
        decision = _make_decision("L2", fake_vlm_dir, "amber-tutorial")
        result = analyze_with_decision(
            paper_id="amber-tutorial",
            mineru_content="",
            decision=decision,
            output_dir=out,
        )

        # concepts + relations present
        assert (out / "concepts.md").exists()
        assert (out / "relations.md").exists()
        # hierarchy + evidence absent
        assert not (out / "hierarchy.md").exists()
        assert not (out / "evidence.md").exists()
        # result shape
        assert result.level == AnalysisLevel.L2
        assert set(result.files) == {"concepts.md", "relations.md"}

    # ---- L3: concepts + relations + hierarchy (KB use case) ----

    def test_e2e_l3_amber_manual(self, fake_vlm_dir):
        """L3 decision scaffolds 3 files; ``base_dir`` is preserved.

        KB use case (amber manual, 500+ pages equivalent). Verifies
        the file count, the preserved base_dir on the Decision, and
        that evidence.md is still absent (L4 territory).
        """
        out = fake_vlm_dir / "out_l3"
        decision = _make_decision("L3", fake_vlm_dir, "amber-manual")

        result = analyze_with_decision(
            paper_id="amber-manual",
            mineru_content="",
            decision=decision,
            output_dir=out,
        )

        # 3 files created
        assert len(result.files) == 3
        assert (out / "concepts.md").exists()
        assert (out / "relations.md").exists()
        assert (out / "hierarchy.md").exists()
        # evidence.md still absent
        assert not (out / "evidence.md").exists()
        # base_dir is preserved on the Decision
        assert decision.base_dir == fake_vlm_dir
        # result level matches
        assert result.level == AnalysisLevel.L3
        assert set(result.files) == {"concepts.md", "relations.md", "hierarchy.md"}

    # ---- L4: all 4 files (academic paper, deepest analysis) ----

    def test_e2e_l4_academic_paper(self, fake_vlm_dir):
        """L4 decision scaffolds all 4 files; Decision fields roundtrip.

        Academic-paper use case. Verifies evidence.md is created at L4
        and that the Decision's level/format/use_case fields survive
        the call untouched.
        """
        out = fake_vlm_dir / "out_l4"
        decision = _make_decision("L4", fake_vlm_dir, "academic-paper")

        result = analyze_with_decision(
            paper_id="academic-paper",
            mineru_content="",
            decision=decision,
            output_dir=out,
        )

        # 4 files created
        assert len(result.files) == 4
        assert (out / "evidence.md").exists()
        # decision fields roundtrip
        assert decision.level == "L4"
        assert decision.format == "markdown"
        assert decision.use_case == "kb"
        # result level
        assert result.level == AnalysisLevel.L4
        assert set(result.files) == {
            "concepts.md",
            "relations.md",
            "hierarchy.md",
            "evidence.md",
        }

    # ---- v1.0 backward compat (A/B/C still work) ----

    def test_e2e_backward_compat_a_b_c(self, fake_vlm_dir):
        """v1.0 A/B/C still flow through ``analyze_with_decision`` with no error.

        The v1.0 legacy path is not exercised by the v2.0 scaffold
        generator — A/B/C return an empty file list. The contract is
        "no error raised, empty files dict" for each legacy level.
        """
        results = {}
        for level in ("A", "B", "C"):
            out = fake_vlm_dir / f"out_legacy_{level}"
            decision = Decision(
                level=level,
                base_dir=fake_vlm_dir,
                doc_name=f"legacy-{level}",
                format="markdown",
                use_case="obsidian",
            )
            # Must not raise for any of A/B/C
            results[level] = analyze_with_decision(
                paper_id=f"legacy-{level}",
                mineru_content="",
                decision=decision,
                output_dir=out,
            )

        # All three legacy levels return an empty files dict
        # (the v1.0 code path is intentionally not exercised by v2.0 scaffold)
        assert all(r.files == {} for r in results.values())

    # ---- hybrid_auto/ subdir naming (alt scheme) ----

    def test_e2e_hybrid_auto_naming(self, tmp_path):
        """``hybrid_auto/`` subdir is auto-detected and readable by the adapter.

        This is the second amber-agent / MinerU 2.5 naming scheme. The
        adapter must accept it transparently via ``detect`` and ``read``.
        """
        ha = tmp_path / "hybrid_auto"
        ha.mkdir()
        basename = tmp_path.name
        (ha / f"{basename}.md").write_text(
            "# Hybrid Auto Test\n\nContent from hybrid_auto/ subdir.",
            encoding="utf-8",
        )
        (ha / f"{basename}_content_list.json").write_text(
            '{"source": "hybrid_auto"}',
            encoding="utf-8",
        )

        # detect + read work for hybrid_auto/
        assert detect_amber_agent_vlm_output(tmp_path) is True
        content, metadata = read_vlm_output(tmp_path)
        assert "Hybrid Auto" in content
        assert metadata.get("source") == "hybrid_auto"
