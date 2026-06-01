"""Tests for config backup."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from skills.config.backup import ConfigBackup


class TestConfigBackupInit:
    """Tests for ConfigBackup initialization."""

    def test_default_backup_dir(self, tmp_path, monkeypatch):
        """Default backup dir is under .paper-reader."""
        monkeypatch.setenv("HOME", str(tmp_path))
        backup = ConfigBackup()
        expected = tmp_path / ".paper-reader" / "backups"
        assert backup._backup_dir == expected

    def test_custom_backup_dir(self, tmp_path):
        """Custom backup dir is respected."""
        custom = tmp_path / "custom_backups"
        backup = ConfigBackup(backup_dir=custom)
        assert backup._backup_dir == custom


class TestConfigBackupBackup:
    """Tests for backup()."""

    def test_creates_backup_file(self, tmp_path):
        """backup() creates a backup file."""
        backup = ConfigBackup(backup_dir=tmp_path)
        config = tmp_path / "config.json"
        config.write_text('{"key": "value"}')

        result = backup.backup(config)
        assert Path(result).exists()

    def test_backup_contains_original_data(self, tmp_path):
        """Backup file contains original data."""
        backup = ConfigBackup(backup_dir=tmp_path)
        config = tmp_path / "config.json"
        config.write_text('{"key": "value"}')

        result = backup.backup(config)
        with open(result) as f:
            data = json.load(f)
        assert data["key"] == "value"


class TestConfigBackupRestore:
    """Tests for restore()."""

    def test_restores_from_backup(self, tmp_path):
        """restore() overwrites config with backup."""
        backup = ConfigBackup(backup_dir=tmp_path)
        config = tmp_path / "config.json"
        config.write_text('{"key": "old"}')

        backup_path = backup.backup(config)
        config.write_text('{"key": "new"}')

        backup.restore(Path(backup_path))
        with open(config) as f:
            data = json.load(f)
        assert data["key"] == "old"


class TestConfigBackupList:
    """Tests for list_backups()."""

    def test_lists_all_backups(self, tmp_path):
        """list_backups() returns all backup paths."""
        backup = ConfigBackup(backup_dir=tmp_path)
        config = tmp_path / "config.json"
        config.write_text('{}')

        b1 = backup.backup(config)
        config.write_text('{"a": 1}')
        b2 = backup.backup(config)

        backups = backup.list_backups()
        assert len(backups) == 2
        assert b1 in backups
        assert b2 in backups


class TestConfigBackupPrune:
    """Tests for prune()."""

    def test_prune_removes_old_backups(self, tmp_path):
        """prune() removes all but keep N newest."""
        backup = ConfigBackup(backup_dir=tmp_path)
        config = tmp_path / "config.json"
        config.write_text('{}')

        for i in range(7):
            config.write_text(f'{{"v": {i}}}')
            backup.backup(config)

        backup.prune(keep=3)
        backups = backup.list_backups()
        assert len(backups) == 3
