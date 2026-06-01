"""Tests for arXiv API source."""
import pytest
from unittest.mock import patch, MagicMock
from xml.etree import ElementTree as ET

from skills.fetch.sources.arxiv import (
    extract_arxiv_id,
    _parse_atom_entry,
    search_arxiv,
)


# --- extract_arxiv_id tests ---

class TestExtractArxivId:
    def test_url_with_version(self):
        url = "http://arxiv.org/abs/2301.00001v2"
        assert extract_arxiv_id(url) == "2301.00001v2"

    def test_url_without_version(self):
        url = "http://arxiv.org/abs/2301.00001"
        assert extract_arxiv_id(url) == "2301.00001"

    def test_https_url(self):
        url = "https://arxiv.org/abs/2301.00001v3"
        assert extract_arxiv_id(url) == "2301.00001v3"

    def test_url_not_matching(self):
        assert extract_arxiv_id("https://example.com/paper/123") is None


# --- _parse_atom_entry tests ---

ATOM_ENTRY = """<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom">
  <id>http://arxiv.org/abs/2301.00001v1</id>
  <title>Test Paper Title</title>
  <author><name>John Doe</name></author>
  <author><name>Jane Smith</name></author>
  <published>2023-01-15T00:00:00Z</published>
  <summary>This is a test abstract for the paper. It contains details about the methodology and results.</summary>
  <link title="pdf" href="https://arxiv.org/pdf/2301.00001v1"/>
</entry>
"""


class TestParseAtomEntry:
    def test_parses_valid_entry(self):
        root = ET.fromstring(ATOM_ENTRY)
        entry = root  # root is the entry element
        paper = _parse_atom_entry(entry)

        assert paper is not None
        assert paper.paper_id == "arxiv:2301.00001v1"
        assert paper.title == "Test Paper Title"
        assert paper.authors == ["John Doe", "Jane Smith"]
        assert paper.year == 2023
        assert paper.abstract == "This is a test abstract for the paper. It contains details about the methodology and results."
        assert paper.url == "https://arxiv.org/abs/2301.00001v1"
        assert paper.pdf_url == "https://arxiv.org/pdf/2301.00001v1"
        assert paper.source == "arxiv"

    def test_returns_none_on_missing_field(self):
        entry_xml = """<entry><title>No ID here</title></entry>"""
        root = ET.fromstring(entry_xml)
        assert _parse_atom_entry(root) is None


# --- search_arxiv integration with mocked HTTP ---

MOCK_ATOM_FEED = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2301.00001v1</id>
    <title>Attention Is All You Need</title>
    <author><name>Ashish Vaswani</name></author>
    <author><name>Noam Shazeer</name></author>
    <published>2017-06-12T00:00:00Z</published>
    <summary> We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.</summary>
    <link title="pdf" href="https://arxiv.org/pdf/2301.00001v1"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2301.00002v1</id>
    <title>BERT: Pre-training of Deep Bidirectional Transformers</title>
    <author><name>Jacob Devlin</name></author>
    <published>2018-10-11T00:00:00Z</published>
    <summary>We introduce a new language representation model called BERT.</summary>
    <link title="pdf" href="https://arxiv.org/pdf/2301.00002v1"/>
  </entry>
</feed>
"""


class TestSearchArxiv:
    @patch("skills.fetch.sources.arxiv.requests.get")
    def test_search_arxiv_returns_results(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = MOCK_ATOM_FEED.encode("utf-8")
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        results = search_arxiv("transformer", max_results=10)

        assert len(results) == 2
        assert results[0].title == "Attention Is All You Need"
        assert results[0].authors == ["Ashish Vaswani", "Noam Shazeer"]
        assert results[0].year == 2017
        assert results[1].title == "BERT: Pre-training of Deep Bidirectional Transformers"
        assert results[1].year == 2018

    @patch("skills.fetch.sources.arxiv.requests.get")
    def test_search_arxiv_calls_api_with_correct_params(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>"""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        search_arxiv("deep learning", max_results=5)

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "http://export.arxiv.org/api/query"
        assert call_args[1]["params"]["search_query"] == "all:deep learning"
        assert call_args[1]["params"]["max_results"] == 5
        assert call_args[1]["timeout"] == 30
