"""Tests for the amber-agent KB adapter.

Covers the two naming schemes amber-agent / MinerU may emit (vlm/ and
hybrid_auto/), the read tuple semantics, and the exception contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skills.analyze.amber_agent_adapter import (
    AmberAgentVLMNotFound,
    detect_amber_agent_vlm_output,
    read_vlm_output,
)


# ---------------------------------------------------------------------------
# detect_amber_agent_vlm_output
# ---------------------------------------------------------------------------


class TestDetectVLM:
    """Behaviour of detect_amber_agent_vlm_output()."""

    def test_detect_vlm_subdir_returns_true(self, tmp_path):
        """Returns True when a vlm/ subdir exists under the given path."""
        (tmp_path / "vlm").mkdir()
        assert detect_amber_agent_vlm_output(tmp_path) is True

    def test_detect_hybrid_auto_subdir_returns_true(self, tmp_path):
        """Returns True when a hybrid_auto/ subdir exists under the given path."""
        (tmp_path / "hybrid_auto").mkdir()
        assert detect_amber_agent_vlm_output(tmp_path) is True

    def test_detect_missing_subdir_returns_false(self, tmp_path):
        """Returns False when neither vlm/ nor hybrid_auto/ exists under the path."""
        # tmp_path exists but has no recognised subdirs.
        assert detect_amber_agent_vlm_output(tmp_path) is False

    def test_detect_nonexistent_path_returns_false(self):
        """Returns False (does not raise) for a path that does not exist."""
        nonexistent = "/tmp/amber-agent-adapter-no-such-path-xyz-12345"
        assert detect_amber_agent_vlm_output(nonexistent) is False

    def test_detect_accepts_string_path(self, tmp_path):
        """A plain string path is accepted and behaves like a Path."""
        (tmp_path / "vlm").mkdir()
        assert detect_amber_agent_vlm_output(str(tmp_path)) is True


# ---------------------------------------------------------------------------
# read_vlm_output
# ---------------------------------------------------------------------------


class TestReadVLM:
    """Behaviour of read_vlm_output()."""

    def test_read_vlm_output_vlm_naming(self, tmp_path):
        """Reads markdown + metadata from a vlm/ subdir using <basename>.md."""
        vlm = tmp_path / "vlm"
        vlm.mkdir()
        basename = tmp_path.name
        md_text = f"# {basename}\n\nHello from {basename}"
        (vlm / f"{basename}.md").write_text(md_text, encoding="utf-8")
        meta_payload = [{"type": "text", "text": "hello", "page_idx": 0}]
        (vlm / f"{basename}_content_list.json").write_text(
            json.dumps(meta_payload), encoding="utf-8"
        )

        content, metadata = read_vlm_output(tmp_path)

        assert content == md_text

    def test_read_vlm_output_hybrid_auto_naming(self, tmp_path):
        """Reads markdown from a hybrid_auto/ subdir the same as vlm/."""
        ha = tmp_path / "hybrid_auto"
        ha.mkdir()
        basename = tmp_path.name
        md_text = f"# {basename} (hybrid_auto)"
        (ha / f"{basename}.md").write_text(md_text, encoding="utf-8")

        content, metadata = read_vlm_output(tmp_path)

        assert content == md_text

    def test_read_vlm_output_no_metadata_returns_empty_dict(self, tmp_path):
        """Missing content_list.json yields an empty dict, not a raise."""
        vlm = tmp_path / "vlm"
        vlm.mkdir()
        basename = tmp_path.name
        (vlm / f"{basename}.md").write_text("# no metadata", encoding="utf-8")

        content, metadata = read_vlm_output(tmp_path)

        assert metadata == {}

    def test_read_vlm_output_parses_content_list_json(self, tmp_path):
        """Parsed content_list.json is exposed in the metadata dict."""
        vlm = tmp_path / "vlm"
        vlm.mkdir()
        basename = tmp_path.name
        (vlm / f"{basename}.md").write_text("# x", encoding="utf-8")
        (vlm / f"{basename}_content_list.json").write_text(
            json.dumps({"source": "amber-agent KB", "n": 3}), encoding="utf-8"
        )

        content, metadata = read_vlm_output(tmp_path)

        assert metadata.get("source") == "amber-agent KB"

    def test_read_vlm_output_raises_not_found_for_missing_subdir(self, tmp_path):
        """Raises AmberAgentVLMNotFound when no vlm/ or hybrid_auto/ subdir."""
        with pytest.raises(AmberAgentVLMNotFound):
            read_vlm_output(tmp_path)

    def test_read_vlm_output_raises_file_not_found_for_missing_md(self, tmp_path):
        """Raises FileNotFoundError when <basename>.md is absent from the subdir."""
        vlm = tmp_path / "vlm"
        vlm.mkdir()
        # Note: do NOT create <basename>.md
        with pytest.raises(FileNotFoundError):
            read_vlm_output(tmp_path)

    def test_read_vlm_output_accepts_string_path(self, tmp_path):
        """A plain string path is accepted and behaves like a Path."""
        vlm = tmp_path / "vlm"
        vlm.mkdir()
        basename = tmp_path.name
        md_text = "# string-path test"
        (vlm / f"{basename}.md").write_text(md_text, encoding="utf-8")

        content, _ = read_vlm_output(str(tmp_path))

        assert content == md_text


# ---------------------------------------------------------------------------
# Exception contract
# ---------------------------------------------------------------------------


class TestExceptions:
    """Exception class contract."""

    def test_amber_agent_vlm_not_found_is_exception(self):
        """AmberAgentVLMNotFound is a subclass of Exception."""
        assert issubclass(AmberAgentVLMNotFound, Exception)

    def test_amber_agent_vlm_not_found_can_be_raised_with_message(self):
        """The exception can be raised and caught with a custom message."""
        msg = "no amber-agent output here"
        with pytest.raises(AmberAgentVLMNotFound, match=msg):
            raise AmberAgentVLMNotFound(msg)
