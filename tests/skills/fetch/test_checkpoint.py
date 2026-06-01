"""Tests for batch checkpoint."""

import json
import tempfile
from pathlib import Path
from skills.fetch.checkpoint import BatchCheckpoint


class TestBatchCheckpointInit:
    """Tests for BatchCheckpoint initialization."""

    def test_default_path_is_paper_reader_dir(self, tmp_path, monkeypatch):
        """Default checkpoint path is ~/.paper-reader/batch_checkpoints.json."""
        monkeypatch.setenv("HOME", str(tmp_path))
        checkpoint = BatchCheckpoint()
        expected = tmp_path / ".paper-reader" / "batch_checkpoints.json"
        assert checkpoint._path == expected

    def test_custom_path(self, tmp_path):
        """Custom path is respected."""
        custom = tmp_path / "custom_checkpoints.json"
        checkpoint = BatchCheckpoint(checkpoint_path=custom)
        assert checkpoint._path == custom


class TestBatchCheckpointGetProcessed:
    """Tests for get_processed()."""

    def test_returns_empty_set_for_new_batch(self, tmp_path):
        """New batch returns empty set."""
        checkpoint = BatchCheckpoint(checkpoint_path=tmp_path / "cp.json")
        result = checkpoint.get_processed("batch_001")
        assert result == set()

    def test_returns_stored_ids(self, tmp_path):
        """Stored paper IDs are returned."""
        path = tmp_path / "cp.json"
        path.write_text(json.dumps({"batch_001": ["arxiv:123", "doi:456"]}))
        checkpoint = BatchCheckpoint(checkpoint_path=path)
        result = checkpoint.get_processed("batch_001")
        assert result == {"arxiv:123", "doi:456"}


class TestBatchCheckpointMarkProcessed:
    """Tests for mark_processed()."""

    def test_marks_paper_as_processed(self, tmp_path):
        """mark_processed adds paper ID to batch."""
        path = tmp_path / "cp.json"
        checkpoint = BatchCheckpoint(checkpoint_path=path)
        checkpoint.mark_processed("batch_001", "arxiv:123")
        assert checkpoint.is_processed("batch_001", "arxiv:123")

    def test_idempotent(self, tmp_path):
        """Calling mark_processed twice is idempotent."""
        path = tmp_path / "cp.json"
        checkpoint = BatchCheckpoint(checkpoint_path=path)
        checkpoint.mark_processed("batch_001", "arxiv:123")
        checkpoint.mark_processed("batch_001", "arxiv:123")
        result = checkpoint.get_processed("batch_001")
        assert result == {"arxiv:123"}


class TestBatchCheckpointIsProcessed:
    """Tests for is_processed()."""

    def test_unprocessed_returns_false(self, tmp_path):
        """Unprocessed paper returns False."""
        path = tmp_path / "cp.json"
        checkpoint = BatchCheckpoint(checkpoint_path=path)
        assert checkpoint.is_processed("batch_001", "arxiv:123") is False


class TestBatchCheckpointClear:
    """Tests for clear()."""

    def test_clears_batch(self, tmp_path):
        """clear removes batch from checkpoint file."""
        path = tmp_path / "cp.json"
        path.write_text(json.dumps({"batch_001": ["arxiv:123"]}))
        checkpoint = BatchCheckpoint(checkpoint_path=path)
        checkpoint.clear("batch_001")
        assert checkpoint.get_processed("batch_001") == set()


class TestBatchCheckpointListBatches:
    """Tests for list_batches()."""

    def test_lists_all_batches(self, tmp_path):
        """list_batches returns all batch IDs."""
        path = tmp_path / "cp.json"
        path.write_text(json.dumps({"batch_001": [], "batch_002": []}))
        checkpoint = BatchCheckpoint(checkpoint_path=path)
        batches = checkpoint.list_batches()
        assert set(batches) == {"batch_001", "batch_002"}
