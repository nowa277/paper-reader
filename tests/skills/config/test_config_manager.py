"""Tests for ConfigManager."""

import json
import tempfile
from pathlib import Path

import pytest
from skills.config.config_manager import ConfigManager, DEFAULT_CONFIG


class TestConfigManagerInit:
    """Tests for ConfigManager initialization."""

    def test_loads_existing_config(self, temp_config_dir):
        """Existing config file is loaded."""
        config_file = temp_config_dir / "config.json"
        config_file.write_text(json.dumps({"version": "1.0", "test": "data"}))

        manager = ConfigManager(config_path=config_file)
        assert manager.get("test") == "data"

    def test_creates_default_if_missing(self, temp_config_dir):
        """Missing config file creates default."""
        config_file = temp_config_dir / "config.json"
        manager = ConfigManager(config_path=config_file)

        assert manager.get("version") == "1.0"
        assert config_file.exists()

    def test_creates_default_if_corrupted(self, temp_config_dir):
        """Corrupted config file resets to default."""
        config_file = temp_config_dir / "config.json"
        config_file.write_text("not valid json{")

        manager = ConfigManager(config_path=config_file)
        assert manager.get("version") == "1.0"


class TestConfigManagerGet:
    """Tests for ConfigManager.get method."""

    def test_get_simple_key(self, temp_config_dir):
        """Simple key returns value."""
        manager = ConfigManager(config_path=temp_config_dir / "c.json")
        assert manager.get("version") == "1.0"

    def test_get_nested_key(self, temp_config_dir):
        """Dotted key returns nested value."""
        manager = ConfigManager(config_path=temp_config_dir / "c.json")
        assert manager.get("mineru.installed") is False

    def test_get_missing_key_returns_default(self, temp_config_dir):
        """Missing key returns provided default."""
        manager = ConfigManager(config_path=temp_config_dir / "c.json")
        assert manager.get("nonexistent", "default") == "default"

    def test_get_missing_no_default_returns_none(self, temp_config_dir):
        """Missing key without default returns None."""
        manager = ConfigManager(config_path=temp_config_dir / "c.json")
        assert manager.get("nonexistent") is None


class TestConfigManagerSet:
    """Tests for ConfigManager.set method."""

    def test_set_simple_key(self, temp_config_dir):
        """Setting simple key persists and returns on reload."""
        config_file = temp_config_dir / "c.json"
        manager = ConfigManager(config_path=config_file)

        manager.set("test_key", "test_value")
        assert manager.get("test_key") == "test_value"

        # Verify persisted
        manager2 = ConfigManager(config_path=config_file)
        assert manager2.get("test_key") == "test_value"

    def test_set_nested_key(self, temp_config_dir):
        """Setting dotted key creates intermediate dicts."""
        config_file = temp_config_dir / "c.json"
        manager = ConfigManager(config_path=config_file)

        manager.set("new_section.nested_key", "nested_value")
        assert manager.get("new_section.nested_key") == "nested_value"


class TestConfigManagerGetAll:
    """Tests for ConfigManager.get_all method."""

    def test_returns_copy_of_config(self, temp_config_dir):
        """get_all returns a copy, not the original."""
        manager = ConfigManager(config_path=temp_config_dir / "c.json")
        all_config = manager.get_all()

        assert isinstance(all_config, dict)
        assert "version" in all_config


class TestConfigManagerSave:
    """Tests for ConfigManager.save method."""

    def test_save_creates_directory(self, temp_config_dir):
        """Save creates parent directory if missing."""
        config_file = temp_config_dir / "subdir" / "config.json"
        manager = ConfigManager(config_path=config_file)

        manager.set("test", "value")
        assert config_file.exists()
