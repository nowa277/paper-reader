"""Tests for platform detection utilities.

These tests verify the platform detection works correctly.
We use direct function calls and pytest's monkeypatch for environment handling.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import importlib.util

# Dynamically load the platform module to avoid conflicts with stdlib
config_dir = Path(__file__).parent.parent
platform_file = config_dir / "platform.py"
spec = importlib.util.spec_from_file_location("platform_detection", platform_file)
platform_detection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(platform_detection)

get_platform = platform_detection.get_platform
get_linux_distro = platform_detection.get_linux_distro
is_wsl = platform_detection.is_wsl


class TestGetPlatform:
    """Tests for get_platform() function."""

    def test_returns_linux_on_linux(self):
        """On Linux, should return 'linux'."""
        result = get_platform()
        assert result == "linux"

    def test_returns_valid_platform(self):
        """Should return one of the valid platform strings."""
        result = get_platform()
        valid = {"linux", "macos", "windows", "unknown"}
        assert result in valid


class TestGetLinuxDistro:
    """Tests for get_linux_distro() function."""

    def test_returns_ubuntu_on_ubuntu(self):
        """On Ubuntu, should return 'ubuntu'."""
        result = get_linux_distro()
        assert result == "ubuntu"

    def test_returns_none_on_non_linux(self):
        """On non-Linux, should return None."""
        # Patch get_platform to return 'windows'
        with patch.object(platform_detection, "get_platform", return_value="windows"):
            result = get_linux_distro()
        assert result is None


class TestIsWSL:
    """Tests for is_wsl() function."""

    def test_returns_false_on_native_linux(self):
        """On native Linux (not WSL), should return False."""
        result = is_wsl()
        assert result is False

    def test_returns_false_on_non_linux(self):
        """On non-Linux, should return False."""
        with patch.object(platform_detection, "get_platform", return_value="windows"):
            result = is_wsl()
        assert result is False

    def test_detects_wsl_in_proc_version(self):
        """Should detect WSL in /proc/version."""
        with patch.object(platform_detection, "get_platform", return_value="linux"):
            with patch.object(Path, "read_text") as mock_read:
                mock_read.return_value = "Linux version 5.10.16.3-microsoft-standard-WSL2"
                result = is_wsl()
        assert result is True

    def test_detects_wsl_in_env_var(self):
        """Should detect WSL via WSL_DISTRO_NAME env var."""
        with patch.object(platform_detection, "get_platform", return_value="linux"):
            with patch.object(Path, "read_text") as mock_read:
                mock_read.return_value = "Linux version 6.8.0"
                # Use environment variable detection
                with patch.dict(os.environ, {"WSL_DISTRO_NAME": "Ubuntu"}):
                    result = is_wsl()
        assert result is True


class TestPlatformInfo:
    """Tests for PlatformInfo dataclass."""

    def test_platform_info_dataclass(self):
        """Test PlatformInfo can be instantiated with all fields."""
        PlatformInfo = platform_detection.PlatformInfo

        info = PlatformInfo(
            platform="linux",
            distro="ubuntu",
            distro_version="22.04",
            is_wsl=True,
            wsl_version=2,
            macos_version=None,
            shell=None,
            shell_version=None,
            windows_version=None,
        )

        assert info.platform == "linux"
        assert info.distro == "ubuntu"
        assert info.is_wsl is True
        assert info.wsl_version == 2
        assert info.is_linux is True
        assert info.is_powershell is False
        assert info.is_cmd is False

    def test_is_macos_property(self):
        """Test is_macos property."""
        PlatformInfo = platform_detection.PlatformInfo
        info = PlatformInfo(platform="macos")
        assert info.is_macos is True
        assert info.is_linux is False

    def test_is_windows_property(self):
        """Test is_windows property."""
        PlatformInfo = platform_detection.PlatformInfo
        info = PlatformInfo(platform="windows")
        assert info.is_windows is True
        assert info.is_unknown is False

    def test_is_unknown_property(self):
        """Test is_unknown property."""
        PlatformInfo = platform_detection.PlatformInfo
        info = PlatformInfo(platform="unknown")
        assert info.is_unknown is True

    def test_is_powershell_property(self):
        """Test is_powershell detects both powershell and pwsh."""
        PlatformInfo = platform_detection.PlatformInfo
        info_pwsh = PlatformInfo(platform="windows", shell="pwsh")
        info_ps = PlatformInfo(platform="windows", shell="powershell")
        assert info_pwsh.is_powershell is True
        assert info_ps.is_powershell is True

    def test_is_cmd_property(self):
        """Test is_cmd property."""
        PlatformInfo = platform_detection.PlatformInfo
        info = PlatformInfo(platform="windows", shell="cmd")
        assert info.is_cmd is True

    def test_default_values(self):
        """Test PlatformInfo has sensible defaults."""
        PlatformInfo = platform_detection.PlatformInfo
        info = PlatformInfo()
        assert info.platform == "unknown"
        assert info.distro is None
        assert info.distro_version is None
        assert info.is_wsl is False
        assert info.wsl_version is None
        assert info.macos_version is None
        assert info.shell is None
        assert info.shell_version is None
        assert info.windows_version is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])