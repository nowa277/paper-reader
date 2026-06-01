"""Platform detection utilities for paper-reader skill.

Provides functions to detect the current OS, Linux distribution,
and whether the process is running under Windows Subsystem for Linux.
"""

import logging
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PlatformInfo:
    """Comprehensive platform information."""

    # Core platform
    platform: str = "unknown"
    distro: Optional[str] = None
    distro_version: Optional[str] = None

    # WSL detection
    is_wsl: bool = False
    wsl_version: Optional[int] = None

    # macOS specific
    macos_version: Optional[tuple] = None

    # Windows specific
    shell: Optional[str] = None
    shell_version: Optional[str] = None
    windows_version: Optional[str] = None

    @property
    def is_linux(self) -> bool:
        return self.platform == "linux"

    @property
    def is_macos(self) -> bool:
        return self.platform == "macos"

    @property
    def is_windows(self) -> bool:
        return self.platform == "windows"

    @property
    def is_unknown(self) -> bool:
        return self.platform == "unknown"

    @property
    def is_powershell(self) -> bool:
        return self.shell in ("powershell", "pwsh")

    @property
    def is_cmd(self) -> bool:
        return self.shell == "cmd"


def get_platform() -> str:
    """Return the current platform identifier.

    Returns:
        One of 'linux', 'macos', 'windows'.
    """
    system = platform.system()
    if system == "Linux":
        return "linux"
    if system == "Darwin":
        return "macos"
    if system == "Windows":
        return "windows"
    # Fallback to sys.platform for edge cases
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform == "win32":
        return "windows"
    logger.warning("Unrecognized platform: system=%s, sys.platform=%s", system, sys.platform)
    return "unknown"


def get_linux_distro() -> str | None:
    """Return the Linux distribution identifier.

    Parses /etc/os-release to extract the ID field (e.g. 'ubuntu',
    'debian', 'fedora', 'arch'). Falls back to the freedesktop
    os-release helper on Python 3.10+.

    Returns:
        Lowercase distro ID string (e.g. 'ubuntu'), or None if not on
        Linux or if the distro cannot be determined.
    """
    if get_platform() != "linux":
        return None

    # Strategy 1: parse /etc/os-release directly (widely available)
    try:
        content = Path("/etc/os-release").read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("ID="):
                distro_id = line.split("=", 1)[1].strip().strip('"')
                if distro_id:
                    return distro_id.lower()
    except OSError:
        logger.debug("/etc/os-release not readable")

    # Strategy 2: freedesktop helper (Python 3.10+)
    try:
        info = platform.freedesktop_os_release()  # type: ignore[attr-defined]
        distro_id = info.get("ID")
        if distro_id:
            return distro_id.lower()
    except (OSError, AttributeError):
        logger.debug("freedesktop_os_release() unavailable or failed")

    logger.warning("Could not determine Linux distribution")
    return None


def is_wsl() -> bool:
    """Detect whether the current environment is Windows Subsystem for Linux.

    Checks /proc/version for WSL indicators and also inspects the
    WSL_DISTRO_NAME environment variable.

    Returns:
        True if running under WSL, False otherwise.
    """
    if get_platform() != "linux":
        return False

    # Check /proc/version for Microsoft/WSL signatures
    try:
        version_text = Path("/proc/version").read_text(encoding="utf-8").lower()
        if "microsoft" in version_text or "wsl" in version_text:
            return True
    except OSError:
        logger.debug("/proc/version not readable")

    # Check WSL_DISTRO_NAME environment variable (set inside WSL2)
    import os
    if os.environ.get("WSL_DISTRO_NAME"):
        return True

    return False
