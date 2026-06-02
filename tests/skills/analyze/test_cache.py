"""Tests for paper cache."""

import json
import tempfile
from pathlib import Path
from skills.analyze.cache import PaperCache


class TestPaperCacheInit:
    """Tests for PaperCache initialization."""

    def test_default_cache_dir(self, tmp_path, monkeypatch):
        """Default cache dir is under .paper-reader."""
        monkeypatch.setenv("HOME", str(tmp_path))
        cache = PaperCache()
        expected = tmp_path / ".paper-reader" / "cache" / "papers"
        assert cache._cache_dir == expected

    def test_custom_cache_dir(self, tmp_path):
        """Custom cache dir is respected."""
        custom = tmp_path / "custom_cache"
        cache = PaperCache(cache_dir=custom)
        assert cache._cache_dir == custom


class TestPaperCacheHas:
    """Tests for has()."""

    def test_returns_false_for_missing(self, tmp_path):
        """Missing paper returns False."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        assert cache.has("arxiv:12345") is False

    def test_returns_true_for_existing(self, tmp_path):
        """Existing paper returns True."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        cache.set("arxiv:12345", {"title": "Test"})
        assert cache.has("arxiv:12345") is True


class TestPaperCacheGet:
    """Tests for get()."""

    def test_returns_none_for_missing(self, tmp_path):
        """Missing paper returns None."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        assert cache.get("arxiv:12345") is None

    def test_returns_cached_data(self, tmp_path):
        """Cached paper returns stored data."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        cache.set("arxiv:12345", {"title": "Test Paper", "domain": "ai"})
        result = cache.get("arxiv:12345")
        assert result["title"] == "Test Paper"
        assert result["domain"] == "ai"


class TestPaperCacheSet:
    """Tests for set()."""

    def test_creates_cache_file(self, tmp_path):
        """set() creates a cache file."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        cache.set("arxiv:12345", {"title": "Test"})
        assert cache.has("arxiv:12345")


class TestPaperCacheClear:
    """Tests for clear()."""

    def test_clear_single_paper(self, tmp_path):
        """clear(paper_id) removes single paper."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        cache.set("arxiv:12345", {"title": "Test"})
        cache.clear("arxiv:12345")
        assert cache.has("arxiv:12345") is False

    def test_clear_all(self, tmp_path):
        """clear() with no args removes all papers."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        cache.set("arxiv:12345", {})
        cache.set("doi:67890", {})
        cache.clear()
        assert cache.has("arxiv:12345") is False
        assert cache.has("doi:67890") is False
