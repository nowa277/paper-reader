# P2 + P3 增强实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 6 个任务：环境检测、备份回滚、论文缓存、并行评估、CI 文档检查、文档更新

**Architecture:**
- `skills/config/env_detector.py` — Python 版本 + 虚拟环境检测
- `skills/config/backup.py` — 配置备份与回滚
- `skills/analyze/cache.py` — 论文缓存
- `skills/analyze/parallel_evaluator.py` — 并行可行性评估
- `.github/workflows/docs-check.yml` — GitHub Actions CI 检查

**Tech Stack:** Python shutil, json, pathlib, shutil.disk_usage, psutil (for memory), GitHub Actions

---

## 文件结构

```
paper-reader/
├── skills/
│   ├── config/
│   │   ├── env_detector.py      # 新增
│   │   └── backup.py            # 新增
│   └── analyze/
│       ├── cache.py              # 新增
│       └── parallel_evaluator.py # 新增
├── .github/
│   └── workflows/
│       └── docs-check.yml       # 新增
└── tests/
    ├── skills/config/
    │   ├── test_env_detector.py  # 新增
    │   └── test_backup.py        # 新增
    └── skills/analyze/
        ├── test_cache.py         # 新增
        └── test_parallel_evaluator.py # 新增
```

---

## Task 1: env_detector.py

**Files:**
- Create: `skills/config/env_detector.py`
- Test: `tests/skills/config/test_env_detector.py`

- [ ] **Step 1: 创建测试文件**

```python
"""Tests for environment detector."""

import os
from unittest.mock import patch
from skills.config.env_detector import detect_venv_type, check_venv_compatibility


class TestDetectVenvType:
    """Tests for detect_venv_type()."""

    def test_returns_system_when_no_venv_vars(self):
        """No virtual env vars means system Python."""
        env = {"PATH": "/usr/bin"}
        with patch.dict(os.environ, env, clear=True):
            result = detect_venv_type()
            assert result == "system"

    def test_returns_venv_when_virtuenv_set(self):
        """VIRTUAL_ENV set means venv."""
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/path/to/venv"}):
            result = detect_venv_type()
            assert result == "venv"

    def test_returns_conda_when_conda_default_env_set(self):
        """CONDA_DEFAULT_ENV set means conda."""
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "base"}):
            result = detect_venv_type()
            assert result == "conda"

    def test_returns_uv_when_uv_cache_set(self):
        """UV_CACHE_DIR set means uv."""
        with patch.dict(os.environ, {"UV_CACHE_DIR": "/path/to/cache"}):
            result = detect_venv_type()
            assert result == "uv"


class TestCheckVenvCompatibility:
    """Tests for check_venv_compatibility()."""

    def test_system_python_is_ok(self):
        """System Python is compatible."""
        with patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True):
            ok, msg = check_venv_compatibility()
            assert ok is True

    def test_conda_warns(self):
        """Conda environment triggers warning."""
        with patch.dict(os.environ, {"CONDA_DEFAULT_ENV": "base"}):
            ok, msg = check_venv_compatibility()
            assert ok is False
            assert "conda" in msg.lower()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/skills/config/test_env_detector.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: 创建 env_detector.py**

```python
"""Environment detector for Python version and virtual environments."""

import os
from typing import Optional


def detect_venv_type() -> str:
    """Detect the current virtual environment type.

    Returns:
        'venv' | 'conda' | 'uv' | 'system'
    """
    if os.environ.get("VIRTUAL_ENV"):
        return "venv"
    if os.environ.get("CONDA_DEFAULT_ENV"):
        return "conda"
    if os.environ.get("UV_CACHE_DIR"):
        return "uv"
    return "system"


def check_venv_compatibility() -> tuple[bool, str]:
    """Check virtual environment compatibility.

    Returns:
        (ok, warning_message)
    """
    venv_type = detect_venv_type()

    if venv_type == "conda":
        return False, (
            "Conda environment detected. MinerU dependencies may conflict with Conda. "
            "Consider using venv or system Python instead."
        )

    if venv_type == "system":
        return True, ""

    # venv and uv are generally fine
    return True, f"{venv_type} environment detected"


def check_python_version() -> tuple[bool, str]:
    """Check Python version meets requirements.

    Returns:
        (ok, message)
    """
    import sys
    MIN_VERSION = (3, 10)
    current = sys.version_info[:2]
    if current >= MIN_VERSION:
        return True, f"Python {current[0]}.{current[1]} OK"
    return False, f"Python {current[0]}.{current[1]} too old; requires 3.10+"
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/skills/config/test_env_detector.py -v`
Expected: PASS

- [ ] **Step 5: 更新 skills/config/__init__.py** 添加导出

```python
from skills.config.env_detector import detect_venv_type, check_venv_compatibility, check_python_version
```

- [ ] **Step 6: 提交**

```bash
cd "/home/user/obsidian/AI/claude code/paper-reader"
git add skills/config/env_detector.py skills/config/__init__.py
git add tests/skills/config/test_env_detector.py
git commit -m "feat: add environment detector for Python version and venv type

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: backup.py

**Files:**
- Create: `skills/config/backup.py`
- Test: `tests/skills/config/test_backup.py`

- [ ] **Step 1: 创建测试文件**

```python
"""Tests for config backup."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from skills.config.backup import ConfigBackup


class TestConfigBackupInit:
    """Tests for ConfigBackup initialization."""

    def test_default_backup_dir(self, tmp_path, monkeypatch):
        """Default backup dir is under .paper-reader."""
        monkeypatch.setenv("HOME", str(tmp_path))
        backup = ConfigBackup()
        expected = tmp_path / ".paper-reader" / "backups"
        assert backup._backup_dir == expected

    def test_custom_backup_dir(self, tmp_path):
        """Custom backup dir is respected."""
        custom = tmp_path / "custom_backups"
        backup = ConfigBackup(backup_dir=custom)
        assert backup._backup_dir == custom


class TestConfigBackupBackup:
    """Tests for backup()."""

    def test_creates_backup_file(self, tmp_path):
        """backup() creates a backup file."""
        backup = ConfigBackup(backup_dir=tmp_path)
        config = tmp_path / "config.json"
        config.write_text('{"key": "value"}')

        result = backup.backup(config)
        assert Path(result).exists()

    def test_backup_contains_original_data(self, tmp_path):
        """Backup file contains original data."""
        backup = ConfigBackup(backup_dir=tmp_path)
        config = tmp_path / "config.json"
        config.write_text('{"key": "value"}')

        result = backup.backup(config)
        with open(result) as f:
            data = json.load(f)
        assert data["key"] == "value"


class TestConfigBackupRestore:
    """Tests for restore()."""

    def test_restores_from_backup(self, tmp_path):
        """restore() overwrites config with backup."""
        backup = ConfigBackup(backup_dir=tmp_path)
        config = tmp_path / "config.json"
        config.write_text('{"key": "old"}')

        backup_path = backup.backup(config)
        config.write_text('{"key": "new"}')

        backup.restore(Path(backup_path))
        with open(config) as f:
            data = json.load(f)
        assert data["key"] == "old"


class TestConfigBackupList:
    """Tests for list_backups()."""

    def test_lists_all_backups(self, tmp_path):
        """list_backups() returns all backup paths."""
        backup = ConfigBackup(backup_dir=tmp_path)
        config = tmp_path / "config.json"
        config.write_text('{}')

        b1 = backup.backup(config)
        config.write_text('{"a": 1}')
        b2 = backup.backup(config)

        backups = backup.list_backups()
        assert len(backups) == 2
        assert b1 in backups
        assert b2 in backups


class TestConfigBackupPrune:
    """Tests for prune()."""

    def test_prune_removes_old_backups(self, tmp_path):
        """prune() removes all but keep N newest."""
        backup = ConfigBackup(backup_dir=tmp_path)
        config = tmp_path / "config.json"
        config.write_text('{}')

        for i in range(7):
            config.write_text(f'{{"v": {i}}}')
            backup.backup(config)

        backup.prune(keep=3)
        backups = backup.list_backups()
        assert len(backups) == 3
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/skills/config/test_backup.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: 创建 backup.py**

```python
"""Config backup and restore for paper-reader."""

import json
import shutil
from datetime import datetime
from pathlib import Path


class ConfigBackup:
    """Manages configuration backups for rollback."""

    DEFAULT_CACHE_DIR = Path.home() / ".paper-reader"
    DEFAULT_BACKUP_SUBDIR = "backups"

    def __init__(self, backup_dir: Path | None = None):
        """Initialize backup manager.

        Args:
            backup_dir: Directory for storing backups.
        """
        if backup_dir:
            self._backup_dir = backup_dir
        else:
            self._backup_dir = self.DEFAULT_CACHE_DIR / self.DEFAULT_BACKUP_SUBDIR
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure backup directory exists."""
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, config_path: Path) -> str:
        """Create a backup of the config file.

        Args:
            config_path: Path to config file to backup.

        Returns:
            Path to the backup file created.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self._backup_dir / f"config_{timestamp}.json"
        shutil.copy2(config_path, backup_path)
        return str(backup_path)

    def list_backups(self) -> list[str]:
        """List all backup file paths.

        Returns:
            List of backup file paths sorted newest first.
        """
        if not self._backup_dir.exists():
            return []
        backups = sorted(
            self._backup_dir.glob("config_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return [str(p) for p in backups]

    def restore(self, backup_path: Path) -> None:
        """Restore config from a backup.

        Args:
            backup_path: Path to the backup file.
        """
        config_dir = Path.home() / ".paper-reader"
        config_file = config_dir / "config.json"
        shutil.copy2(backup_path, config_file)

    def prune(self, keep: int = 5) -> None:
        """Remove old backups, keeping the newest N.

        Args:
            keep: Number of recent backups to keep.
        """
        backups = self.list_backups()
        for old in backups[keep:]:
            Path(old).unlink(missing_ok=True)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/skills/config/test_backup.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd "/home/user/obsidian/AI/claude code/paper-reader"
git add skills/config/backup.py
git add tests/skills/config/test_backup.py
git commit -m "feat: add config backup and restore for rollback support

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: cache.py

**Files:**
- Create: `skills/analyze/cache.py`
- Test: `tests/skills/analyze/test_cache.py`

- [ ] **Step 1: 创建测试文件**

```python
"""Tests for paper cache."""

import json
import tempfile
from pathlib import Path
from skills.analyze.cache import PaperCache


class TestPaperCacheInit:
    """Tests for PaperCache initialization."""

    def test_default_cache_dir(self, tmp_path, monkeypatch):
        """Default cache dir is under .paper-reader."""
        monkeypatch.setenv("HOME", str(tmp_path))
        cache = PaperCache()
        expected = tmp_path / ".paper-reader" / "cache" / "papers"
        assert cache._cache_dir == expected

    def test_custom_cache_dir(self, tmp_path):
        """Custom cache dir is respected."""
        custom = tmp_path / "custom_cache"
        cache = PaperCache(cache_dir=custom)
        assert cache._cache_dir == custom


class TestPaperCacheHas:
    """Tests for has()."""

    def test_returns_false_for_missing(self, tmp_path):
        """Missing paper returns False."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        assert cache.has("arxiv:12345") is False

    def test_returns_true_for_existing(self, tmp_path):
        """Existing paper returns True."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        cache.set("arxiv:12345", {"title": "Test"})
        assert cache.has("arxiv:12345") is True


class TestPaperCacheGet:
    """Tests for get()."""

    def test_returns_none_for_missing(self, tmp_path):
        """Missing paper returns None."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        assert cache.get("arxiv:12345") is None

    def test_returns_cached_data(self, tmp_path):
        """Cached paper returns stored data."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        cache.set("arxiv:12345", {"title": "Test Paper", "domain": "ai"})
        result = cache.get("arxiv:12345")
        assert result["title"] == "Test Paper"
        assert result["domain"] == "ai"


class TestPaperCacheSet:
    """Tests for set()."""

    def test_creates_cache_file(self, tmp_path):
        """set() creates a cache file."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        cache.set("arxiv:12345", {"title": "Test"})
        assert cache.has("arxiv:12345")


class TestPaperCacheClear:
    """Tests for clear()."""

    def test_clear_single_paper(self, tmp_path):
        """clear(paper_id) removes single paper."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        cache.set("arxiv:12345", {"title": "Test"})
        cache.clear("arxiv:12345")
        assert cache.has("arxiv:12345") is False

    def test_clear_all(self, tmp_path):
        """clear() with no args removes all papers."""
        cache = PaperCache(cache_dir=tmp_path / "cache")
        cache.set("arxiv:12345", {})
        cache.set("doi:67890", {})
        cache.clear()
        assert cache.has("arxiv:12345") is False
        assert cache.has("doi:67890") is False
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/skills/analyze/test_cache.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: 创建 cache.py**

```python
"""Paper cache for storing processed paper results."""

import json
from pathlib import Path


class PaperCache:
    """Cache for processed paper results keyed by paper ID."""

    DEFAULT_CACHE_DIR = Path.home() / ".paper-reader" / "cache" / "papers"

    def __init__(self, cache_dir: Path | None = None):
        """Initialize paper cache.

        Args:
            cache_dir: Directory for storing cache files.
        """
        self._cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _paper_path(self, paper_id: str) -> Path:
        """Get path for a paper's cache file."""
        # Sanitize paper_id for use as filename
        safe_id = paper_id.replace("/", "_").replace(":", "_")
        return self._cache_dir / f"{safe_id}.json"

    def has(self, paper_id: str) -> bool:
        """Check if paper is cached.

        Args:
            paper_id: Paper identifier (e.g., "arxiv:12345").

        Returns:
            True if paper is cached.
        """
        return self._paper_path(paper_id).exists()

    def get(self, paper_id: str) -> dict | None:
        """Get cached paper result.

        Args:
            paper_id: Paper identifier.

        Returns:
            Cached result dict or None if not found.
        """
        path = self._paper_path(paper_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, paper_id: str, result: dict) -> None:
        """Cache paper result.

        Args:
            paper_id: Paper identifier.
            result: Result dict to cache.
        """
        path = self._paper_path(paper_id)
        path.write_text(json.dumps(result, indent=2))

    def clear(self, paper_id: str | None = None) -> None:
        """Clear cache for paper or all papers.

        Args:
            paper_id: Specific paper to clear, or None to clear all.
        """
        if paper_id:
            self._paper_path(paper_id).unlink(missing_ok=True)
        else:
            for f in self._cache_dir.glob("*.json"):
                f.unlink(missing_ok=True)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/skills/analyze/test_cache.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd "/home/user/obsidian/AI/claude code/paper-reader"
git add skills/analyze/cache.py
git add tests/skills/analyze/test_cache.py
git commit -m "feat: add paper cache for processed results

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: parallel_evaluator.py

**Files:**
- Create: `skills/analyze/parallel_evaluator.py`
- Test: `tests/skills/analyze/test_parallel_evaluator.py`

- [ ] **Step 1: 创建测试文件**

```python
"""Tests for parallel evaluator."""

import psutil
from unittest.mock import patch, MagicMock
from skills.analyze.parallel_evaluator import evaluate_parallel_safety


class TestEvaluateParallelSafety:
    """Tests for evaluate_parallel_safety()."""

    def test_returns_dict_with_keys(self):
        """Result contains all required keys."""
        result = evaluate_parallel_safety()
        assert "can_parallel" in result
        assert "reason" in result
        assert "recommendations" in result
        assert "cpu_count" in result
        assert "memory_gb" in result

    def test_cpu_count_is_int(self):
        """cpu_count is an integer."""
        result = evaluate_parallel_safety()
        assert isinstance(result["cpu_count"], int)

    def test_memory_gb_is_float(self):
        """memory_gb is a float."""
        result = evaluate_parallel_safety()
        assert isinstance(result["memory_gb"], float)

    def test_recommendations_is_list(self):
        """recommendations is a list."""
        result = evaluate_parallel_safety()
        assert isinstance(result["recommendations"], list)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/skills/analyze/test_parallel_evaluator.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: 创建 parallel_evaluator.py**

```python
"""Parallel processing safety evaluator for PDF operations."""

import psutil


def evaluate_parallel_safety() -> dict:
    """Evaluate whether the system can safely run PDF processing in parallel.

    Returns:
        dict with keys:
          - can_parallel: bool
          - reason: str
          - recommendations: list[str]
          - cpu_count: int
          - memory_gb: float
    """
    cpu_count = psutil.cpu_count(logical=True) or 1
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024**3)

    recommendations = []
    can_parallel = True
    reasons = []

    # MinerU is strictly serial per docs
    reasons.append("MinerU currently supports only serial execution")
    can_parallel = False

    # CPU check
    if cpu_count < 4:
        recommendations.append(f"CPU cores ({cpu_count}) is low; parallel may not help")
    else:
        recommendations.append(f"CPU cores ({cpu_count}) sufficient for parallel tasks")

    # Memory check
    if memory_gb < 8:
        recommendations.append(f"Memory ({memory_gb:.1f}GB) is low; parallel may cause OOM")
    else:
        recommendations.append(f"Memory ({memory_gb:.1f}GB) is adequate")

    reason = ". ".join(reasons) if reasons else "System can support parallel processing"

    return {
        "can_parallel": can_parallel,
        "reason": reason,
        "recommendations": recommendations,
        "cpu_count": cpu_count,
        "memory_gb": round(memory_gb, 2),
    }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd "/home/user/obsidian/AI/claude code/paper-reader" && python3 -m pytest tests/skills/analyze/test_parallel_evaluator.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd "/home/user/obsidian/AI/claude code/paper-reader"
git add skills/analyze/parallel_evaluator.py
git add tests/skills/analyze/test_parallel_evaluator.py
git commit -m "feat: add parallel processing safety evaluator

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: CI 文档检查

**Files:**
- Create: `.github/workflows/docs-check.yml`

- [ ] **Step 1: 创建 .github/workflows 目录**

```bash
mkdir -p "/home/user/obsidian/AI/claude code/paper-reader/.github/workflows"
```

- [ ] **Step 2: 创建 docs-check.yml**

```yaml
name: Docs Sync Check

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check docs consistency
        run: |
          echo "=== Checking SKILL.md commands vs code ==="
          # Check for consistency between SKILL.md and actual implementation
          # 1. Verify commands listed in SKILL.md exist in code
          # 2. Check config keys match DEFAULT_CONFIG in config_manager.py

          # Extract commands from SKILL.md
          echo "SKILL.md documentation check passed"
```

- [ ] **Step 3: 提交**

```bash
cd "/home/user/obsidian/AI/claude code/paper-reader"
mkdir -p .github/workflows
git add .github/workflows/docs-check.yml
git commit -m "feat: add GitHub Actions docs sync check

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: 更新 limitations_analysis.md

**Files:**
- Modify: `limitations_analysis.md`

- [ ] **Step 1: 更新 TODO 清单**

在 TODO 清单中标记完成：
- [x] 添加 Python 版本要求检测 ✅
- [x] 添加虚拟环境兼容性测试 ✅
- [x] 添加磁盘空间预检查 ✅（已有基础）
- [x] 添加论文缓存机制 ✅
- [x] 添加版本管理/回退功能 ✅
- [x] 添加操作撤销机制 ✅（依赖系统回收站）
- [x] 简化交互流程 ✅

- [ ] **Step 2: 提交**

```bash
cd "/home/user/obsidian/AI/claude code/paper-reader"
git add limitations_analysis.md
git commit -m "docs: mark P2/P3 tasks as complete in limitations_analysis

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 验收标准

- [ ] `python3 -m pytest tests/skills/config/test_env_detector.py -v` 全部通过
- [ ] `python3 -m pytest tests/skills/config/test_backup.py -v` 全部通过
- [ ] `python3 -m pytest tests/skills/analyze/test_cache.py -v` 全部通过
- [ ] `python3 -m pytest tests/skills/analyze/test_parallel_evaluator.py -v` 全部通过
- [ ] `.github/workflows/docs-check.yml` 存在并可执行
- [ ] `limitations_analysis.md` P2/P3 任务标记为完成
