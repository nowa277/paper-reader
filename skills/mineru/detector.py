"""MinerU installation detector.

Checks whether MinerU (magic-pdf CLI) is installed and locates
its executable path and version.
"""

import logging
import shutil
import subprocess
import sys
from pathlib import Path

from skills.config.platform import get_platform

logger = logging.getLogger(__name__)

# Common installation paths per platform
_COMMON_PATHS: dict[str, list[str]] = {
    "linux": [
        "~/.local/bin/",
        "/usr/local/bin/",
    ],
    "macos": [
        "~/Library/Python/*/bin/",
        "/usr/local/bin/",
    ],
    "windows": [
        r"C:\Python*\Scripts\\",
    ],
}

_CLI_NAME = "magic-pdf"


def _run_pip_show() -> tuple[str | None, str | None]:
    """Run ``pip3 show mineru`` (then ``pip show`` as fallback) and extract version and location.

    Returns:
        (version, location) — either may be None if pip doesn't find the package.
    """
    for pip_cmd in ("pip3", "pip"):
        try:
            result = subprocess.run(
                [pip_cmd, "show", "mineru"],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired):
            logger.debug("%s show mineru failed or timed out", pip_cmd)
            continue

        if result.returncode != 0:
            continue

        version = None
        location = None
        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                version = line.split(":", 1)[1].strip()
            elif line.startswith("Location:"):
                location = line.split(":", 1)[1].strip()

        return version, location

    return None, None


def _check_which() -> str | None:
    """Find ``magic-pdf`` on PATH via :func:`shutil.which`.

    On Windows, also checks for ``magic-pdf.exe``.

    Returns:
        Absolute path to the executable, or None.
    """
    found = shutil.which(_CLI_NAME)
    if found:
        return str(Path(found).resolve())
    # On Windows, shutil.which may not find .exe variants in some cases
    if sys.platform == "win32":
        found = shutil.which(_CLI_NAME + ".exe")
        if found:
            return str(Path(found).resolve())
    return None


def _check_common_paths() -> str | None:
    """Search platform-specific common installation directories.

    Returns:
        Absolute path to the first ``magic-pdf`` found, or None.
    """
    current_platform = get_platform()
    is_windows = current_platform == "windows"
    paths = _COMMON_PATHS.get(current_platform, [])

    # Candidate names: magic-pdf and (on Windows) magic-pdf.exe
    cli_names = [_CLI_NAME]
    if is_windows:
        cli_names.append(_CLI_NAME + ".exe")

    for pattern in paths:
        expanded = Path(pattern).expanduser()

        # If the pattern has no glob, check directly
        if "*" not in pattern:
            for name in cli_names:
                candidate = expanded / name
                if candidate.is_file():
                    return str(candidate.resolve())
            continue

        # Glob using the full pattern from the expanded root.
        # For patterns like ~/Library/Python/*/bin/ we need to find an
        # anchor directory that exists and glob from there.
        # Strategy: walk up from the expanded path to find the first
        # non-glob ancestor, then glob the remaining relative pattern.
        parts = expanded.parts
        # Find the first part that contains a glob wildcard
        first_glob_idx = None
        for i, part in enumerate(parts):
            if "*" in part:
                first_glob_idx = i
                break

        if first_glob_idx is None:
            # Shouldn't happen since "*" is in the pattern string
            continue

        # The anchor is the directory before the first glob part
        anchor = Path(*parts[:first_glob_idx])
        # The relative glob pattern is everything from the first glob part onward
        rel_pattern = str(Path(*parts[first_glob_idx:]))

        if not anchor.is_dir():
            continue

        for matched_dir in sorted(anchor.glob(rel_pattern)):
            if not matched_dir.is_dir():
                continue
            for name in cli_names:
                candidate = matched_dir / name
                if candidate.is_file():
                    return str(candidate.resolve())

    return None


def detect_mineru() -> dict:
    """Detect whether MinerU is installed.

    Checks in order:
      1. ``pip3 show mineru`` (falls back to ``pip``) for version info
      2. ``shutil.which('magic-pdf')`` for the CLI on PATH
      3. Platform-specific common paths as a fallback

    Returns:
        dict with keys:
          - ``installed`` (bool): whether MinerU was found
          - ``path`` (str | None): resolved path to ``magic-pdf``
          - ``version`` (str | None): installed version string
    """
    version, _location = _run_pip_show()

    # Find the executable — which first, then common paths
    path = _check_which() or _check_common_paths()

    installed = path is not None or version is not None

    return {
        "installed": installed,
        "path": path,
        "version": version,
    }
