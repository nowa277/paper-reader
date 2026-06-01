"""Configuration manager for paper-reader skill.

Handles reading, writing, and accessing the unified config stored at
~/.paper-reader/config.json. Creates the directory and default config
automatically on first use or if the existing file is corrupted.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "version": "1.0",
    "initialized_skills": [],
    "mineru": {
        "installed": False,
        "path": None,
        "version": None,
        "last_check": None,
    },
    "fetch": {
        "default_mode": "jina",
    },
    "analyze": {
        "default_template": "default",
    },
}

CONFIG_DIR = Path.home() / ".paper-reader"
CONFIG_FILE = CONFIG_DIR / "config.json"


class ConfigManager:
    """Manages paper-reader configuration stored in ~/.paper-reader/config.json."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize ConfigManager.

        Args:
            config_path: Override the default config file path. Useful for testing.
        """
        self._config_path = config_path or CONFIG_FILE
        self._config_dir = self._config_path.parent
        self._config: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load config from disk. Creates default config if file is missing or corrupted."""
        self._ensure_dir()
        if self._config_path.exists():
            try:
                text = self._config_path.read_text(encoding="utf-8")
                data = json.loads(text)
                if not isinstance(data, dict):
                    raise ValueError("Config root must be a JSON object")
                self._config = data
                return
            except (json.JSONDecodeError, ValueError, OSError) as exc:
                logger.warning("Config file corrupted (%s), resetting to defaults", exc)
        # No valid config found — write defaults and use them
        self._config = self._deep_copy_default()
        self.save()

    def save(self) -> None:
        """Write current config to disk."""
        self._ensure_dir()
        try:
            self._config_path.write_text(
                json.dumps(self._config, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            logger.error("Failed to save config: %s", exc)
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by dotted key.

        Args:
            key: Dot-separated key path, e.g. "mineru.installed".
            default: Value returned when the key is not found.

        Returns:
            The config value, or *default* if the key path does not exist.
        """
        parts = key.split(".")
        node: Any = self._config
        for part in parts:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def set(self, key: str, value: Any) -> None:
        """Set a config value by dotted key and persist to disk.

        Args:
            key: Dot-separated key path, e.g. "mineru.installed".
            value: The value to store.
        """
        parts = key.split(".")
        node: dict[str, Any] = self._config
        for part in parts[:-1]:
            if part not in node or not isinstance(node[part], dict):
                node[part] = {}
            node = node[part]
        node[parts[-1]] = value
        self.save()

    def get_all(self) -> dict[str, Any]:
        """Return a copy of the entire config dictionary."""
        return dict(self._config)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_dir(self) -> None:
        """Create the config directory if it does not exist."""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error("Failed to create config directory %s: %s", self._config_dir, exc)
            raise

    @staticmethod
    def _deep_copy_default() -> dict[str, Any]:
        """Return a deep copy of the default config."""
        return json.loads(json.dumps(DEFAULT_CONFIG))
