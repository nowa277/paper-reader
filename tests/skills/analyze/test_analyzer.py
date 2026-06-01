"""Tests for analyzer module."""

import pytest
from pathlib import Path
from skills.analyze.analyzer import (
    AnalysisLevel,
    AnalysisResult,
    get_analysis_prompt,
    get_output_files,
    parse_mineru_output,
    create_output_dir,
    write_analysis_files,
)

def test_analysis_level_enum():
    assert AnalysisLevel.A.value == "A"
    assert AnalysisLevel.B.value == "B"
    assert AnalysisLevel.C.value == "C"

def test_get_output_files_level_a():
    files = get_output_files(AnalysisLevel.A)
    assert "summary.md" in files
    assert "key_findings.md" in files
    assert len(files) == 2

def test_get_output_files_level_b():
    files = get_output_files(AnalysisLevel.B)
    assert "summary.md" in files
    assert "methodology.md" in files
    assert "figures.md" in files
    assert "related_work.md" in files
    assert len(files) == 5

def test_get_output_files_level_c():
    files = get_output_files(AnalysisLevel.C)
    assert "limitations.md" in files
    assert "trends.md" in files
    assert "reproducibility.md" in files
    assert len(files) == 8

def test_get_analysis_prompt_level_a():
    prompt = get_analysis_prompt(AnalysisLevel.A)
    assert "summary.md" in prompt
    assert "key_findings.md" in prompt

def test_get_analysis_prompt_level_b():
    prompt = get_analysis_prompt(AnalysisLevel.B)
    assert "methodology.md" in prompt
    assert "figures.md" in prompt

def test_get_analysis_prompt_level_c():
    prompt = get_analysis_prompt(AnalysisLevel.C)
    assert "limitations.md" in prompt
    assert "trends.md" in prompt
    assert "reproducibility.md" in prompt

def test_parse_mineru_output_valid():
    content = "# Title\n\n## Abstract\n\nThis is the abstract content."
    result = parse_mineru_output(content)
    assert result["title"] == "Title"
    assert "This is the abstract content" in result["abstract"]

def test_parse_mineru_output_empty():
    result = parse_mineru_output("")
    assert result["title"] == ""

def test_analysis_result_dataclass():
    result = AnalysisResult(
        paper_id="test:123",
        level=AnalysisLevel.A,
        output_dir=Path("/tmp/test"),
        files={"summary.md": "# Summary\n"},
    )
    assert result.paper_id == "test:123"
    assert result.level == AnalysisLevel.A
    assert "summary.md" in result.files

def test_create_output_dir(tmp_path, monkeypatch):
    # Temporarily override DEFAULT_OUTPUT_DIR
    from skills.analyze import analyzer
    monkeypatch.setattr(analyzer, "DEFAULT_OUTPUT_DIR", tmp_path)
    out_dir = create_output_dir("test:123")
    assert out_dir.exists()
    assert "test_123" in str(out_dir)

def test_write_analysis_files(tmp_path):
    files = {
        "summary.md": "# Summary\nTest content",
        "key_findings.md": "# Key Findings\nFinding 1",
    }
    write_analysis_files(tmp_path, files)
    assert (tmp_path / "summary.md").exists()
    assert (tmp_path / "key_findings.md").exists()
    assert (tmp_path / "summary.md").read_text() == "# Summary\nTest content"
