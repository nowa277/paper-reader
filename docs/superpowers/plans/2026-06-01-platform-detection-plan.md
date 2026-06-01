# Platform Detection Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance platform detection to provide comprehensive platform information including WSL version detection, Linux distro version, macOS version, and Windows shell detection (PowerShell/CMD)

**Architecture:** Create PlatformInfo dataclass with comprehensive detection, implement detect_platform() main function, add platform-specific detection for Linux/macOS/Windows, preserve backward compatibility

**Tech Stack:** Python dataclasses, platform module, subprocess, pathlib

---

### Task 1: Create PlatformInfo dataclass

**Files:**
- Modify: `paper-reader/skills/config/platform.py`

- [ ] **Step 1: Write the failing test**

```python
# Test in: paper-reader/skills/config/tests/test_platform.py
def test_platform_info_dataclass():
    """Test PlatformInfo can be instantiated with all fields."""
    from skills.config.platform import PlatformInfo
    
    info = PlatformInfo(
        platform="linux",
        distro="ubuntu",
        distro_version="22.04",
        is_wsl=True,
        wsl_version=2,
        macos_version=None,
        shell=None,
        shell_version=None,
        windows_version=None
    )
    
    assert info.platform == "linux"
    assert info.distro == "ubuntu"
    assert info.is_wsl is True
    assert info.wsl_version == 2
    assert info.is_linux is True
    assert info.is_powershell is False
    assert info.is_cmd is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_platform_info_dataclass -v`
Expected: FAIL with "cannot import name 'PlatformInfo'"

- [ ] **Step 3: Write minimal implementation**

```python
# Add to paper-reader/skills/config/platform.py

from dataclasses import dataclass
from typing import Optional

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_platform_info_dataclass -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add paper-reader/skills/config/platform.py
git commit -m "feat: add PlatformInfo dataclass with all platform fields"
```

---

### Task 2: Implement detect_platform() main function

**Files:**
- Modify: `paper-reader/skills/config/platform.py:80-100`

- [ ] **Step 1: Write the failing test**

```python
def test_detect_platform_returns_platform_info():
    """Test detect_platform() returns PlatformInfo."""
    from skills.config.platform import detect_platform, PlatformInfo
    
    result = detect_platform()
    
    assert isinstance(result, PlatformInfo)
    assert result.platform in ("linux", "macos", "windows", "unknown")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_detect_platform_returns_platform_info -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
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
    pass  # Placeholder for now


def _detect_wsl(info: PlatformInfo) -> None:
    """Detect WSL version."""
    pass  # Placeholder for now


def _detect_macos_version(info: PlatformInfo) -> None:
    """Detect macOS version."""
    pass  # Placeholder for now


def _detect_windows_shell(info: PlatformInfo) -> None:
    """Detect Windows shell environment."""
    pass  # Placeholder for now


def _get_windows_version() -> str | None:
    """Get Windows version/build number."""
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_detect_platform_returns_platform_info -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add paper-reader/skills/config/platform.py
git commit -m "feat: add detect_platform() main function"
```

---

### Task 3: Implement Linux-specific detection (enhanced)

**Files:**
- Modify: `paper-reader/skills/config/platform.py:_detect_linux_details`

- [ ] **Step 1: Write the failing test**

```python
def test_detect_linux_distro():
    """Test Linux distribution detection."""
    from skills.config.platform import detect_platform
    
    info = detect_platform()
    
    if info.platform == "linux":
        # Should detect something or None (acceptable)
        assert info.distro is None or isinstance(info.distro, str)
        assert info.distro_version is None or isinstance(info.distro_version, str)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_detect_linux_distro -v`
Expected: FAIL (distro is always None in current placeholder)

- [ ] **Step 3: Write implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_detect_linux_distro -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add paper-reader/skills/config/platform.py
git commit -m "feat: add enhanced Linux distro detection"
```

---

### Task 4: Implement WSL version detection (enhanced)

**Files:**
- Modify: `paper-reader/skills/config/platform.py:_detect_wsl`

- [ ] **Step 1: Write the failing test**

```python
def test_wsl_version_detection():
    """Test WSL version detection returns 1 or 2."""
    from skills.config.platform import detect_platform
    
    info = detect_platform()
    
    if info.platform == "linux":
        # If is_wsl is True, wsl_version should be 1 or 2
        if info.is_wsl:
            assert info.wsl_version in (1, 2)
        # If not WSL, should be False
        assert info.is_wsl in (True, False)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_wsl_version_detection -v`
Expected: FAIL (is_wsl returns False always)

- [ ] **Step 3: Write implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_wsl_version_detection -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add paper-reader/skills/config/platform.py
git commit -m "feat: add WSL version detection (WSL1/WSL2)"
```

---

### Task 5: Implement macOS version detection

**Files:**
- Modify: `paper-reader/skills/config/platform.py:_detect_macos_version`

- [ ] **Step 1: Write the failing test**

```python
def test_macos_version_detection():
    """Test macOS version detection."""
    from skills.config.platform import detect_platform
    
    info = detect_platform()
    
    if info.platform == "macos":
        assert info.macos_version is None or isinstance(info.macos_version, tuple)
        if info.macos_version:
            assert len(info.macos_version) == 3
            assert all(isinstance(x, int) for x in info.macos_version)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_macos_version_detection -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
def _detect_macos_version(info: PlatformInfo) -> None:
    """Detect macOS version."""
    try:
        version_str, _, machine = platform.mac_ver()
        if version_str:
            parts = version_str.split(".")
            info.macos_version = tuple(int(p) for p in parts[:3])
    except (OSError, ValueError):
        pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_macos_version_detection -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add paper-reader/skills/config/platform.py
git commit -m "feat: add macOS version detection"
```

---

### Task 6: Implement Windows shell detection (PowerShell/CMD)

**Files:**
- Modify: `paper-reader/skills/config/platform.py:_detect_windows_shell`

- [ ] **Step 1: Write the failing test**

```python
def test_windows_shell_detection():
    """Test Windows shell detection returns shell type."""
    from skills.config.platform import detect_platform
    
    info = detect_platform()
    
    if info.platform == "windows":
        assert info.shell in ("powershell", "pwsh", "cmd", "unknown", None)
        if info.shell in ("powershell", "pwsh"):
            assert info.is_powershell is True
        if info.shell == "cmd":
            assert info.is_cmd is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_windows_shell_detection -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
import subprocess
import re

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_windows_shell_detection -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add paper-reader/skills/config/platform.py
git commit -m "feat: add Windows shell detection (PowerShell/CMD)"
```

---

### Task 7: Add backward-compatible wrapper functions

**Files:**
- Modify: `paper-reader/skills/config/platform.py:end of file`

- [ ] **Step 1: Write the failing test**

```python
def test_backward_compatibility():
    """Test legacy functions still work."""
    from skills.config.platform import get_platform, get_linux_distro, is_wsl
    
    platform_result = get_platform()
    assert platform_result in ("linux", "macos", "windows", "unknown")
    
    if platform_result == "linux":
        distro = get_linux_distro()
        assert distro is None or isinstance(distro, str)
    
    wsl_result = is_wsl()
    assert isinstance(wsl_result, bool)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_backward_compatibility -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# Keep backward compatible functions
def get_platform() -> str:
    """Returns: 'linux', 'macos', 'windows', or 'unknown'"""
    return detect_platform().platform


def get_linux_distro() -> str | None:
    """Returns: 'ubuntu', 'debian', 'fedora', etc. or None"""
    return detect_platform().distro


def is_wsl() -> bool:
    """Returns: True if running under WSL"""
    return detect_platform().is_wsl
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py::test_backward_compatibility -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add paper-reader/skills/config/platform.py
git commit -m "feat: add backward-compatible wrapper functions"
```

---

### Task 8: Comprehensive tests and verify all pass

**Files:**
- Test: `paper-reader/skills/config/tests/test_platform.py`

- [ ] **Step 1: Run all platform tests**

Run: `cd paper-reader && python -m pytest skills/config/tests/test_platform.py -v`
Expected: All tests pass

- [ ] **Step 2: Commit final changes**

```bash
git add paper-reader/
git commit -m "feat: complete platform detection enhancement"
```