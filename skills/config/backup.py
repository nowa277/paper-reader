"""Config backup and restore for paper-reader."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path


class ConfigBackup:
    """Manages configuration backups for rollback."""

    DEFAULT_BACKUP_SUBDIR = "backups"

    def __init__(self, backup_dir: Path | None = None):
        """Initialize backup manager.

        Args:
            backup_dir: Directory for storing backups.
        """
        if backup_dir:
            self._backup_dir = backup_dir
        else:
            home = Path(os.environ.get("HOME", str(Path.home())))
            self._backup_dir = home / ".paper-reader" / self.DEFAULT_BACKUP_SUBDIR
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure backup directory exists."""
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, config_path: Path) -> str:
        """Create a backup of the config file.

        Args:
            config_path: Path to config file to backup.

        Returns:
            Path to the backup file created.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_path = self._backup_dir / f"config_{timestamp}.json"
        shutil.copy2(config_path, backup_path)
        return str(backup_path)

    def list_backups(self) -> list[str]:
        """List all backup file paths.

        Returns:
            List of backup file paths sorted newest first.
        """
        if not self._backup_dir.exists():
            return []
        backups = sorted(
            self._backup_dir.glob("config_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return [str(p) for p in backups]

    def restore(self, backup_path: Path) -> None:
        """Restore config from a backup.

        Args:
            backup_path: Path to the backup file.
        """
        config_file = self._backup_dir / "config.json"
        shutil.copy2(backup_path, config_file)

    def prune(self, keep: int = 5) -> None:
        """Remove old backups, keeping the newest N.

        Args:
            keep: Number of recent backups to keep.
        """
        backups = self.list_backups()
        for old in backups[keep:]:
            Path(old).unlink(missing_ok=True)
