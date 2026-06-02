"""Tests for MinerU detector module."""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

# Import the module under test
import sys, importlib.util

detector_file = Path(__file__).parent.parent / "detector.py"
spec = importlib.util.spec_from_file_location("detector", detector_file)
detector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(detector)

detect_mineru = detector.detect_mineru
_run_pip_show = detector._run_pip_show
_check_which = detector._check_which
_check_common_paths = detector._check_common_paths


class TestRunPipShow:
    """Tests for _run_pip_show() — tries pip3 first, then pip."""

    def test_tries_pip3_first(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Name: mineru\nVersion: 1.2.3\nLocation: /some/path\n"
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            version, location = _run_pip_show()
        # First call should be pip3
        assert mock_run.call_args_list[0][0][0][0] == "pip3"
        assert version == "1.2.3"
        assert location == "/some/path"

    def test_falls_back_to_pip_when_pip3_fails(self):
        # pip3 returns non-zero, pip succeeds
        fail_result = MagicMock()
        fail_result.returncode = 1
        fail_result.stdout = ""
        success_result = MagicMock()
        success_result.returncode = 0
        success_result.stdout = "Name: mineru\nVersion: 2.0.0\nLocation: /other\n"

        with patch("subprocess.run", side_effect=[fail_result, success_result]) as mock_run:
            version, location = _run_pip_show()
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0][0][0][0] == "pip3"
        assert mock_run.call_args_list[1][0][0][0] == "pip"
        assert version == "2.0.0"
        assert location == "/other"

    def test_falls_back_to_pip_when_pip3_oserror(self):
        success_result = MagicMock()
        success_result.returncode = 0
        success_result.stdout = "Name: mineru\nVersion: 3.0.0\nLocation: /foo\n"

        with patch("subprocess.run", side_effect=[OSError("no pip3"), success_result]) as mock_run:
            version, location = _run_pip_show()
        assert version == "3.0.0"

    def test_returns_none_when_both_fail(self):
        fail_result = MagicMock()
        fail_result.returncode = 1
        fail_result.stdout = ""

        with patch("subprocess.run", return_value=fail_result):
            version, location = _run_pip_show()
        assert version is None
        assert location is None

    def test_returns_none_when_both_oserror(self):
        with patch("subprocess.run", side_effect=OSError("no pip")):
            version, location = _run_pip_show()
        assert version is None
        assert location is None

    def test_returns_none_on_timeout(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pip3", 15)):
            version, location = _run_pip_show()
        assert version is None
        assert location is None

    def test_stops_on_first_success(self):
        """If pip3 succeeds, pip should not be called."""
        success_result = MagicMock()
        success_result.returncode = 0
        success_result.stdout = "Name: mineru\nVersion: 1.0.0\nLocation: /x\n"

        with patch("subprocess.run", return_value=success_result) as mock_run:
            version, location = _run_pip_show()
        assert mock_run.call_count == 1
        assert mock_run.call_args_list[0][0][0][0] == "pip3"


class TestCheckWhich:
    """Tests for _check_which()."""

    def test_returns_resolved_path_when_found(self):
        with patch("shutil.which", return_value="/usr/local/bin/magic-pdf"):
            result = _check_which()
        assert result is not None
        assert "magic-pdf" in result

    def test_returns_none_when_not_found(self):
        with patch("shutil.which", return_value=None):
            result = _check_which()
        assert result is None

    def test_checks_exe_on_windows(self):
        """On Windows, should also check magic-pdf.exe."""
        with patch.object(detector.sys, "platform", "win32"):
            # shutil.which("magic-pdf") returns None, but .exe works
            def which_side_effect(name):
                if name == "magic-pdf.exe":
                    return r"C:\Python311\Scripts\magic-pdf.exe"
                return None
            with patch("shutil.which", side_effect=which_side_effect):
                result = _check_which()
        assert result is not None
        assert "magic-pdf.exe" in result

    def test_no_exe_check_on_linux(self):
        """On non-Windows, should NOT check .exe suffix."""
        with patch.object(detector.sys, "platform", "linux"):
            def which_side_effect(name):
                # If .exe is queried, this should never happen on Linux
                if name == "magic-pdf.exe":
                    pytest.fail("Should not check .exe on Linux")
                return None
            with patch("shutil.which", side_effect=which_side_effect):
                result = _check_which()
        assert result is None


class TestCheckCommonPaths:
    """Tests for _check_common_paths()."""

    def test_finds_magic_pdf_in_linux_local_bin(self):
        with patch.object(detector, "get_platform", return_value="linux"):
            with patch.object(Path, "is_file", side_effect=lambda: True):
                with patch.object(Path, "resolve", return_value=Path("/home/user/.local/bin/magic-pdf")):
                    result = _check_common_paths()
        assert result is not None

    def test_returns_none_when_nothing_found(self):
        with patch.object(detector, "get_platform", return_value="linux"):
            with patch.object(Path, "is_file", return_value=False):
                result = _check_common_paths()
        assert result is None

    def test_returns_none_for_unknown_platform(self):
        with patch.object(detector, "get_platform", return_value="unknown"):
            result = _check_common_paths()
        assert result is None

    def test_macos_glob_resolves_intermediate_wildcard(self):
        """The macOS path ~/Library/Python/*/bin/ has wildcard in an intermediate dir.
        The glob must resolve from ~/Library/Python/ using pattern */bin/."""
        with patch.object(detector, "get_platform", return_value="macos"):
            # Create a real temp directory structure to test glob logic
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                python_dir = Path(tmpdir) / "Library" / "Python"
                python_dir.mkdir(parents=True)
                bin311 = python_dir / "3.11" / "bin"
                bin311.mkdir(parents=True)
                (bin311 / "magic-pdf").touch()

                with patch.object(Path, "expanduser", return_value=Path(tmpdir) / "Library" / "Python" / "*" / "bin"):
                    result = _check_common_paths()
                assert result is not None
                assert "3.11" in result
                assert "magic-pdf" in result

    def test_windows_glob_resolves_intermediate_wildcard(self):
        """The Windows path C:\\Python*\\Scripts\\ has wildcard in an intermediate dir."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts_dir = Path(tmpdir) / "Python311" / "Scripts"
            scripts_dir.mkdir(parents=True)
            (scripts_dir / "magic-pdf.exe").touch()

            # We patch get_platform to windows and construct a pattern
            # that uses tmpdir as the anchor
            with patch.object(detector, "get_platform", return_value="windows"):
                # Pattern: <tmpdir>/Python*/Scripts/
                pattern = str(Path(tmpdir) / "Python*" / "Scripts")
                # Patch _COMMON_PATHS to use our tmpdir pattern
                with patch.object(detector, "_COMMON_PATHS", {"windows": [pattern + "/"]}):
                    result = _check_common_paths()
                assert result is not None
                assert "Python311" in result
                assert "magic-pdf.exe" in result

    def test_windows_checks_exe_suffix(self):
        """On Windows, should check both magic-pdf and magic-pdf.exe in common paths."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts_dir = Path(tmpdir) / "Scripts"
            scripts_dir.mkdir(parents=True)
            # Only magic-pdf.exe exists, not magic-pdf
            (scripts_dir / "magic-pdf.exe").touch()

            with patch.object(detector, "get_platform", return_value="windows"):
                pattern = str(Path(tmpdir) / "Scripts" )
                with patch.object(detector, "_COMMON_PATHS", {"windows": [pattern + "/"]}):
                    result = _check_common_paths()
                assert result is not None
                assert "magic-pdf.exe" in result


class TestDetectMineru:
    """Integration-style tests for detect_mineru()."""

    def test_fully_installed(self):
        """When pip knows the version and which finds the binary."""
        mock_pip = MagicMock()
        mock_pip.returncode = 0
        mock_pip.stdout = "Name: mineru\nVersion: 0.7.0\nLocation: /opt\n"

        with patch("subprocess.run", return_value=mock_pip):
            with patch("shutil.which", return_value="/usr/local/bin/magic-pdf"):
                result = detect_mineru()

        assert result["installed"] is True
        assert result["version"] == "0.7.0"
        assert result["path"] is not None

    def test_not_installed(self):
        """When nothing is found."""
        mock_pip = MagicMock()
        mock_pip.returncode = 1
        mock_pip.stdout = ""

        with patch("subprocess.run", return_value=mock_pip):
            with patch("shutil.which", return_value=None):
                with patch.object(detector, "_check_common_paths", return_value=None):
                    result = detect_mineru()

        assert result["installed"] is False
        assert result["version"] is None
        assert result["path"] is None

    def test_pip_installed_but_not_on_path(self):
        """pip knows the version but magic-pdf isn't on PATH or common dirs."""
        mock_pip = MagicMock()
        mock_pip.returncode = 0
        mock_pip.stdout = "Name: mineru\nVersion: 1.0.0\nLocation: /opt\n"

        with patch("subprocess.run", return_value=mock_pip):
            with patch("shutil.which", return_value=None):
                with patch.object(detector, "_check_common_paths", return_value=None):
                    result = detect_mineru()

        assert result["installed"] is True
        assert result["version"] == "1.0.0"
        assert result["path"] is None

    def test_found_on_common_path_but_no_pip(self):
        """magic-pdf found in common path, but pip show fails."""
        mock_pip = MagicMock()
        mock_pip.returncode = 1
        mock_pip.stdout = ""

        with patch("subprocess.run", return_value=mock_pip):
            with patch("shutil.which", return_value=None):
                with patch.object(detector, "_check_common_paths", return_value="/home/user/.local/bin/magic-pdf"):
                    result = detect_mineru()

        assert result["installed"] is True
        assert result["version"] is None
        assert result["path"] == "/home/user/.local/bin/magic-pdf"

    def test_result_structure(self):
        """Return dict always has the three expected keys."""
        mock_pip = MagicMock()
        mock_pip.returncode = 1
        mock_pip.stdout = ""

        with patch("subprocess.run", return_value=mock_pip):
            with patch("shutil.which", return_value=None):
                with patch.object(detector, "_check_common_paths", return_value=None):
                    result = detect_mineru()

        assert set(result.keys()) == {"installed", "path", "version"}
        assert isinstance(result["installed"], bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
