# P2 + P3 增强设计

**日期:** 2026-06-01
**状态:** 设计完成

---

## 1. 概述

P2（中优先级）和 P3（低优先级）增强功能，分为三个设计包：
1. **P2-A: 环境+资源增强**
2. **P2-B: 性能+体验增强**
3. **P3: 版本+文档增强**

---

## 2. P2-A: 环境+资源增强

### 2.1 Python 版本检测

**现状:** `skills/mineru/installer.py` 已有 `check_python_version()` 函数，检查 `MIN_PYTHON_VERSION = (3, 10)`。

**任务:** 确保 `check_python_version()` 在启动时被调用，版本不满足时给出明确错误。

### 2.2 虚拟环境检测

**新增模块:** `skills/config/env_detector.py`

```python
def detect_venv_type() -> str | None:
    """检测当前虚拟环境类型。

    Returns:
        'venv' | 'conda' | 'uv' | 'system' | None
    """
    # 检查 VIRTUAL_ENV, CONDA_DEFAULT_ENV, UV_CACHE_DIR 等环境变量
    ...

def check_venv_compatibility() -> tuple[bool, str]:
    """检查虚拟环境兼容性。

    Returns:
        (ok, warning_message)
    """
    venv_type = detect_venv_type()
    if venv_type is None:
        return True, ""  # 系统 Python，无问题
    if venv_type == 'conda':
        return False, "Conda 环境可能与 MinerU 依赖冲突，建议使用 venv 或系统 Python"
    if venv_type == 'uv':
        return True, "UV 环境检测到"
    return True, ""
```

### 2.3 磁盘空间检查

**现状:** `skills/fetch/fetcher.py` 中 `download_with_space_check()` 已有实现。

### 2.4 临时文件

**策略:** 默认不清理。所有文件自动整理到结构化目录：
```
~/.paper-reader/
├── cache/              # 论文缓存
├── temp/               # 临时文件（不自动清理）
├── backups/           # 配置备份
└── config.json
```

---

## 3. P2-B: 性能+体验增强

### 3.1 论文缓存

**新增模块:** `skills/analyze/cache.py`

```python
class PaperCache:
    """基于 Paper ID 的论文缓存。"""

    def __init__(self, cache_dir: Path | None = None):
        """初始化缓存。"""
        self._cache_dir = cache_dir or (CACHE_DIR / "papers")
        self._index_file = CACHE_DIR / "cache_index.json"

    def get(self, paper_id: str) -> dict | None:
        """获取缓存的论文结果。"""
        ...

    def set(self, paper_id: str, result: dict) -> None:
        """缓存论文结果。"""
        ...

    def has(self, paper_id: str) -> bool:
        """检查论文是否已缓存。"""
        ...

    def clear(self, paper_id: str | None = None) -> None:
        """清除缓存。"""
        ...
```

**缓存键:** `arxiv:XXXX.XXXXX`, `doi:XXXXX`, `url:XXXXX`

### 3.2 并行可行性评估

**新增模块:** `skills/analyze/parallel_evaluator.py`

```python
def evaluate_parallel_safety() -> dict:
    """评估当前系统是否适合并行处理 PDF。

    Returns:
        {
            "can_parallel": bool,
            "reason": str,
            "recommendations": list[str],
            "cpu_count": int,
            "memory_gb": float,
        }
    """
    # 1. 检查 CPU 核心数
    # 2. 检查可用内存
    # 3. 检查 MinerU 是否支持并行（当前不支持）
    # 4. 输出评估报告
```

**评估标准:**
- CPU ≥ 4 核: 建议并行
- 内存 ≥ 8GB: 建议并行
- MinerU 当前严格串行: 报告说明

### 3.3 简化交互流程

**3步核心流:**
```
1. fetch <url/id>     # 获取论文
2. analyze            # 分析（自动检测领域 + 选择模式）
3. archive           # 归档到 Obsidian
```

**自动化:**
- 领域检测: 读取内容后自动检测，无需用户确认
- 模式选择: 默认深度精读模式，可通过参数覆盖
- 归档: 自动创建目录，无需用户干预

**用户可选覆盖:**
```
/paper-reader analyze --domain ai --mode deep ./paper.pdf
/paper-reader analyze --domain med --mode scan ./paper.pdf
```

---

## 4. P3: 版本+文档增强

### 4.1 自动备份

**新增模块:** `skills/config/backup.py`

```python
class ConfigBackup:
    """配置自动备份与回滚。"""

    def __init__(self, backup_dir: Path | None = None):
        """初始化备份管理器。"""
        self._backup_dir = backup_dir or (CACHE_DIR / "backups")

    def backup(self, config_path: Path) -> str:
        """创建配置备份。

        Returns:
            备份文件路径
        """
        # 每次修改前自动调用
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self._backup_dir / f"config_{timestamp}.json"
        shutil.copy2(config_path, backup_path)
        return str(backup_path)

    def list_backups(self) -> list[dict]:
        """列出所有备份。"""
        ...

    def restore(self, backup_path: Path) -> None:
        """从备份恢复。"""
        ...

    def prune(self, keep: int = 5) -> None:
        """删除旧备份，保留最近 N 个。"""
        ...
```

**触发时机:**
- 配置文件修改前（`ConfigManager.set()` 内部调用）
- MinerU 安装前

### 4.2 撤销机制

**策略:** 依赖系统回收站
- 删除操作使用 `send2trash` 库（跨平台）而非直接删除
- 如果回收站不可用，回退到直接删除但给出警告

### 4.3 CI 文档同步检查

**新增 GitHub Actions:** `.github/workflows/docs-check.yml`

```yaml
name: Docs Sync Check
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check docs consistency
        run: |
          # 1. 检查 SKILL.md 中的命令与代码实现是否匹配
          # 2. 检查 README.md 与 SKILL.md 是否同步
          # 3. 检查设计文档与实现是否一致
```

**检查内容:**
- `SKILL.md` 中列出的命令是否在代码中实现
- 配置项默认值是否与文档一致
- 依赖版本要求是否与文档一致

---

## 5. 文件结构

```
paper-reader/
├── skills/
│   ├── config/
│   │   ├── env_detector.py      # 新增: Python/venv 检测
│   │   ├── backup.py             # 新增: 配置备份与回滚
│   │   └── ...
│   ├── fetch/
│   │   └── fetcher.py            # 已有
│   └── analyze/
│       ├── cache.py              # 新增: 论文缓存
│       ├── parallel_evaluator.py # 新增: 并行可行性评估
│       └── ...
├── .github/
│   └── workflows/
│       └── docs-check.yml        # 新增: CI 文档检查
└── docs/superpowers/specs/
    └── 2026-06-01-p2-p3-enhancements-design.md
```

---

## 6. 实现顺序

1. **P2-A:** `env_detector.py` + `check_python_version()` 集成
2. **P3:** `backup.py` + `ConfigManager` 集成
3. **P2-B:** `cache.py` + `parallel_evaluator.py`
4. **P2-B:** 简化流程（修改 SKILL.md 和相关代码）
5. **P3:** GitHub Actions CI 检查

---

## 7. 验收标准

- [ ] `check_python_version()` 在 MinerU 安装前被调用
- [ ] 虚拟环境检测在启动时输出警告（如适用）
- [ ] 论文缓存按 paper ID 工作，`PaperCache.has()` 正确判断
- [ ] 并行评估报告输出系统资源和建议
- [ ] 3步流程可正常工作（fetch → analyze → archive）
- [ ] 配置修改前自动备份
- [ ] `ConfigBackup.restore()` 可恢复历史备份
- [ ] GitHub Actions CI 检查 `SKILL.md` 与代码一致性
