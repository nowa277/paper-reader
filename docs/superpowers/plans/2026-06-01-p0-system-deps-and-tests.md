# P0 系统依赖检测 + 单元测试框架 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现系统依赖检测模块 + 统一测试框架，提升测试覆盖率到 80%+

**Architecture:**
- `skills/config/system_deps.py` - 系统依赖检测模块，使用 dataclass 定义依赖项，shutil.which() 检测
- `tests/conftest.py` - 统一 fixtures（temp_config_dir, mock_home, system_deps）
- 各模块独立测试文件

**Tech Stack:** Python shutil, subprocess, dataclass, pytest, pytest-cov

---

## 文件结构

```
paper-reader/
├── skills/config/
│   ├── __init__.py           # 更新：导出 system_deps
│   ├── platform.py           # 现有
│   ├── system_deps.py        # 新建
│   └── config_manager.py     # 现有
├── tests/
│   ├── conftest.py           # 更新：添加统一 fixtures
│   └── skills/config/
│       ├── test_platform.py        # 现有
│       ├── test_system_deps.py     # 新建
│       └── test_config_manager.py # 新建
```

---

## Task 1: 创建 system_deps.py

**Files:**
- Create: `skills/config/system_deps.py`
- Test: `tests/skills/config/test_system_deps.py`

- [ ] **Step 1: 创建 system_deps.py 骨架**

```python
"""System dependency detection for paper-reader skill.

Detects external tools: curl, pandoc, tesseract.
"""

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class Dependency:
    """System dependency definition."""
    name: str           # Display name
    command: str        # Command to check
    required: bool      # Whether this is required
    version_args: Optional[list[str]] = None  # Args for version check


SYSTEM_DEPS = {
    "curl": Dependency("curl", "curl", True, ["--version"]),
    "pandoc": Dependency("Pandoc", "pandoc", True, ["--version"]),
    "tesseract": Dependency("Tesseract OCR", "tesseract", False, ["--version"]),
}


def check_dependency(dep_id: str) -> tuple[bool, Optional[str]]:
    """Check if a dependency is installed.

    Args:
        dep_id: Key in SYSTEM_DEPS

    Returns:
        (is_installed, version_info_or_error_message)
    """
    if dep_id not in SYSTEM_DEPS:
        return False, f"Unknown dependency: {dep_id}"

    dep = SYSTEM_DEPS[dep_id]
    path = shutil.which(dep.command)
    if path is None:
        return False, f"{dep.name} not found in PATH"

    if dep.version_args:
        try:
            result = subprocess.run(
                [dep.command] + dep.version_args,
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return True, version_line[:100]
            return True, "Installed (version check failed)"
        except (OSError, subprocess.TimeoutExpired):
            return True, "Installed (version check failed)"

    return True, path


def check_all_dependencies() -> dict[str, dict]:
    """Check all system dependencies.

    Returns:
        {dep_id: {"installed": bool, "version": str, "required": bool}}
    """
    results = {}
    for dep_id in SYSTEM_DEPS:
        installed, version = check_dependency(dep_id)
        results[dep_id] = {
            "installed": installed,
            "version": version,
            "required": SYSTEM_DEPS[dep_id].required,
        }
    return results


def get_missing_required() -> list[str]:
    """Return list of missing required dependency IDs."""
    missing = []
    for dep_id, dep in SYSTEM_DEPS.items():
        if dep.required:
            installed, _ = check_dependency(dep_id)
            if not installed:
                missing.append(dep_id)
    return missing


def get_installation_instructions(dep_id: str) -> str:
    """Get installation instructions for a dependency."""
    instructions = {
        "curl": "Ubuntu/Debian: sudo apt install curl",
        "pandoc": "Ubuntu/Debian: sudo apt install pandoc",
        "tesseract": "Ubuntu/Debian: sudo apt install tesseract-ocr",
    }
    return instructions.get(dep_id, f"Install {dep_id} using your system's package manager")
```

- [ ] **Step 2: 运行查看现有测试结构**

Run: `ls -la tests/skills/config/`
Expected: test_platform.py exists

- [ ] **Step 3: 创建 test_system_deps.py**

```python
"""Tests for system dependency detection."""

import pytest
from unittest.mock import patch
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
```

- [ ] **Step 4: 运行测试验证失败（预期）**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/skills/config/test_system_deps.py -v`
Expected: 多个测试失败（因为 system_deps.py 不在 skills.config 路径下）

- [ ] **Step 5: 更新 skills/config/__init__.py**

```python
"""Config module for paper-reader skill."""

from skills.config.platform import (
    get_platform,
    get_linux_distro,
    is_wsl,
    detect_platform,
    PlatformInfo,
)
from skills.config.config_manager import ConfigManager

__all__ = [
    "get_platform",
    "get_linux_distro",
    "is_wsl",
    "detect_platform",
    "PlatformInfo",
    "ConfigManager",
]
```

- [ ] **Step 6: 添加 system_deps 到 __init__.py**

```python
"""Config module for paper-reader skill."""

from skills.config.platform import (
    get_platform,
    get_linux_distro,
    is_wsl,
    detect_platform,
    PlatformInfo,
)
from skills.config.config_manager import ConfigManager
from skills.config.system_deps import (
    SYSTEM_DEPS,
    check_dependency,
    check_all_dependencies,
    get_missing_required,
    get_installation_instructions,
)

__all__ = [
    "get_platform",
    "get_linux_distro",
    "is_wsl",
    "detect_platform",
    "PlatformInfo",
    "ConfigManager",
    "SYSTEM_DEPS",
    "check_dependency",
    "check_all_dependencies",
    "get_missing_required",
    "get_installation_instructions",
]
```

- [ ] **Step 7: 更新 test_system_deps.py 导入路径**

```python
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
```

- [ ] **Step 8: 运行测试**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/skills/config/test_system_deps.py -v`
Expected: 全部 PASS

- [ ] **Step 9: 提交**

```bash
cd "/home/user/obsidian/AI/claude code/paper-reader"
git add skills/config/system_deps.py skills/config/__init__.py
git add tests/skills/config/test_system_deps.py
git commit -m "feat: add system dependency detection for curl, pandoc, tesseract

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: 更新 conftest.py 添加统一 fixtures

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: 更新 conftest.py**

```python
"""Pytest configuration and shared fixtures for paper-reader tests."""

import sys
from pathlib import Path

import pytest

# Ensure the paper-reader directory is in sys.path for imports
paper_reader_path = Path(__file__).parent.parent
if str(paper_reader_path) not in sys.path:
    sys.path.insert(0, str(paper_reader_path))


@pytest.fixture
def temp_config_dir(tmp_path):
    """Temporary config directory fixture.

    Creates a temporary ~/.paper-reader-style directory structure.
    """
    config_dir = tmp_path / ".paper-reader"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_home(tmp_path, monkeypatch):
    """Mock HOME directory for isolated testing.

    Sets HOME to a temp directory and returns the path.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


@pytest.fixture
def system_deps():
    """System dependencies checker fixture.

    Returns the SYSTEM_DEPS dict and check functions.
    """
    from skills.config import system_deps
    return {
        "deps": system_deps.SYSTEM_DEPS,
        "check": system_deps.check_dependency,
        "check_all": system_deps.check_all_dependencies,
        "get_missing": system_deps.get_missing_required,
    }
```

- [ ] **Step 2: 运行测试确保不破坏现有测试**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/skills/config/test_platform.py -v`
Expected: 全部 PASS

- [ ] **Step 3: 提交**

```bash
cd "/home/user/obsidian/AI/claude code/paper-reader"
git add tests/conftest.py
git commit -m "test: add unified pytest fixtures (temp_config_dir, mock_home, system_deps)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: 创建 test_config_manager.py

**Files:**
- Create: `tests/skills/config/test_config_manager.py`
- Test: `skills/config/config_manager.py`

- [ ] **Step 1: 创建 test_config_manager.py**

```python
"""Tests for ConfigManager."""

import json
import tempfile
from pathlib import Path

import pytest
from skills.config.config_manager import ConfigManager, DEFAULT_CONFIG


class TestConfigManagerInit:
    """Tests for ConfigManager initialization."""

    def test_loads_existing_config(self, temp_config_dir):
        """Existing config file is loaded."""
        config_file = temp_config_dir / "config.json"
        config_file.write_text(json.dumps({"version": "1.0", "test": "data"}))

        manager = ConfigManager(config_path=config_file)
        assert manager.get("test") == "data"

    def test_creates_default_if_missing(self, temp_config_dir):
        """Missing config file creates default."""
        config_file = temp_config_dir / "config.json"
        manager = ConfigManager(config_path=config_file)

        assert manager.get("version") == "1.0"
        assert config_file.exists()

    def test_creates_default_if_corrupted(self, temp_config_dir):
        """Corrupted config file resets to default."""
        config_file = temp_config_dir / "config.json"
        config_file.write_text("not valid json{")

        manager = ConfigManager(config_path=config_file)
        assert manager.get("version") == "1.0"


class TestConfigManagerGet:
    """Tests for ConfigManager.get method."""

    def test_get_simple_key(self, temp_config_dir):
        """Simple key returns value."""
        manager = ConfigManager(config_path=temp_config_dir / "c.json")
        assert manager.get("version") == "1.0"

    def test_get_nested_key(self, temp_config_dir):
        """Dotted key returns nested value."""
        manager = ConfigManager(config_path=temp_config_dir / "c.json")
        assert manager.get("mineru.installed") is False

    def test_get_missing_key_returns_default(self, temp_config_dir):
        """Missing key returns provided default."""
        manager = ConfigManager(config_path=temp_config_dir / "c.json")
        assert manager.get("nonexistent", "default") == "default"

    def test_get_missing_no_default_returns_none(self, temp_config_dir):
        """Missing key without default returns None."""
        manager = ConfigManager(config_path=temp_config_dir / "c.json")
        assert manager.get("nonexistent") is None


class TestConfigManagerSet:
    """Tests for ConfigManager.set method."""

    def test_set_simple_key(self, temp_config_dir):
        """Setting simple key persists and returns on reload."""
        config_file = temp_config_dir / "c.json"
        manager = ConfigManager(config_path=config_file)

        manager.set("test_key", "test_value")
        assert manager.get("test_key") == "test_value"

        # Verify persisted
        manager2 = ConfigManager(config_path=config_file)
        assert manager2.get("test_key") == "test_value"

    def test_set_nested_key(self, temp_config_dir):
        """Setting dotted key creates intermediate dicts."""
        config_file = temp_config_dir / "c.json"
        manager = ConfigManager(config_path=config_file)

        manager.set("new_section.nested_key", "nested_value")
        assert manager.get("new_section.nested_key") == "nested_value"


class TestConfigManagerGetAll:
    """Tests for ConfigManager.get_all method."""

    def test_returns_copy_of_config(self, temp_config_dir):
        """get_all returns a copy, not the original."""
        manager = ConfigManager(config_path=temp_config_dir / "c.json")
        all_config = manager.get_all()

        assert isinstance(all_config, dict)
        assert "version" in all_config


class TestConfigManagerSave:
    """Tests for ConfigManager.save method."""

    def test_save_creates_directory(self, temp_config_dir):
        """Save creates parent directory if missing."""
        config_file = temp_config_dir / "subdir" / "config.json"
        manager = ConfigManager(config_path=config_file)

        manager.set("test", "value")
        assert config_file.exists()

    def test_save_is_called_on_init_for_default(self, temp_config_dir):
        """Init with missing file calls save()."""
        config_file = temp_config_dir / "c.json"
        manager = ConfigManager(config_path=config_file)

        # DEFAULT_CONFIG has initialized_skills as empty list
        assert manager.get("initialized_skills") == []
```

- [ ] **Step 2: 运行测试**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/skills/config/test_config_manager.py -v`
Expected: 全部 PASS

- [ ] **Step 3: 提交**

```bash
cd "/home/user/obsidian/AI/claude code/paper-reader"
git add tests/skills/config/test_config_manager.py
git commit -m "test: add ConfigManager unit tests

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: 验证完整测试覆盖率

**Files:**
- None (仅运行测试)

- [ ] **Step 1: 运行完整测试套件**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/ -v --tb=short`
Expected: 全部 PASS

- [ ] **Step 2: 运行覆盖率检查**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/ --cov=skills --cov-report=term-missing`
Expected: 整体覆盖率 ≥ 70%，重点模块 ≥ 80%

- [ ] **Step 3: 最终提交（如有改进）**

```bash
cd "/home/user/obsidian/AI/claude code/paper-reader"
git add -A
git commit -m "test: expand test coverage for config and system_deps modules

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 验收标准

- [ ] `python3 -m pytest tests/skills/config/test_system_deps.py` 全部通过
- [ ] `python3 -m pytest tests/skills/config/test_config_manager.py` 全部通过
- [ ] 整体测试覆盖率 ≥ 70%
- [ ] 所有提交已推送到 git
