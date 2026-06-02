"""Tests for MinerU installer module."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
import importlib.util

installer_file = Path(__file__).parent.parent / "installer.py"
spec = importlib.util.spec_from_file_location("installer", installer_file)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

check_python_version = installer.check_python_version
verify_installation = installer.verify_installation
install_mineru = installer.install_mineru
_resolve_pip_command = installer._resolve_pip_command


class TestCheckPythonVersion:
    """Tests for check_python_version()."""

    def test_passes_on_3_10(self):
        with patch.object(installer.sys, "version_info", (3, 10, 0)):
            ok, msg = check_python_version()
        assert ok is True
        assert "3.10" in msg

    def test_passes_on_newer(self):
        with patch.object(installer.sys, "version_info", (3, 12, 1)):
            ok, msg = check_python_version()
        assert ok is True

    def test_fails_on_3_9(self):
        with patch.object(installer.sys, "version_info", (3, 9, 7)):
            ok, msg = check_python_version()
        assert ok is False
        assert "too old" in msg

    def test_fails_on_3_8(self):
        with patch.object(installer.sys, "version_info", (3, 8, 0)):
            ok, msg = check_python_version()
        assert ok is False

    def test_message_contains_version(self):
        with patch.object(installer.sys, "version_info", (3, 9, 1)):
            ok, msg = check_python_version()
        assert "3.9" in msg
        assert "3.10" in msg


class TestVerifyInstallation:
    """Tests for verify_installation()."""

    def test_delegates_to_detect_mineru(self):
        fake_result = {"installed": True, "path": "/usr/bin/magic-pdf", "version": "1.0.0"}
        with patch.object(installer, "detect_mineru", return_value=fake_result):
            result = verify_installation()
        assert result == fake_result

    def test_returns_detection_dict(self):
        fake_result = {"installed": False, "path": None, "version": None}
        with patch.object(installer, "detect_mineru", return_value=fake_result):
            result = verify_installation()
        assert "installed" in result
        assert "path" in result
        assert "version" in result


class TestInstallMineru:
    """Tests for install_mineru()."""

    def _make_config_manager(self):
        """Create a mock ConfigManager."""
        cm = MagicMock()
        cm.set = MagicMock()
        return cm

    def test_requires_user_consent(self):
        result = install_mineru(user_consent=False)
        assert result["success"] is False
        assert "confirmation" in result["message"].lower()
        assert result["detection"] is not None

    def test_raises_on_old_python(self):
        cm = self._make_config_manager()
        with patch.object(installer.sys, "version_info", (3, 8, 0)):
            with pytest.raises(RuntimeError, match="too old"):
                install_mineru(user_consent=True, config_manager=cm)

    def test_dry_run_skips_pip(self):
        cm = self._make_config_manager()
        detection = {"installed": True, "path": "/usr/bin/magic-pdf", "version": "1.0.0"}
        with patch.object(installer, "verify_installation", return_value=detection):
            with patch.object(installer, "check_python_version", return_value=(True, "ok")):
                with patch("subprocess.run") as mock_run:
                    result = install_mineru(user_consent=True, config_manager=cm, dry_run=True)
        # subprocess.run should NOT be called
        mock_run.assert_not_called()
        assert result["success"] is True
        assert "dry_run" in result["message"]

    def test_successful_install(self):
        cm = self._make_config_manager()
        pip_result = MagicMock()
        pip_result.returncode = 0
        pip_result.stdout = "Successfully installed mineru-1.0.0"
        pip_result.stderr = ""

        detection = {"installed": True, "path": "/usr/bin/magic-pdf", "version": "1.0.0"}
        with patch.object(installer, "check_python_version", return_value=(True, "ok")):
            with patch.object(installer, "_resolve_pip_command", return_value="pip3"):
                with patch("subprocess.run", return_value=pip_result):
                    with patch.object(installer, "verify_installation", return_value=detection):
                        result = install_mineru(user_consent=True, config_manager=cm)

        assert result["success"] is True
        assert "successfully" in result["message"].lower()
        assert result["detection"]["installed"] is True

        # Config should be updated
        cm.set.assert_any_call("mineru.installed", True)
        cm.set.assert_any_call("mineru.path", "/usr/bin/magic-pdf")
        cm.set.assert_any_call("mineru.version", "1.0.0")

    def test_pip_install_fails(self):
        cm = self._make_config_manager()
        pip_result = MagicMock()
        pip_result.returncode = 1
        pip_result.stdout = ""
        pip_result.stderr = "error: no matching distribution"

        detection = {"installed": False, "path": None, "version": None}
        with patch.object(installer, "check_python_version", return_value=(True, "ok")):
            with patch.object(installer, "_resolve_pip_command", return_value="pip3"):
                with patch("subprocess.run", return_value=pip_result):
                    with patch.object(installer, "verify_installation", return_value=detection):
                        result = install_mineru(user_consent=True, config_manager=cm)

        assert result["success"] is False
        assert "failed" in result["message"].lower()

    def test_pip_timeout(self):
        cm = self._make_config_manager()
        detection = {"installed": False, "path": None, "version": None}
        with patch.object(installer, "check_python_version", return_value=(True, "ok")):
            with patch.object(installer, "_resolve_pip_command", return_value="pip3"):
                with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pip3", 300)):
                    with patch.object(installer, "verify_installation", return_value=detection):
                        result = install_mineru(user_consent=True, config_manager=cm)

        assert result["success"] is False
        assert "timed out" in result["message"]

    def test_pip_oserror(self):
        cm = self._make_config_manager()
        detection = {"installed": False, "path": None, "version": None}
        with patch.object(installer, "check_python_version", return_value=(True, "ok")):
            with patch.object(installer, "_resolve_pip_command", return_value="pip3"):
                with patch("subprocess.run", side_effect=OSError("pip not found")):
                    with patch.object(installer, "verify_installation", return_value=detection):
                        result = install_mineru(user_consent=True, config_manager=cm)

        assert result["success"] is False
        assert "Failed to run" in result["message"]

    def test_install_succeeds_but_verification_fails(self):
        cm = self._make_config_manager()
        pip_result = MagicMock()
        pip_result.returncode = 0
        pip_result.stdout = "Successfully installed mineru-1.0.0"
        pip_result.stderr = ""

        detection = {"installed": False, "path": None, "version": None}
        with patch.object(installer, "check_python_version", return_value=(True, "ok")):
            with patch.object(installer, "_resolve_pip_command", return_value="pip3"):
                with patch("subprocess.run", return_value=pip_result):
                    with patch.object(installer, "verify_installation", return_value=detection):
                        result = install_mineru(user_consent=True, config_manager=cm)

        assert result["success"] is False
        assert "verification" in result["message"].lower()

    def test_creates_config_manager_if_not_provided(self):
        pip_result = MagicMock()
        pip_result.returncode = 0
        pip_result.stdout = "ok"
        pip_result.stderr = ""

        detection = {"installed": True, "path": "/usr/bin/magic-pdf", "version": "1.0.0"}
        mock_cm = MagicMock()
        with patch.object(installer, "check_python_version", return_value=(True, "ok")):
            with patch.object(installer, "_resolve_pip_command", return_value="pip3"):
                with patch("subprocess.run", return_value=pip_result):
                    with patch.object(installer, "verify_installation", return_value=detection):
                        with patch.object(installer, "ConfigManager", return_value=mock_cm):
                            result = install_mineru(user_consent=True)

        assert result["success"] is True
        mock_cm.set.assert_any_call("mineru.installed", True)

    def test_install_mineru_reports_elapsed_time(self):
        """install_mineru returns elapsed_seconds in result."""
        cm = self._make_config_manager()
        pip_result = MagicMock()
        pip_result.returncode = 0
        pip_result.stdout = "Successfully installed mineru-1.0.0"
        pip_result.stderr = ""

        detection = {"installed": True, "path": "/usr/bin/magic-pdf", "version": "1.0.0"}
        with patch.object(installer, "check_python_version", return_value=(True, "ok")):
            with patch.object(installer, "_resolve_pip_command", return_value="pip3"):
                with patch("subprocess.run", return_value=pip_result):
                    with patch.object(installer, "verify_installation", return_value=detection):
                        result = install_mineru(user_consent=True, config_manager=cm)

        assert "elapsed_seconds" in result
        assert isinstance(result["elapsed_seconds"], float)
        assert result["elapsed_seconds"] >= 0

    def test_uses_pip3_command(self):
        cm = self._make_config_manager()
        pip_result = MagicMock()
        pip_result.returncode = 0
        pip_result.stdout = "ok"
        pip_result.stderr = ""

        detection = {"installed": True, "path": "/usr/bin/magic-pdf", "version": "1.0.0"}
        with patch.object(installer, "check_python_version", return_value=(True, "ok")):
            with patch.object(installer, "_resolve_pip_command", return_value="pip3"):
                with patch("subprocess.run", return_value=pip_result) as mock_run:
                    with patch.object(installer, "verify_installation", return_value=detection):
                        install_mineru(user_consent=True, config_manager=cm)

        actual_cmd = mock_run.call_args[0][0]
        assert actual_cmd[0] == "pip3"
        assert "install" in actual_cmd
        assert "mineru" in actual_cmd


class TestResolvePipCommand:
    """Tests for _resolve_pip_command()."""

    def test_prefers_pip3(self):
        with patch.object(installer, "which", side_effect=lambda cmd: "/usr/bin/pip3" if cmd == "pip3" else None):
            result = _resolve_pip_command()
        assert result == "pip3"

    def test_falls_back_to_pip(self):
        with patch.object(installer, "which", side_effect=lambda cmd: "/usr/bin/pip" if cmd == "pip" else None):
            result = _resolve_pip_command()
        assert result == "pip"

    def test_defaults_to_pip3_when_none_found(self):
        with patch.object(installer, "which", return_value=None):
            result = _resolve_pip_command()
        assert result == "pip3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
