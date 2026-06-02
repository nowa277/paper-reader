"""Tests for fetcher with auto-directory creation."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from skills.fetch.fetcher import (
    ensure_dir,
    download_with_space_check,
    fetch_paper,
    search_and_fetch,
    _parse_identifier,
    _get_pdf_url,
)


class TestParseIdentifier:
    """Tests for _parse_identifier()."""

    def test_parses_arxiv_with_prefix(self):
        """arxiv: prefix is parsed correctly."""
        id_type, paper_id = _parse_identifier("arxiv:2301.00001")
        assert id_type == "arxiv"
        assert paper_id == "2301.00001"

    def test_parses_doi_with_prefix(self):
        """doi: prefix is parsed correctly."""
        id_type, paper_id = _parse_identifier("doi:10.1038/nature12373")
        assert id_type == "doi"
        assert paper_id == "10.1038/nature12373"

    def test_parses_pubmed_with_prefix(self):
        """pubmed: prefix is parsed correctly."""
        id_type, paper_id = _parse_identifier("pubmed:12345678")
        assert id_type == "pubmed"
        assert paper_id == "12345678"

    def test_parses_url(self):
        """http URLs are parsed correctly."""
        id_type, paper_id = _parse_identifier("https://arxiv.org/abs/2301.00001")
        assert id_type == "url"
        assert paper_id == "https://arxiv.org/abs/2301.00001"

    def test_parses_bare_arxiv_id(self):
        """Bare arXiv ID (no prefix) is detected as arxiv."""
        id_type, paper_id = _parse_identifier("2301.00001")
        assert id_type == "arxiv"
        assert paper_id == "2301.00001"

    def test_parses_arxiv_id_with_slash(self):
        """arXiv ID with slashes is detected as arxiv."""
        id_type, paper_id = _parse_identifier("2301.00001v2")
        assert id_type == "arxiv"
        assert paper_id == "2301.00001v2"

    def test_parses_long_string_as_arxiv(self):
        """Long strings are detected as arxiv."""
        id_type, paper_id = _parse_identifier("a" * 25)
        assert id_type == "arxiv"

    def test_strips_whitespace(self):
        """Whitespace is stripped from identifier."""
        id_type, paper_id = _parse_identifier("  arxiv:2301.00001  ")
        assert id_type == "arxiv"
        assert paper_id == "2301.00001"

    def test_returns_unknown_for_short_non_prefixed(self):
        """Short non-prefixed strings return unknown."""
        id_type, paper_id = _parse_identifier("test")
        assert id_type == "unknown"


class TestGetPdfUrl:
    """Tests for _get_pdf_url()."""

    def test_returns_arxiv_pdf_url(self):
        """arXiv ID returns arXiv PDF URL."""
        url = _get_pdf_url("arxiv:2301.00001")
        assert url == "https://arxiv.org/pdf/2301.00001.pdf"

    def test_returns_doi_url(self):
        """DOI returns DOI URL."""
        url = _get_pdf_url("doi:10.1038/nature12373")
        assert url == "https://doi.org/10.1038/nature12373"

    def test_returns_pubmed_url(self):
        """PMID returns PubMed URL."""
        url = _get_pdf_url("pubmed:12345678")
        assert url == "https://pubmed.ncbi.nlm.nih.gov/12345678/"

    def test_returns_none_for_unknown(self):
        """Unknown identifier returns None."""
        url = _get_pdf_url("unknown")
        assert url is None


class TestEnsureDir:
    """Tests for ensure_dir()."""

    def test_creates_existing_dir(self, tmp_path):
        """Existing directory is left as-is."""
        existing = tmp_path / "existing"
        existing.mkdir()
        ensure_dir(existing)
        assert existing.is_dir()

    def test_creates_nested_dirs(self, tmp_path):
        """Nested directories are created."""
        nested = tmp_path / "a" / "b" / "c"
        ensure_dir(nested)
        assert nested.is_dir()


class TestDownloadWithSpaceCheck:
    """Tests for download_with_space_check()."""

    def test_downloads_when_space_sufficient(self, tmp_path):
        """Download proceeds when space is sufficient."""
        output = tmp_path / "test.pdf"
        # Mock response with Content-Length
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.headers = {"Content-Length": "1024"}
        # Use PropertyMock so response.raw returns the same mock each time
        mock_raw = MagicMock()
        mock_raw.read = MagicMock(side_effect=[b"test content", b""])
        type(mock_response).raw = PropertyMock(return_value=mock_raw)

        with patch("requests.get", return_value=mock_response):
            result = download_with_space_check("http://example.com/test.pdf", output)
            assert output.exists()
            assert output.read_bytes() == b"test content"


class TestFetchPaper:
    """Tests for fetch_paper()."""

    def test_unknown_identifier_returns_error(self):
        """Unknown identifier returns error."""
        result = fetch_paper("test")
        assert result["success"] is False
        assert "error" in result

    def test_fetch_arxiv_with_jina_reader(self, tmp_path):
        """arXiv paper is fetched via Jina Reader."""
        mock_response = MagicMock()
        mock_response.text = "# Test Paper\nContent"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with patch("skills.fetch.fetcher.download_with_space_check"):
                result = fetch_paper("2301.00001", output_dir=tmp_path)
                assert result["success"] is True
                assert result["content"] == "# Test Paper\nContent"

    def test_fetch_with_prefixes(self, tmp_path):
        """Identifiers with prefixes are handled correctly."""
        mock_response = MagicMock()
        mock_response.text = "# Test Paper\nContent"

        with patch("requests.get", return_value=mock_response):
            with patch("skills.fetch.fetcher.download_with_space_check"):
                # Test arxiv: prefix
                result = fetch_paper("arxiv:2301.00001", output_dir=tmp_path)
                assert result["success"] is True

                # Test doi: prefix
                result = fetch_paper("doi:10.1038/nature12373", output_dir=tmp_path)
                assert result["success"] is True

                # Test pubmed: prefix
                result = fetch_paper("pubmed:12345678", output_dir=tmp_path)
                assert result["success"] is True


class TestSearchAndFetch:
    """Tests for search_and_fetch()."""

    def test_search_and_fetch_returns_results(self):
        """search_and_fetch returns search results."""
        with patch("skills.fetch.searcher.search_papers") as mock_search:
            mock_search.return_value = []
            result = search_and_fetch("machine learning")
            assert result["success"] is True
            assert "results" in result
            assert "count" in result

    def test_search_and_fetch_respects_max_results(self):
        """search_and_fetch passes max_results to search."""
        with patch("skills.fetch.searcher.search_papers") as mock_search:
            mock_search.return_value = []
            search_and_fetch("machine learning", max_results=5)
            mock_search.assert_called_once_with("machine learning", None, 5)

    def test_search_and_fetch_passes_domain(self):
        """search_and_fetch passes domain to search."""
        with patch("skills.fetch.searcher.search_papers") as mock_search:
            mock_search.return_value = []
            search_and_fetch("protein", domain="bio")
            mock_search.assert_called_once_with("protein", "bio", 10)
