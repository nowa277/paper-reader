"""Paper cache for storing processed paper results."""

import json
from pathlib import Path


class PaperCache:
    """Cache for processed paper results keyed by paper ID."""

    def __init__(self, cache_dir: Path | None = None):
        """Initialize paper cache.

        Args:
            cache_dir: Directory for storing cache files.
        """
        self._cache_dir = cache_dir or (Path.home() / ".paper-reader" / "cache" / "papers")
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _paper_path(self, paper_id: str) -> Path:
        """Get path for a paper's cache file."""
        # Sanitize paper_id for use as filename
        safe_id = paper_id.replace("/", "_").replace(":", "_")
        return self._cache_dir / f"{safe_id}.json"

    def has(self, paper_id: str) -> bool:
        """Check if paper is cached.

        Args:
            paper_id: Paper identifier (e.g., "arxiv:12345").

        Returns:
            True if paper is cached.
        """
        return self._paper_path(paper_id).exists()

    def get(self, paper_id: str) -> dict | None:
        """Get cached paper result.

        Args:
            paper_id: Paper identifier.

        Returns:
            Cached result dict or None if not found.
        """
        path = self._paper_path(paper_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, paper_id: str, result: dict) -> None:
        """Cache paper result.

        Args:
            paper_id: Paper identifier.
            result: Result dict to cache.
        """
        path = self._paper_path(paper_id)
        path.write_text(json.dumps(result, indent=2))

    def clear(self, paper_id: str | None = None) -> None:
        """Clear cache for paper or all papers.

        Args:
            paper_id: Specific paper to clear, or None to clear all.
        """
        if paper_id:
            self._paper_path(paper_id).unlink(missing_ok=True)
        else:
            for f in self._cache_dir.glob("*.json"):
                f.unlink(missing_ok=True)
