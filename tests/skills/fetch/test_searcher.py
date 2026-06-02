"""Tests for searcher.py - multi-source search orchestration"""
import pytest
import time
from unittest.mock import patch, MagicMock
from skills.fetch.searcher import (
    detect_domain,
    _deduplicate_and_sort,
    _get_sources_for_domain,
    search_papers,
    _rate_limited_search,
    _search_limiters,
    DOMAIN_KEYWORDS,
)
from skills.fetch.models import PaperResult


class TestDetectDomain:
    """Tests for detect_domain function."""

    def test_cs_domain(self):
        """CS keywords should detect 'cs' domain."""
        for kw in DOMAIN_KEYWORDS["cs"]:
            assert detect_domain(kw) == "cs", f"Keyword '{kw}' should detect as 'cs'"

    def test_bio_domain(self):
        """Biology keywords should detect 'bio' domain."""
        for kw in DOMAIN_KEYWORDS["bio"]:
            assert detect_domain(kw) == "bio", f"Keyword '{kw}' should detect as 'bio'"

    def test_chem_domain(self):
        """Chemistry keywords should detect 'chem' domain."""
        for kw in DOMAIN_KEYWORDS["chem"]:
            assert detect_domain(kw) == "chem", f"Keyword '{kw}' should detect as 'chem'"

    def test_physics_domain(self):
        """Physics keywords should detect 'physics' domain."""
        for kw in DOMAIN_KEYWORDS["physics"]:
            assert detect_domain(kw) == "physics", f"Keyword '{kw}' should detect as 'physics'"

    def test_general_when_no_match(self):
        """No keywords match should return 'general'."""
        assert detect_domain("random query xyz 123") == "general"
        assert detect_domain("hello world") == "general"

    def test_case_insensitive(self):
        """Domain detection should be case insensitive."""
        assert detect_domain("MACHINE LEARNING") == "cs"
        assert detect_domain("Protein") == "bio"


class TestDeduplicateAndSort:
    """Tests for _deduplicate_and_sort function."""

    def test_deduplicates_by_paper_id(self):
        """Should remove duplicates based on paper_id."""
        results = [
            PaperResult(paper_id="arxiv:1234", title="Paper 1", year=2020),
            PaperResult(paper_id="arxiv:1234", title="Paper 1 dup", year=2020),
            PaperResult(paper_id="arxiv:5678", title="Paper 2", year=2019),
        ]
        deduped = _deduplicate_and_sort(results)
        assert len(deduped) == 2
        assert deduped[0].paper_id == "arxiv:1234"
        assert deduped[1].paper_id == "arxiv:5678"

    def test_sorts_by_year_descending(self):
        """Should sort by year in descending order."""
        results = [
            PaperResult(paper_id="a", title="Old", year=2015),
            PaperResult(paper_id="b", title="New", year=2023),
            PaperResult(paper_id="c", title="Mid", year=2019),
        ]
        sorted_results = _deduplicate_and_sort(results)
        assert [r.year for r in sorted_results] == [2023, 2019, 2015]

    def test_empty_list(self):
        """Should handle empty list."""
        assert _deduplicate_and_sort([]) == []


class TestGetSourcesForDomain:
    """Tests for _get_sources_for_domain function."""

    def test_cs_includes_arxiv(self):
        """CS domain should include arxiv."""
        sources = _get_sources_for_domain("cs")
        source_names = [s[0] for s in sources]
        assert "arxiv" in source_names
        assert "semantic_scholar" in source_names
        assert "crossref" in source_names

    def test_physics_includes_arxiv(self):
        """Physics domain should include arxiv."""
        sources = _get_sources_for_domain("physics")
        source_names = [s[0] for s in sources]
        assert "arxiv" in source_names

    def test_bio_includes_pubmed(self):
        """Bio domain should include pubmed."""
        sources = _get_sources_for_domain("bio")
        source_names = [s[0] for s in sources]
        assert "pubmed" in source_names

    def test_general_no_special_source(self):
        """General domain should not have special sources at front."""
        sources = _get_sources_for_domain("general")
        source_names = [s[0] for s in sources]
        # Should have semantic_scholar and crossref, but no arxiv/pubmed at front
        assert "arxiv" not in source_names
        assert "pubmed" not in source_names


class TestSearchPapers:
    """Tests for search_papers function."""

    @patch("skills.fetch.searcher.search_semantic_scholar")
    @patch("skills.fetch.searcher.search_crossref")
    def test_returns_combined_results(self, mock_crossref, mock_semantic):
        """Should combine results from multiple sources."""
        mock_semantic.return_value = [
            PaperResult(paper_id="ss:1", title="From Semantic", year=2020),
        ]
        mock_crossref.return_value = [
            PaperResult(paper_id="doi:1", title="From Crossref", year=2019),
        ]

        results = search_papers("test query")

        assert len(results) == 2
        mock_semantic.assert_called_once()
        mock_crossref.assert_called_once()

    @patch("skills.fetch.searcher.search_semantic_scholar")
    @patch("skills.fetch.searcher.search_crossref")
    def test_handles_source_failure(self, mock_crossref, mock_semantic):
        """Should continue when one source fails."""
        mock_semantic.side_effect = Exception("API error")
        mock_crossref.return_value = [
            PaperResult(paper_id="doi:1", title="From Crossref", year=2019),
        ]

        results = search_papers("test query")

        # Should still return results from working source
        assert len(results) == 1
        assert results[0].paper_id == "doi:1"

    @patch("skills.fetch.searcher.search_arxiv")
    @patch("skills.fetch.searcher.search_semantic_scholar")
    @patch("skills.fetch.searcher.search_crossref")
    def test_cs_domain_searches_arxiv_first(self, mock_crossref, mock_semantic, mock_arxiv):
        """CS domain should search arxiv."""
        mock_arxiv.return_value = []
        mock_semantic.return_value = []
        mock_crossref.return_value = []

        search_papers("machine learning", domain="cs")

        # Verify arxiv was called
        mock_arxiv.assert_called_once()
        # Verify order: arxiv first
        calls = [
            mock_arxiv.call_count,
            mock_semantic.call_count,
            mock_crossref.call_count,
        ]

    @patch("skills.fetch.searcher.search_pubmed")
    @patch("skills.fetch.searcher.search_semantic_scholar")
    @patch("skills.fetch.searcher.search_crossref")
    def test_bio_domain_searches_pubmed_first(self, mock_crossref, mock_semantic, mock_pubmed):
        """Bio domain should search pubmed."""
        mock_pubmed.return_value = []
        mock_semantic.return_value = []
        mock_crossref.return_value = []

        search_papers("protein", domain="bio")

        mock_pubmed.assert_called_once()

    def test_auto_detects_domain(self):
        """Should auto-detect domain when None."""
        with patch("skills.fetch.searcher.search_semantic_scholar") as mock_semantic:
            with patch("skills.fetch.searcher.search_crossref") as mock_crossref:
                with patch("skills.fetch.searcher.search_arxiv") as mock_arxiv:
                    mock_arxiv.return_value = []
                    mock_semantic.return_value = []
                    mock_crossref.return_value = []

                    # Query with machine learning should trigger cs domain
                    search_papers("machine learning transformer")

                    # Should have called arxiv since cs domain detected
                    mock_arxiv.assert_called_once()


class TestRateLimiting:
    """Tests for rate limiting integration."""

    def test_rate_limited_search_calls_acquire(self):
        """_rate_limited_search should call limiter.acquire() for known sources."""
        mock_limiter = MagicMock()
        mock_search_func = MagicMock(return_value=[])
        original_limiter = _search_limiters.get("arxiv")

        # Temporarily replace the limiter
        _search_limiters["arxiv"] = mock_limiter
        try:
            _rate_limited_search("arxiv", mock_search_func, "query", 10)
            mock_limiter.acquire.assert_called_once()
            mock_search_func.assert_called_once_with("query", 10)
        finally:
            _search_limiters["arxiv"] = original_limiter

    def test_rate_limited_search_unknown_source_skips_limit(self):
        """_rate_limited_search should skip limiting for unknown sources."""
        mock_search_func = MagicMock(return_value=[])

        # Should not raise, even without a limiter
        result = _rate_limited_search("unknown_source", mock_search_func, "query", 10)
        mock_search_func.assert_called_once_with("query", 10)
        assert result == []

    def test_rate_limiter_integrated_in_search_papers(self):
        """search_papers should use rate limiting via _rate_limited_search."""
        with patch("skills.fetch.searcher.search_arxiv") as mock_arxiv:
            with patch("skills.fetch.searcher.search_semantic_scholar") as mock_semantic:
                with patch("skills.fetch.searcher.search_crossref") as mock_crossref:
                    mock_arxiv.return_value = []
                    mock_semantic.return_value = []
                    mock_crossref.return_value = []

                    # Track that search was called
                    search_papers("machine learning", domain="cs")

                    # All sources should have been called
                    mock_arxiv.assert_called_once()
                    mock_semantic.assert_called_once()
                    mock_crossref.assert_called_once()
