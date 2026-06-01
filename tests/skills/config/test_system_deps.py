"""Tests for system dependency detection."""

import pytest
from unittest.mock import patch, MagicMock
from skills.config.system_deps import (
    Dependency,
    SYSTEM_DEPS,
    check_dependency,
    check_all_dependencies,
    get_missing_required,
    get_installation_instructions,
)


class TestCheckDependency:
    """Tests for check_dependency function."""

    def test_unknown_dependency_returns_false(self):
        """Unknown dependency IDs return (False, error)."""
        installed, msg = check_dependency("nonexistent")
        assert installed is False
        assert "Unknown dependency" in msg

    def test_missing_required_dep(self):
        """Missing dependency returns (False, not found message)."""
        with patch("shutil.which", return_value=None):
            installed, msg = check_dependency("curl")
            assert installed is False
            assert "not found" in msg.lower()

    def test_curl_found(self):
        """curl is detected if in PATH."""
        with patch("shutil.which", return_value="/usr/bin/curl"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "curl 7.81.0"
                installed, version = check_dependency("curl")
                assert installed is True
                assert "7.81.0" in version


class TestCheckAllDependencies:
    """Tests for check_all_dependencies function."""

    def test_returns_dict_with_all_deps(self):
        """Returns dict with all dependency IDs as keys."""
        results = check_all_dependencies()
        for dep_id in SYSTEM_DEPS:
            assert dep_id in results
        assert "installed" in results["curl"]
        assert "version" in results["curl"]
        assert "required" in results["curl"]


class TestGetMissingRequired:
    """Tests for get_missing_required function."""

    def test_returns_list_of_strings(self):
        """Returns list of missing required dependency IDs."""
        with patch("skills.config.system_deps.check_dependency") as mock_check:
            mock_check.return_value = (False, "not found")
            missing = get_missing_required()
            assert isinstance(missing, list)
            assert all(isinstance(d, str) for d in missing)


class TestGetInstallationInstructions:
    """Tests for get_installation_instructions function."""

    def test_known_deps_return_instructions(self):
        """Known dependencies return installation instructions."""
        for dep_id in SYSTEM_DEPS:
            instructions = get_installation_instructions(dep_id)
            assert isinstance(instructions, str)
            assert len(instructions) > 0

    def test_unknown_dep_returns_generic_message(self):
        """Unknown deps return generic fallback message."""
        msg = get_installation_instructions("nonexistent")
        assert "nonexistent" in msg
