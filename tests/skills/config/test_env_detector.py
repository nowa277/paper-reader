"""Tests for environment detector."""

import os
from unittest.mock import patch
from skills.config.env_detector import detect_venv_type, check_venv_compatibility


class TestDetectVenvType:
    """Tests for detect_venv_type()."""

    def test_returns_system_when_no_venv_vars(self):
        """No virtual env vars means system Python."""
        env = {"PATH": "/usr/bin"}
        with patch.dict(os.environ, env, clear=True):
            result = detect_venv_type()
            assert result == "system"

    def test_returns_venv_when_virtuenv_set(self):
        """VIRTUAL_ENV set means venv."""
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv"}):
            result = detect_venv_type()
            assert result == "venv"

    def test_returns_conda_when_conda_default_env_set(self):
        """CONDA_DEFAULT_ENV set means conda."""
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "base"}):
            result = detect_venv_type()
            assert result == "conda"

    def test_returns_uv_when_uv_cache_set(self):
        """UV_CACHE_DIR set means uv."""
        with patch.dict(os.environ, {"UV_CACHE_DIR": "/path/to/cache"}):
            result = detect_venv_type()
            assert result == "uv"


class TestCheckVenvCompatibility:
    """Tests for check_venv_compatibility()."""

    def test_system_python_is_ok(self):
        """System Python is compatible."""
        with patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True):
            ok, msg = check_venv_compatibility()
            assert ok is True

    def test_conda_warns(self):
        """Conda environment triggers warning."""
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "base"}):
            ok, msg = check_venv_compatibility()
            assert ok is False
            assert "conda" in msg.lower()
