"""Platform detection utilities for paper-reader skill.

Provides functions to detect the current OS, Linux distribution,
and whether the process is running under Windows Subsystem for Linux.
"""

import logging
import platform
import re
import subprocess
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
    """Returns: 'linux', 'macos', 'windows', or 'unknown'"""
    return detect_platform().platform


def get_linux_distro() -> str | None:
    """Returns: 'ubuntu', 'debian', 'fedora', etc. or None"""
    # Only return distro on Linux systems
    if get_platform() != "linux":
        return None
    return detect_platform().distro


def is_wsl() -> bool:
    """Returns: True if running under WSL"""
    return detect_platform().is_wsl


def detect_platform() -> PlatformInfo:
    """Comprehensive platform detection.

    Returns:
        PlatformInfo with all detected information.
    """
    # Detect base platform
    system = platform.system()
    if system == "Linux":
        base_platform = "linux"
    elif system == "Darwin":
        base_platform = "macos"
    elif system == "Windows":
        base_platform = "windows"
    else:
        base_platform = sys.platform if sys.platform else "unknown"

    result = PlatformInfo(platform=base_platform)

    # Platform-specific detection
    if result.is_linux:
        _detect_linux_details(result)
        _detect_wsl(result)
    elif result.is_macos:
        _detect_macos_version(result)
    elif result.is_windows:
        _detect_windows_shell(result)
        result.windows_version = _get_windows_version()

    return result


def _detect_linux_details(info: PlatformInfo) -> None:
    """Detect Linux distribution and version."""
    # Method 1: Parse /etc/os-release (primary)
    os_release_path = Path("/etc/os-release")
    if os_release_path.exists():
        try:
            content = os_release_path.read_text(encoding="utf-8")
            lines = {}
            for line in content.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    lines[key] = value.strip('"')

            info.distro = lines.get("ID", "").lower() or None
            info.distro_version = lines.get("VERSION_ID") or None
        except OSError:
            pass

    # Method 2: Try /etc/*-release for other distros
    if not info.distro:
        fallback_files = {
            "/etc/redhat-release": "rhel",
            "/etc/centos-release": "centos",
            "/etc/debian_version": "debian",
            "/etc/arch-release": "arch",
            "/etc/lsb-release": "ubuntu",
        }
        for file_path, distro_name in fallback_files.items():
            if Path(file_path).exists():
                info.distro = distro_name
                break


def _detect_wsl(info: PlatformInfo) -> None:
    """Detect WSL version (1 or 2)."""
    import os

    # Check /proc/version for Microsoft/WSL
    try:
        version_text = Path("/proc/version").read_text(encoding="utf-8").lower()
        if "microsoft" in version_text or "wsl" in version_text:
            info.is_wsl = True

            # Determine WSL version
            if "wsl2" in version_text or "microsoft-standard-wsl2" in version_text:
                info.wsl_version = 2
            else:
                info.wsl_version = 1
    except OSError:
        pass

    # Check WSL_DISTRO_NAME environment variable
    wsl_distro = os.environ.get("WSL_DISTRO_NAME")
    if wsl_distro:
        info.is_wsl = True
        if info.wsl_version is None:
            info.wsl_version = 2

    # Check WSL_INTEROP (available in WSL2)
    if os.environ.get("WSL_INTEROP"):
        info.wsl_version = 2


def _detect_macos_version(info: PlatformInfo) -> None:
    """Detect macOS version."""
    try:
        version_str, _, machine = platform.mac_ver()
        if version_str:
            parts = version_str.split(".")
            info.macos_version = tuple(int(p) for p in parts[:3])
    except (OSError, ValueError):
        pass


def _detect_windows_shell(info: PlatformInfo) -> None:
    """Detect Windows shell environment (PowerShell, CMD, PowerShell Core)."""
    import os

    psmodule_path = os.environ.get("PSModulePath", "")
    prompt = os.environ.get("PROMPT", "")
    psversiontable = os.environ.get("PSVersionTable", "")
    psedition = os.environ.get("PSEdition", "")

    if psversiontable or psedition:
        if "PowerShell\\7" in psmodule_path or "PowerShell/7" in psmodule_path:
            info.shell = "pwsh"
            info.shell_version = _get_pwsh_version()
        else:
            info.shell = "powershell"
            info.shell_version = _get_powershell_version()
    elif prompt:
        info.shell = "cmd"
    else:
        info.shell = "unknown"


def _get_powershell_version() -> str | None:
    """Get Windows PowerShell version."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _get_pwsh_version() -> str | None:
    """Get PowerShell Core version."""
    try:
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _get_windows_version() -> str | None:
    """Get Windows version/build number."""
    try:
        result = subprocess.run(
            ["cmd", "/c", "ver"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            match = re.search(r"Version\s+([\d.]+)", result.stdout)
            if match:
                return match.group(1)
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None
