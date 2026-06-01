# Platform Detection Enhancement - Design Document

**Created:** 2026-06-01  
**Phase:** Platform Detection Improvements  
**Approach:** Enhanced PlatformInfo dataclass

---

## Objective

Enhance platform detection to provide comprehensive platform information including WSL version detection, Linux distro version, and macOS version support.

---

## Design Decision

**Chosen Approach:** PlatformInfo dataclass with comprehensive detection

**Rationale:**
- Type-safe with IDE autocomplete support
- Backward compatible (existing functions preserved)
- Extensible for future enhancements
- Clean and simple implementation

---

## New Data Structure

### PlatformInfo Dataclass

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class PlatformInfo:
    """Comprehensive platform information."""
    
    # Core platform
    platform: str                    # 'linux' | 'macos' | 'windows' | 'unknown'
    distro: Optional[str] = None      # 'ubuntu', 'debian', 'fedora', etc.
    distro_version: Optional[str] = None  # e.g., '22.04'
    
    # WSL detection
    is_wsl: bool = False
    wsl_version: Optional[int] = None  # 1 or 2
    
    # macOS specific
    macos_version: Optional[tuple] = None  # (13, 2, 0) for Ventura
    
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
```

---

## Core Functions

### detect_platform() - Main Entry Point

```python
def detect_platform() -> PlatformInfo:
    """Comprehensive platform detection.
    
    Performs all platform detection in a single pass
    for efficiency.
    
    Returns:
        PlatformInfo with all detected information.
    """
    # 1. Detect base platform
    base_platform = _detect_base_platform()
    
    # 2. Initialize result
    result = PlatformInfo(platform=base_platform)
    
    # 3. Platform-specific detection
    if result.is_linux:
        _detect_linux_details(result)
        _detect_wsl(result)
    elif result.is_macos:
        _detect_macos_version(result)
    # Windows - no additional detection needed
    
    return result
```

### Platform-Specific Detection

#### Linux Detection

```python
def _detect_linux_details(info: PlatformInfo) -> None:
    """Detect Linux distribution and version."""
    
    # Method 1: Parse /etc/os-release (primary)
    os_release_path = Path("/etc/os-release")
    if os_release_path.exists():
        content = os_release_path.read_text(encoding="utf-8")
        lines = dict(line.split("=", 1) for line in content.splitlines() if "=" in line)
        
        info.distro = lines.get("ID", "").strip('"').lower() or None
        info.distro_version = lines.get("VERSION_ID", "").strip('"') or None
    
    # Method 2: Try /etc/*-release for other distros
    if not info.distro:
        for pattern in ["/etc/redhat-release", "/etc/centos-release", 
                       "/etc/debian_version", "/etc/arch-release"]:
            if Path(pattern).exists():
                # Extract distro name from file
                ...
```

#### WSL Detection (Enhanced)

```python
def _detect_wsl(info: PlatformInfo) -> None:
    """Detect WSL version (1 or 2)."""
    
    # Check /proc/version for Microsoft/WSL
    try:
        version_text = Path("/proc/version").read_text(encoding="utf-8").lower()
        if "microsoft" in version_text or "wsl" in version_text:
            info.is_wsl = True
            
            # Determine WSL version
            # WSL2 has "microsoft-standard-WSL2"
            if "wsl2" in version_text or "microsoft-standard-wsl2" in version_text:
                info.wsl_version = 2
            else:
                info.wsl_version = 1
    except OSError:
        pass
    
    # Also check WSL_DISTRO_NAME environment variable
    wsl_distro = os.environ.get("WSL_DISTRO_NAME")
    if wsl_distro:
        info.is_wsl = True
        # WSL2 sets this variable, WSL1 may not
    
    # Check WSL_INTEROP (available in WSL2)
    if os.environ.get("WSL_INTEROP"):
        info.wsl_version = 2
```

#### macOS Version Detection

```python
def _detect_macos_version(info: PlatformInfo) -> None:
    """Detect macOS version."""
    import platform
    
    # platform.mac_ver() returns (version, (major, minor, patch), machine)
    try:
        version_str, _, machine = platform.mac_ver()
        if version_str:
            # Parse "13.2.0" -> (13, 2, 0)
            parts = version_str.split(".")
            info.macos_version = tuple(int(p) for p in parts[:3])
    except Exception:
        pass
```

---

## Backward Compatibility

Preserve existing functions:

```python
# Legacy functions - still work
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

---

## Edge Cases Handled

| Case | Handling |
|------|----------|
| Unknown platform | Returns `platform="unknown"`, all other fields None |
| Linux without /etc/os-release | Tries fallback methods, returns None for distro |
| WSL on older kernel | Falls back to `WSL_DISTRO_NAME` check |
| macOS without version | Returns None for macos_version |
| Windows WSL | Reports WSL version correctly |

---

## File Changes

**Modified:**
- `paper-reader/skills/config/platform.py`

**Testing:**
- Add tests for new WSL version detection
- Add tests for distro version parsing
- Add tests for macOS version detection
- Verify backward compatibility

---

## Implementation Order

1. Create PlatformInfo dataclass
2. Implement `detect_platform()` main function
3. Implement Linux-specific detection
4. Implement WSL version detection
5. Implement macOS version detection
6. Add backward-compatible wrapper functions
7. Add comprehensive tests
8. Verify all existing tests still pass