"""Batch checkpoint manager for paper processing.

Stores processed paper IDs per batch to enable restart-from-checkpoint.
"""

import json
import threading
from pathlib import Path
from typing import Optional


class BatchCheckpoint:
    """Manages checkpoint state for batch processing."""

    DEFAULT_CHECKPOINT_DIR_NAME = ".paper-reader"
    DEFAULT_CHECKPOINT_FILE_NAME = "batch_checkpoints.json"

    def __init__(self, checkpoint_path: Optional[Path] = None):
        """Initialize checkpoint manager.

        Args:
            checkpoint_path: Custom path for checkpoint file.
        """
        if checkpoint_path:
            self._path = checkpoint_path
        else:
            self._path = Path.home() / self.DEFAULT_CHECKPOINT_DIR_NAME / self.DEFAULT_CHECKPOINT_FILE_NAME
        self._lock = threading.Lock()
        self._cache: dict[str, list[str]] = {}
        self._load()

    def _load(self) -> None:
        """Load checkpoint file into memory."""
        self._ensure_dir()
        if self._path.exists():
            try:
                self._cache = json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError):
                self._cache = {}

    def _save(self) -> None:
        """Save memory cache to checkpoint file."""
        self._ensure_dir()
        self._path.write_text(json.dumps(self._cache, indent=2))

    def _ensure_dir(self) -> None:
        """Ensure checkpoint directory exists."""
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def get_processed(self, batch_id: str) -> set[str]:
        """Get set of processed paper IDs for a batch.

        Args:
            batch_id: Batch identifier.

        Returns:
            Set of paper IDs already processed.
        """
        return set(self._cache.get(batch_id, []))

    def mark_processed(self, batch_id: str, paper_id: str) -> None:
        """Mark a paper as processed in a batch.

        Args:
            batch_id: Batch identifier.
            paper_id: Paper identifier (e.g., "arxiv:12345").
        """
        with self._lock:
            if batch_id not in self._cache:
                self._cache[batch_id] = []
            if paper_id not in self._cache[batch_id]:
                self._cache[batch_id].append(paper_id)
            self._save()

    def is_processed(self, batch_id: str, paper_id: str) -> bool:
        """Check if a paper has been processed.

        Args:
            batch_id: Batch identifier.
            paper_id: Paper identifier.

        Returns:
            True if paper was already processed.
        """
        return paper_id in self.get_processed(batch_id)

    def clear(self, batch_id: str) -> None:
        """Clear checkpoint for a batch.

        Args:
            batch_id: Batch identifier.
        """
        with self._lock:
            if batch_id in self._cache:
                del self._cache[batch_id]
                self._save()

    def list_batches(self) -> list[str]:
        """List all batch IDs.

        Returns:
            List of batch IDs.
        """
        return list(self._cache.keys())
