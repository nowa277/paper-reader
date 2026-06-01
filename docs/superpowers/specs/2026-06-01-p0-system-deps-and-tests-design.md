# P0 系统依赖检测 + 单元测试框架

**日期:** 2026-06-01
**状态:** 设计完成

---

## 1. 概述

为 paper-reader 实现两个基础设施模块：
1. **系统依赖检测** - 检测 curl, pandoc, tesseract 等外部工具
2. **单元测试框架** - 统一 fixtures，提升测试覆盖率

---

## 2. 系统依赖检测

### 2.1 依赖项定义

| 工具 | 用途 | 必需 |
|------|------|------|
| curl | 网络下载 | 是 |
| pandoc | 文档转换 | 是 |
| tesseract | OCR 识别 | 否 |

### 2.2 API 设计

**文件:** `skills/config/system_deps.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Dependency:
    name: str           # 显示名称
    command: str        # 命令名
    required: bool      # 是否必需
    version_cmd: Optional[list[str]] = None  # 版本检测命令

SYSTEM_DEPS = {
    "curl": Dependency("curl", "curl", True, ["curl", "--version"]),
    "pandoc": Dependency("Pandoc", "pandoc", True, ["pandoc", "--version"]),
    "tesseract": Dependency("Tesseract OCR", "tesseract", False, ["tesseract", "--version"]),
}

def check_dependency(dep_id: str) -> tuple[bool, Optional[str]]:
    """检测单个依赖是否安装。

    Returns:
        (是否安装, 版本信息或错误消息)
    """
    ...

def check_all_dependencies() -> dict[str, dict]:
    """检查所有依赖。

    Returns:
        {dep_id: {"installed": bool, "version": str, "required": bool}}
    """
    ...

def get_missing_required() -> list[str]:
    """返回缺失的必需依赖 ID 列表。"""
    ...

def get_installation_instructions(dep_id: str) -> str:
    """获取依赖安装说明。"""
    ...
```

### 2.3 检测逻辑

1. 使用 `shutil.which()` 查找命令
2. 执行 `--version` 获取版本信息
3. 捕获异常，返回友好错误消息

---

## 3. 测试框架

### 3.1 统一 fixtures

**文件:** `tests/conftest.py`

```python
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def temp_config_dir(tmp_path):
    """临时配置目录 fixture。"""
    config_dir = tmp_path / ".paper-reader"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def mock_home(tmp_path, monkeypatch):
    """模拟 HOME 目录。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path

@pytest.fixture
def system_deps():
    """系统依赖检测器 fixture。"""
    from skills.config.system_deps import SystemDepsChecker
    return SystemDepsChecker()
```

### 3.2 测试覆盖目标

| 模块 | 文件 | 目标覆盖率 |
|------|------|-----------|
| platform.py | test_platform.py | 90% |
| system_deps.py | test_system_deps.py | 90% |
| config_manager.py | test_config_manager.py | 80% |
| qa_logger.py | test_qa_logger.py | 90% |
| mineru/detector.py | test_detector.py | 90% |
| mineru/installer.py | test_installer.py | 85% |

---

## 4. 文件结构

```
paper-reader/
├── skills/config/
│   ├── __init__.py
│   ├── platform.py          # 现有
│   ├── system_deps.py       # 新增
│   └── config_manager.py    # 现有
├── tests/
│   ├── conftest.py          # 更新：添加统一 fixtures
│   ├── skills/config/
│   │   ├── test_platform.py        # 现有
│   │   ├── test_system_deps.py    # 新增
│   │   └── test_config_manager.py # 新增
│   └── skills/analyze/
│       └── test_qa_logger.py       # 现有
```

---

## 5. 实现顺序

1. 创建 `system_deps.py`
2. 创建 `test_system_deps.py`
3. 更新 `conftest.py` 添加 fixtures
4. 创建 `test_config_manager.py`
5. 运行完整测试套件，验证覆盖率

---

## 6. 验收标准

- [ ] `python -m pytest tests/skills/config/test_system_deps.py` 全部通过
- [ ] 系统依赖检测覆盖率 ≥ 90%
- [ ] 所有 fixtures 正常工作
- [ ] `python -m pytest --cov=skills --cov-report=term-missing` 整体覆盖率 ≥ 80%
