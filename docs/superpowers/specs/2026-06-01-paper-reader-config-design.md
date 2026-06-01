# Paper Reader 配置系统设计文档

> 版本: 1.0 | 日期: 2026-06-01 | 状态: 设计中

## 1. 问题陈述

当前 paper-reader skill 存在以下问题：

1. **路径硬编码** — 所有路径直接写在 SKILL.md 中，无法跨平台移植
2. **无自动检测** — 需要用户手动配置 MinerU 等依赖
3. **无智能安装** — 用户需要自行查找并安装 MinerU
4. **平台兼容性差** — Linux/macOS/Windows 路径处理不一致

## 2. 设计目标

| 目标 | 描述 |
|------|------|
| **跨平台兼容** | 支持 Linux (Ubuntu/Debian/RedHat)、macOS、Windows |
| **智能检测** | 自动检测本地环境和依赖 |
| **用户同意** | 自动安装前需用户确认 |
| **状态持久化** | 配置结果保存，可跨会话复用 |
| **可扩展性** | 子技能架构支持后续功能扩展 |

## 3. 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Paper Reader Skill                          │
├─────────────────────────────────────────────────────────────────┤
│  SKILL.md (路由器)                                              │
│  ├── 解析子命令: /paper-reader setup config                     │
│  ├── 路由到对应子技能                                           │
│  └── 共享配置管理器                                             │
├─────────────────────────────────────────────────────────────────┤
│  references/                                                    │
│  ├── setup/                                                     │
│  │   ├── config.md      ← 配置子技能（检测+安装）              │
│  │   └── mineru.md      ← MinerU 安装子技能                    │
│  ├── analyze/                                                   │
│  │   ├── scan.md        ← 快速扫描子技能                       │
│  │   └── deep.md        ← 深度分析子技能                       │
│  └── batch/                                                     │
│      └── process.md   ← 批量处理子技能                          │
├─────────────────────────────────────────────────────────────────┤
│  scripts/                                                       │
│  └── config_manager.py  ← 统一配置管理（读写JSON）              │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 用户调用方式

| 命令 | 功能 |
|------|------|
| `/paper-reader setup config` | 运行配置检测（检测所有依赖） |
| `/paper-reader setup mineru` | 单独检测/安装 MinerU |
| `/paper-reader analyze scan` | 快速扫描模式 |
| `/paper-reader analyze deep` | 深度分析模式 |
| `/paper-reader batch` | 批量处理模式 |

### 3.3 子技能互调流程

```
用户: /paper-reader setup config
  │
  ▼
SKILL.md 解析��令
  │
  ├── 识别: setup → config
  │
  ▼
加载 references/setup/config.md
  │
  ▼
config.md 子技能执行:
  │
  ├── 1. 读取 ~/.paper-reader/config.json
  │
  ├── 2. 检测平台 (Linux/macOS/Windows)
  │
  ├── 3. 检测 MinerU
  │     │
  │     ├── 已安装 → 记录版本 → 跳过
  │     │
  │     └── 未安装 → 询问用户是否安装
  │                    │
  │                    └── 同意 → 调用 mineru.md
  │                                    │
  │                                    ▼
  │                            mineru.md 执行:
  │                            ├── 检测 Python 版本
  │                            ├── 检测 pip 可用性
  │                            ├── 选择安装方式
  │                            ├── 执行安装
  │                            └── 返回结果
  │
  ├── 4. 检测其他依赖 (curl, bash等)
  │
  ├── 5. 检测归档目录
  │
  └── 6. 保存配置 → config.json
       │
       ▼
返回成功消息给用户
```

## 4. 配置存储

### 4.1 配置文件位置

```
~/.paper-reader/config.json
```

| 平台 | 路径示例 |
|------|---------|
| Linux | `/home/user/.paper-reader/config.json` |
| macOS | `/Users/user/.paper-reader/config.json` |
| Windows | `C:\Users\user\.paper-reader\config.json` |

### 4.2 配置结构

```json
{
  "version": "1.0.0",
  "initialized": "2026-06-01T00:00:00Z",
  "platform": {
    "os": "linux",
    "distro": "ubuntu",
    "arch": "x86_64",
    "python_version": "3.11"
  },
  "mineru": {
    "path": "/home/user/.local/bin/mineru",
    "version": "3.1.0",
    "installed": true,
    "install_method": "pip",
    "last_check": "2026-06-01T00:00:00Z"
  },
  "paths": {
    "archive_base": "/home/user/obsidian/papers",
    "work_base": "/tmp/paper-reader"
  },
  "dependencies": {
    "curl": { "available": true, "version": "7.81.0" },
    "bash": { "available": true, "version": "5.2" },
    "python3": { "available": true, "version": "3.11.0" }
  },
  "features": {
    "jina_reader": { "enabled": true, "rate_limit": 20 },
    "vision_analyze": { "enabled": false, "reason": "model_lacks_vision" }
  }
}
```

### 4.3 状态说明

| 字段 | 描述 |
|------|------|
| `version` | 配置文件版本 |
| `initialized` | 首次初始化时间 |
| `platform` | 操作系统信息 |
| `mineru` | MinerU 安装状态和路径 |
| `paths` | 用户目录配置 |
| `dependencies` | 系统依赖检测结果 |
| `features` | 功能特性启用状态 |

## 5. 核心模块设计

### 5.1 config_manager.py

```python
# 功能: 统一配置管理
# 位置: scripts/config_manager.py

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config_path = self._get_config_path()
        self.config = self.load()
    
    def _get_config_path(self) -> str:
        """获取配置文件路径（跨平台）"""
        home = os.path.expanduser("~")
        return os.path.join(home, ".paper-reader", "config.json")
    
    def load(self) -> dict:
        """加载配置"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._default_config()
    
    def save(self):
        """保存配置"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default=None):
        """获取配置项"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value == default:
                return default
        return value
    
    def set(self, key: str, value):
        """设置配置项"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def _default_config(self) -> dict:
        """默认配置"""
        return {
            "version": "1.0.0",
            "platform": {},
            "mineru": {"installed": False},
            "paths": {},
            "dependencies": {},
            "features": {}
        }
```

### 5.2 MinerU 检测逻辑

```python
def detect_mineru() -> dict:
    """检测 MinerU 安装状态"""
    result = {
        "installed": False,
        "path": None,
        "version": None,
        "install_method": None
    }
    
    # 1. 检查 pip 安装
    try:
        proc = subprocess.run(
            ["pip", "show", "mineru"],
            capture_output=True, text=True
        )
        if proc.returncode == 0:
            result["installed"] = True
            result["install_method"] = "pip"
            # 解析版本
            for line in proc.stdout.split('\n'):
                if line.startswith("Version:"):
                    result["version"] = line.split(":")[1].strip()
            result["path"] = "pip-installed"
            return result
    except FileNotFoundError:
        pass
    
    # 2. 检查 PATH 中的 mineru 命令
    try:
        proc = subprocess.run(
            ["which", "mineru"],
            capture_output=True, text=True
        )
        if proc.returncode == 0:
            result["installed"] = True
            result["path"] = proc.stdout.strip()
            # 获取版本
            try:
                vproc = subprocess.run(
                    ["mineru", "--version"],
                    capture_output=True, text=True, timeout=5
                )
                result["version"] = vproc.stdout.strip()
            except:
                pass
            return result
    except FileNotFoundError:
        pass
    
    # 3. 检查常见安装路径
    common_paths = [
        os.path.expanduser("~/.local/bin/mineru"),
        "/usr/local/bin/mineru",
        "/usr/bin/mineru",
    ]
    for path in common_paths:
        if os.path.exists(path):
            result["installed"] = True
            result["path"] = path
            return result
    
    return result
```

### 5.3 MinerU 安装逻辑

```python
def install_mineru(ask_consent: bool = True) -> dict:
    """安装 MinerU"""
    
    # 检查 Python 版本
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        return {"success": False, "error": "Python 3.10+ required"}
    
    # 如果 ask_consent=True，询问用户
    # （实际实现会在 skill 中处理用户交互）
    
    # 安装命令
    install_cmds = [
        "pip install mineru",
        "pip install mineru[pipeline]",  # 推荐，包含完整功能
    ]
    
    for cmd in install_cmds:
        try:
            proc = subprocess.run(
                cmd.split(),
                capture_output=True, text=True,
                timeout=300  # 5分钟超时
            )
            if proc.returncode == 0:
                return {"success": True, "method": cmd}
        except Exception as e:
            continue
    
    return {"success": False, "error": "Installation failed"}
```

## 6. 平台适配

### 6.1 平台检测

```python
import platform
import sys

def detect_platform() -> dict:
    """检测平台信息"""
    system = platform.system().lower()
    
    result = {
        "os": system,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "arch": platform.machine()
    }
    
    if system == "linux":
        # 检测发行版
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        result["distro"] = line.split("=")[1].strip().strip('"')
                        break
        except:
            result["distro"] = "unknown"
    
    elif system == "darwin":
        result["distro"] = "macos"
        
    elif system == "windows":
        result["distro"] = "windows"
    
    return result
```

### 6.2 路径适配

| 场景 | Linux/macOS | Windows |
|------|-------------|---------|
| 用户目录 | `~` | `~` (C:\Users\) |
| 临时目录 | `/tmp/paper-reader` | `%TEMP%\paper-reader` |
| 配置目录 | `~/.paper-reader/` | `%USERPROFILE%\.paper-reader\` |
| 归档目录 | `~/obsidian/papers` | `C:\Users\user\obsidian\papers` |

## 7. 子技能接口

### 7.1 子技能标准格式

每个子技能文件（如 `config.md`）应包含：

```markdown
---
name: paper-reader-setup-config
description: 检测并配置 paper-reader 运行环境中
parent: paper-reader
subcommand: setup config
---

## 执行步骤

1. 调用 ConfigManager 加载配置
2. 检测平台信息
3. 检测 MinerU 状态
4. 如未安装，询问用户是否安装
5. 保存配置

## 输出

返回配置检测结果和后续操作建议
```

### 7.2 子技能互调

子技能可以通过以下方式调用其他子技能：

```python
# 在 config.md 子技能中调用 mineru.md
# 通过 Skill 工具调用
skill("paper-reader-setup-mineru")
```

## 8. 用户交互流程

### 8.1 首次配置流程

```
用户: /paper-reader setup config

→ config.md 加载
→ 检测平台: Linux Ubuntu x86_64
→ 检测 MinerU: ❌ 未安装
→ 检测 Python: ✅ 3.11.0
→ 检测 curl: ✅ 7.81.0

输出:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 环境检测结果

| 组件 | 状态 | 版本 |
|------|------|------|
| 平台 | ✅ Ubuntu 22.04 | x86_64 |
| Python | ✅ 已安装 | 3.11.0 |
| MinerU | ❌ 未安装 | - |
| curl | ✅ 已安装 | 7.81.0 |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ MinerU 未安装，需要安装才能使用论文解析功能。

是否现在安装？
  A. ✅ 安装 mineru[pipeline]（推荐）
  B. 🔄 稍后手动安装
  C. ❌ 取消
```

### 8.2 已配置用户

```
用户: /paper-reader analyze scan paper.pdf

→ SKILL.md 解析命令
→ 检测配置存在 → 加载 config.json
→ MinerU 已安装 ✅ → 直接执行
→ 输出扫描结果
```

## 9. 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| 配置文件损坏 | 自动重建默认配置，提示用户 |
| Python 版本不足 | 提示升级 Python，给出具体版本要求 |
| 网络安装失败 | 提供备选方案（镜像源、离线安装） |
| 权限不足 | 提示使用 `sudo` 或虚拟环境 |
| 磁盘空间不足 | 检测并警告，提供清理建议 |

## 10. 验收标准

| 标准 | 描述 |
|------|------|
| **跨平台** | 在 Linux/macOS/Windows 上均可运行 |
| **自动检测** | 无需手动配置，自动检测环境 |
| **用户同意** | 安装前必须用户确认 |
| **状态持久** | 配置保存后，下次启动无需重新配置 |
| **错误恢复** | 错误场景有友好提示和解决方案 |

## 11. 待定事项

- [ ] 确定配置文件的精确路径规则
- [ ] 设计配置备份/恢复机制
- [ ] 定义子技能间的标准通信协议
- [ ] 编写完整的 config_manager.py 代码
- [ ] 编写各子技能的详细实现

---

## 附录：相关文件

| 文件 | 描述 |
|------|------|
| `SKILL.md` | 主 skill 路由入口 |
| `scripts/config_manager.py` | 配置管理模块 |
| `references/setup/config.md` | 配置子技能 |
| `references/setup/mineru.md` | MinerU 安装子技能 |
| `~/.paper-reader/config.json` | 配置文件（运行时生成） |