"""Tests for fetcher with auto-directory creation."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from skills.fetch.fetcher import ensure_dir, download_with_space_check, fetch_paper


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
        mock_response.iter_content = MagicMock(return_value=[b"test content"])

        with patch("requests.get", return_value=mock_response):
            result = download_with_space_check("http://example.com/test.pdf", output)
            assert output.exists()


class TestFetchPaper:
    """Tests for fetch_paper()."""

    def test_returns_markdown_for_jina_url(self, tmp_path):
        """Jina URL returns markdown content."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.text = "# Test Paper\nContent"
            mock_get.return_value = mock_response

            result = fetch_paper("https://r.jina.ai/http://example.com/paper")
            assert "markdown" in result or "content" in result