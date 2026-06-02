"""Tests for Semantic Scholar API source."""
import pytest
from unittest.mock import patch, MagicMock

from skills.fetch.sources.semantic_scholar import search_semantic_scholar


MOCK_S2_RESPONSE = {
    "data": [
        {
            "paperId": "abc123",
            "title": "Attention Is All You Need",
            "authors": [
                {"name": "Ashish Vaswani"},
                {"name": "Noam Shazeer"},
            ],
            "year": 2017,
            "venue": "NeurIPS",
            "abstract": "We propose a new simple network architecture...",
            "url": "https://www.semanticscholar.org/paper/abc123",
            "openAccessPdf": {"url": "https://arxiv.org/pdf/1706.03762"},
        },
        {
            "paperId": "def456",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "authors": [
                {"name": "Jacob Devlin"},
            ],
            "year": 2018,
            "venue": "NAACL",
            "abstract": "We present a new language representation model...",
            "url": "https://www.semanticscholar.org/paper/def456",
            "openAccessPdf": None,
        },
    ]
}


class TestSearchSemanticScholar:
    @patch("skills.fetch.sources.semantic_scholar.requests.get")
    def test_search_returns_results(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_S2_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = search_semantic_scholar("transformer", max_results=10)

        assert len(results) == 2
        assert results[0].paper_id == "ss:abc123"
        assert results[0].title == "Attention Is All You Need"
        assert results[0].authors == ["Ashish Vaswani", "Noam Shazeer"]
        assert results[0].year == 2017
        assert results[0].venue == "NeurIPS"
        assert results[0].url == "https://www.semanticscholar.org/paper/abc123"
        assert results[0].pdf_url == "https://arxiv.org/pdf/1706.03762"
        assert results[0].source == "semantic_scholar"

        assert results[1].paper_id == "ss:def456"
        assert results[1].pdf_url is None

    @patch("skills.fetch.sources.semantic_scholar.requests.get")
    def test_search_returns_empty_when_no_results(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = search_semantic_scholar("xyznonexistent", max_results=5)

        assert results == []

    @patch("skills.fetch.sources.semantic_scholar.requests.get")
    def test_search_api_params(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        search_semantic_scholar("machine learning", max_results=5)

        call_args = mock_get.call_args
        assert "semanticscholar.org" in call_args[0][0]
        assert call_args[1]["params"]["query"] == "machine learning"
        assert call_args[1]["params"]["limit"] == 5
        assert call_args[1]["timeout"] == 30

    @patch("skills.fetch.sources.semantic_scholar.requests.get")
    def test_skips_items_without_paper_id(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {"paperId": None, "title": "Bad Item"},
                {"paperId": "valid123", "title": "Good Item"},
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = search_semantic_scholar("test", max_results=10)

        assert len(results) == 1
        assert results[0].paper_id == "ss:valid123"
