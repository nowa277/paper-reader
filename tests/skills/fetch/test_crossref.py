"""Tests for CrossRef API source."""
import pytest
from unittest.mock import patch, MagicMock

from skills.fetch.sources.crossref import search_crossref


MOCK_CROSSREF_RESPONSE = {
    "message": {
        "items": [
            {
                "DOI": "10.1000/xyz123",
                "title": ["Deep Learning"],
                "author": [
                    {"given": "Ian", "family": "Goodfellow"},
                ],
                "published-print": {"date-parts": [[2016]]},
                "container-title": ["MIT Press"],
                "abstract": "<jats:p>Deep Learning textbook...</jats:p>",
                "URL": "https://doi.org/10.1000/xyz123",
            },
            {
                "DOI": "10.1000/abc789",
                "title": ["Machine Learning: A Probabilistic Perspective"],
                "author": [
                    {"given": "Kevin", "family": "Murphy"},
                ],
                "published-online": {"date-parts": [[2012]]},
                "container-title": ["MIT Press"],
                "abstract": "<jats:p>A comprehensive introduction...</jats:p>",
                "URL": "https://doi.org/10.1000/abc789",
            },
        ]
    }
}


class TestSearchCrossref:
    @patch("skills.fetch.sources.crossref.requests.get")
    def test_search_returns_results(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_CROSSREF_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = search_crossref("deep learning", max_results=10)

        assert len(results) == 2
        assert results[0].paper_id == "doi:10.1000/xyz123"
        assert results[0].title == "Deep Learning"
        assert results[0].authors == ["Ian Goodfellow"]
        assert results[0].year == 2016
        assert results[0].venue == "MIT Press"
        assert results[0].url == "https://doi.org/10.1000/xyz123"
        assert results[0].pdf_url is None
        assert results[0].source == "crossref"

        assert results[1].paper_id == "doi:10.1000/abc789"
        assert results[1].year == 2012

    @patch("skills.fetch.sources.crossref.requests.get")
    def test_search_returns_empty_when_no_results(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"message": {"items": []}}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = search_crossref("xyznonexistent", max_results=5)

        assert results == []

    @patch("skills.fetch.sources.crossref.requests.get")
    def test_search_api_params(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"message": {"items": []}}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        search_crossref("machine learning", max_results=5)

        call_args = mock_get.call_args
        assert "crossref.org" in call_args[0][0]
        assert call_args[1]["params"]["query"] == "machine learning"
        assert call_args[1]["params"]["rows"] == 5
        assert call_args[1]["timeout"] == 30

    @patch("skills.fetch.sources.crossref.requests.get")
    def test_handles_missing_author_fields(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1000/test",
                        "title": ["Test Paper"],
                        "author": [
                            {"given": "", "family": ""},
                        ],
                        "created": {"date-parts": [[2020]]},
                        "URL": "https://doi.org/10.1000/test",
                    }
                ]
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = search_crossref("test", max_results=5)

        assert len(results) == 1
        assert results[0].authors == []

    @patch("skills.fetch.sources.crossref.requests.get")
    def test_handles_missing_dates(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1000/nodate",
                        "title": ["No Date Paper"],
                        "author": [],
                        "URL": "https://doi.org/10.1000/nodate",
                    }
                ]
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = search_crossref("test", max_results=5)

        assert len(results) == 1
        assert results[0].year == 0
