import pytest
from skills.fetch.models import PaperResult


def test_paper_result_display_name():
    result = PaperResult(
        paper_id="arxiv:2301.00001",
        title="Attention Is All You Need",
        authors=["Vaswani", "Shazeer", "Parmar"],
        year=2017,
        venue="NeurIPS"
    )
    assert "Attention Is All You Need" in result.display_name
    assert "Vaswani" in result.display_name
    assert "2017" in result.display_name


def test_to_selection_item():
    result = PaperResult(paper_id="x", title="Test", authors=["A"], year=2024, venue="X")
    # Single author: no "et al." since 3 or fewer authors are shown in full
    assert result.to_selection_item(1) == "1. Test — A, 2024 (X)"


def test_display_name_single_author():
    result = PaperResult(
        paper_id="x",
        title="Single Author Paper",
        authors=["Smith"],
        year=2020,
        venue="ICML"
    )
    assert "Single Author Paper" in result.display_name
    assert "Smith" in result.display_name
    assert "et al." not in result.display_name


def test_display_name_three_authors():
    result = PaperResult(
        paper_id="x",
        title="Three Authors Paper",
        authors=["A", "B", "C"],
        year=2021,
        venue="ICLR"
    )
    assert "et al." not in result.display_name
    assert "A, B, C" in result.display_name


def test_display_name_more_than_three_authors():
    result = PaperResult(
        paper_id="x",
        title="Many Authors Paper",
        authors=["A", "B", "C", "D", "E"],
        year=2022,
        venue="NeurIPS"
    )
    assert "et al." in result.display_name
    assert "A, B, C et al." in result.display_name


def test_display_name_no_authors():
    result = PaperResult(
        paper_id="x",
        title="No Authors Paper",
        authors=[],
        year=2023,
        venue="AAAI"
    )
    # With no authors, it should still work (empty join gives "")
    assert "No Authors Paper" in result.display_name


def test_default_fields():
    result = PaperResult(paper_id="test:1", title="Test Paper")
    assert result.paper_id == "test:1"
    assert result.title == "Test Paper"
    assert result.authors == []
    assert result.year == 0
    assert result.venue == ""
    assert result.abstract == ""
    assert result.url == ""
    assert result.pdf_url is None
    assert result.domain == "general"
    assert result.source == ""


def test_selection_item_different_indices():
    result = PaperResult(paper_id="x", title="Test", authors=["A"], year=2024, venue="X")
    # Single author: no "et al." since 3 or fewer authors are shown in full
    assert result.to_selection_item(1) == "1. Test — A, 2024 (X)"
    assert result.to_selection_item(5) == "5. Test — A, 2024 (X)"
    assert result.to_selection_item(99) == "99. Test — A, 2024 (X)"
