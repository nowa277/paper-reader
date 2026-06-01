# Paper Reader Skill - Agent 适配器设计

> 版本: 1.0
> 日期: 2026-06-01
> 状态: 已批准

---

## 1. 概述

本文档描述 Paper Reader Skill 的多 Agent 适配器架构设计，实现对主流 AI Coding Agent 的统一支持。

### 1.1 目标

- 为 Claude Code、Hermes、Codex、OpenCode、Cursor、Windsurf、Zed、Copilot CLI、Gemini CLI 提供原生适配
- 单一源配置，避免多副本同步问题
- 模块化架构，易于扩展新 Agent

### 1.2 参考文献

- [Understand-Anything](https://github.com/Lum1104/Understand-Anything) - 插件目录模式
- [CodeGraph](https://github.com/colbymchenry/codegraph) - AgentTarget Registry 模式
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) - agentskills.io 标准

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    agent_adapters/                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │  registry   │───▶│ BaseAdapter  │───▶│ AgentAdapter  │  │
│  │  (注册表)    │    │ (抽象基类)    │    │ (具体实现)     │  │
│  └─────────────┘    └──────────────┘    └───────────────┘  │
│         │                                           ▲       │
│         ▼                                           │       │
│  ┌─────────────────────────────────────────────────┴─────┐  │
│  │                    generator.py                       │  │
│  │              (模板 + 配置 → 适配文件)                  │  │
│  └──────���────────────────────────────────────────────────┘  │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐             │
│         ▼                  ▼                  ▼             │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐        │
│  │ templates/ │    │ templates/ │    │ templates/ │  ...   │
│  │ skill_md   │    │ agents_md  │    │ hermes_yaml│        │
│  └────────────┘    └────────────┘    └────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| **BaseAdapter** | `base.py` | 抽象基类，定义适配器接口 |
| **AgentAdapter** | `adapters/*.py` | 各 Agent 的具体实现 |
| **Registry** | `registry.py` | 适配器注册与管理 |
| **Generator** | `generator.py` | 读取配置，生成适配文件 |
| **Templates** | `templates/*.j2` | Jinja2 模板文件 |

---

## 3. 组件设计

### 3.1 BaseAdapter 抽象基类

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class AdapterConfig:
    """适配器配置"""
    name: str                          # 显示名称
    id: str                            # 唯一标识符
    config_file: str                   # 配置文件路径
    skill_format: str                  # 技能格式 (markdown/yaml/json)
    command_prefix: str                # 命令前缀

@dataclass
class GenerationResult:
    """生成结果"""
    success: bool
    output_files: list[str]
    errors: list[str]

class BaseAdapter(ABC):
    """Agent 适配器抽象基类"""
    
    @abstractmethod
    def get_config(self) -> AdapterConfig:
        """获取适配器配置"""
        pass
    
    @abstractmethod
    def generate_skill_file(self, skill_source: str) -> str:
        """生成技能文件"""
        pass
    
    @abstractmethod
    def generate_config_file(self, config: dict) -> str:
        """生成配置文件"""
        pass
    
    @abstractmethod
    def detect_installation(self) -> bool:
        """检测 Agent 是否已安装"""
        pass
    
    @abstractmethod
    def get_installation_instructions(self) -> str:
        """获取安装指南"""
        pass
```

### 3.2 Agent 适配器注册表

```python
# registry.py
from typing import Dict, Type
from .base import BaseAdapter

class Registry:
    """Agent 适配器注册表"""
    
    _adapters: Dict[str, Type[BaseAdapter]] = {}
    
    @classmethod
    def register(cls, adapter_id: str, adapter_class: Type[BaseAdapter]):
        """注册适配器"""
        cls._adapters[adapter_id] = adapter_class
    
    @classmethod
    def get(cls, adapter_id: str) -> BaseAdapter:
        """获取适配器实例"""
        if adapter_id not in cls._adapters:
            raise ValueError(f"Unknown adapter: {adapter_id}")
        return cls._adapters[adapter_id]()
    
    @classmethod
    def list_all(cls) -> list[str]:
        """列出所有已注册的适配器"""
        return list(cls._adapters.keys())
    
    @classmethod
    def detect_available(cls) -> list[str]:
        """检测已安装的 Agent"""
        available = []
        for adapter_id in cls._adapters:
            try:
                if cls.get(adapter_id).detect_installation():
                    available.append(adapter_id)
            except:
                pass
        return available
```

### 3.3 Generator 生成器

```python
# generator.py
from jinja2 import Environment, FileSystemLoader, Template
from pathlib import Path
from .base import BaseAdapter, GenerationResult
from .registry import Registry

class Generator:
    """适配文件生成器"""
    
    def __init__(self, template_dir: str, output_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.output_dir = Path(output_dir)
    
    def generate_all(self, skill_source: str, config: dict) -> GenerationResult:
        """生成所有适配文件"""
        results = []
        errors = []
        
        for adapter_id in Registry.list_all():
            try:
                adapter = Registry.get(adapter_id)
                output_file = self._generate_for_adapter(
                    adapter, skill_source, config
                )
                results.append(output_file)
            except Exception as e:
                errors.append(f"{adapter_id}: {str(e)}")
        
        return GenerationResult(
            success=len(errors) == 0,
            output_files=results,
            errors=errors
        )
    
    def _generate_for_adapter(
        self, 
        adapter: BaseAdapter, 
        skill_source: str, 
        config: dict
    ) -> str:
        """为单个适配器生成文件"""
        # 生成技能文件
        skill_content = adapter.generate_skill_file(skill_source)
        
        # 生成配置文件
        config_content = adapter.generate_config_file(config)
        
        # 写入文件
        output_path = self.output_dir / adapter.get_config().id
        output_path.mkdir(parents=True, exist_ok=True)
        
        (output_path / "SKILL.md").write_text(skill_content)
        (output_path / "config.json").write_text(config_content)
        
        return str(output_path)
```

---

## 4. Agent 适配器实现

### 4.1 支持的 Agent 列表

| Agent ID | 显示名称 | 配置文件 | 技能格式 |
|----------|----------|----------|----------|
| `claude` | Claude Code | `~/.claude/settings.json` | SKILL.md |
| `hermes` | Hermes Agent | `~/.hermes/skills/` | YAML (agentskills.io) |
| `codex` | Codex | `AGENTS.md` | AGENTS.md |
| `opencode` | OpenCode | `~/.config/opencode/` | agent-config.json |
| `cursor` | Cursor | `~/.cursor/rules/` | .cursorrules |
| `windsurf` | Windsurf | `~/.windsurf/rules/` | rules.md |
| `zed` | Zed | `.zed/` |zed.md |
| `copilot` | Copilot CLI | `~/.github-copilot/` | skills/ |
| `gemini` | Gemini CLI | `~/.gemini/settings.json` | GEMINI.md |

### 4.2 Claude Code 适配器

```python
# adapters/claude.py
from ..base import BaseAdapter, AdapterConfig

class ClaudeAdapter(BaseAdapter):
    """Claude Code 适配器"""
    
    def get_config(self) -> AdapterConfig:
        return AdapterConfig(
            name="Claude Code",
            id="claude",
            config_file="~/.claude/settings.json",
            skill_format="markdown",
            command_prefix="/paper-reader"
        )
    
    def generate_skill_file(self, skill_source: str) -> str:
        """生成 SKILL.md"""
        # 使用 skill_md.j2 模板
        template = self.env.get_template("skill_md.j2")
        return template.render(
            skill_name="paper-reader",
            skill_content=skill_source,
            command_prefix="/paper-reader"
        )
    
    def detect_installation(self) -> bool:
        """检测 Claude Code 是否已安装"""
        config_path = Path.home() / ".claude" / "settings.json"
        return config_path.exists()
```

### 4.3 Hermes 适配器

```python
# adapters/hermes.py
from ..base import BaseAdapter, AdapterConfig
import yaml

class HermesAdapter(BaseAdapter):
    """Hermes Agent 适配器"""
    
    def get_config(self) -> AdapterConfig:
        return AdapterConfig(
            name="Hermes Agent",
            id="hermes",
            config_file="~/.hermes/skills/",
            skill_format="yaml",
            command_prefix="/paper-reader"
        )
    
    def generate_skill_file(self, skill_source: str) -> str:
        """生成 Hermes 技能 YAML (agentskills.io 格式)"""
        template = self.env.get_template("hermes_yaml.j2")
        
        # 解析 skill_source 提取命令和参数
        commands = self._parse_commands(skill_source)
        
        return template.render(
            skill_name="paper-reader",
            description="Read and analyze academic papers",
            commands=commands,
            triggers=["/paper-reader", "paper-reader"]
        )
    
    def _parse_commands(self, skill_source: str) -> list[dict]:
        """解析命令定义"""
        commands = []
        # 实现命令解析逻辑
        return commands
    
    def detect_installation(self) -> bool:
        """检测 Hermes 是否已安装"""
        hermes_path = Path.home() / ".hermes" / "hermes-agent"
        return hermes_path.exists() or shutil.which("hermes") is not None
```

### 4.4 其他适配器

其他适配器（Codex, OpenCode, Cursor, Windsurf, Zed, Copilot, Gemini）遵循相同模式，继承 `BaseAdapter` 并实现对应接口。

---

## 5. 模板设计

### 5.1 SKILL.md 模板 (Claude Code)

```jinja2
# {{ skill_name }}

{{ skill_content }}

## 使用方式

```
{{ command_prefix }} <命令> [参数]
```

## 可用命令

{% for command in commands %}
- `{{ command_prefix }} {{ command.name }}` - {{ command.description }}
{% endfor %}
```

### 5.2 Hermes YAML 模板 (agentskills.io)

```jinja2
name: {{ skill_name }}
description: {{ description }}
version: 1.0.0

triggers:
{% for trigger in triggers %}
  - {{ trigger }}
{% endfor %}

commands:
{% for command in commands %}
  - name: {{ command.name }}
    description: {{ command.description }}
    arguments:
{% for arg in command.arguments %}
      - name: {{ arg.name }}
        type: {{ arg.type }}
        required: {{ arg.required }}
        description: {{ arg.description }}
{% endfor %}
{% endfor %}

permissions:
  - filesystem:read
  - filesystem:write
  - network:fetch
```

### 5.3 AGENTS.md 模板 (Codex)

```jinja2
# {{ skill_name }}

## 概述

{{ skill_content }}

## 命令

{% for command in commands %}
### {{ command.name }}

{{ command.description }}

**用法:**
```
{{ command.usage }}
```

{% endfor %}
```

---

## 6. 文件结构

```
paper-reader/
├── agent_adapters/
│   ├── __init__.py
│   ├── registry.py           # 适配器注册表
│   ├── base.py               # 抽象基类
│   ├── generator.py          # 文件生成器
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── claude.py         # Claude Code
│   │   ├── hermes.py         # Hermes
│   │   ├── codex.py          # Codex
│   │   ├── opencode.py       # OpenCode
│   │   ├── cursor.py         # Cursor
│   │   ├── windsurf.py       # Windsurf
│   │   ├── zed.py            # Zed
│   │   ├── copilot.py        # Copilot CLI
│   │   └── gemini.py         # Gemini CLI
│   └── templates/
│       ├── skill_md.j2       # SKILL.md 模板
│       ├── agents_md.j2      # AGENTS.md 模板
│       ├── hermes_yaml.j2    # Hermes YAML 模板
│       ├── opencode_json.j2  # OpenCode JSON 模板
│       ├── cursor_rules.j2   # Cursor rules 模板
│       └── zed_md.j2         # Zed 模板
├── paper-reader/
│   └── skills/
│       ├── config/           # Phase 1 已完成
│       ├── mineru/           # Phase 1 已完成
│       ├── fetch/
│       └── analyze/
└── docs/
    └── superpowers/
        ├── specs/            # 设计文档
        └── plans/            # 实现计划
```

---

## 7. 使用流程

### 7.1 用户流程

```
用户运行 generate.sh
       │
       ▼
┌──────────────────┐
│  读取 skills/    │  ← 源技能定义
│  源配置          │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  遍历 Registry   │  ← 获取所有已注册适配器
│  中的适配器      │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  每个适配器      │
│  生成对应文件    │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  输出到          │
│  output/         │
└──────────────────┘
```

### 7.2 开发者流程

```bash
# 添加新 Agent 适配器
1. 创建 adapters/new_agent.py
2. 继承 BaseAdapter 实现接口
3. 在 registry.py 中注册
4. 在 templates/ 添加模板
5. 运行 generate.sh 测试
```

---

## 8. 错误处理

| 错误场景 | 处理策略 |
|----------|----------|
| Agent 未安装 | 跳过生成，输出警告 |
| 模板文件缺失 | 使用默认模板 |
| 权限不足 | 提示用户手动复制 |
| 源配置解析失败 | 记录错误，继续生成其他 |
| 输出目录不存在 | 自动创建 |

---

## 9. 测试策略

### 9.1 单元测试

- `test_base_adapter` - 抽象基类测试
- `test_registry` - 注册表功能测试
- `test_generator` - 生成器逻辑测试
- `test_adapters` - 各适配器输出测试

### 9.2 集成测试

- `test_full_generation` - 完整生成流程测试
- `test_output_format` - 输出格式验证
- `test_agent_detection` - Agent 检测逻辑测试

---

## 10. 扩展性

### 10.1 添加新 Agent

1. 创建 `adapters/<agent_id>.py`
2. 继承 `BaseAdapter` 实现所有方法
3. 在 `registry.py` 添加注册语句
4. 创建对应的 Jinja2 模板
5. 添加对应测试用例

### 10.2 添加新模板

1. 在 `templates/` 目录创建 `.j2` 文件
2. 在对应的适配器中引用新模板
3. 添加模板测试

---

## 11. 待实现功能

- [ ] 适配器基类和注册表
- [ ] 9 个 Agent 适配器实现
- [ ] 6 个 Jinja2 模板
- [ ] 生成器脚本
- [ ] 单元测试
- [ ] 使用文档

---

## 12. 相关文档

- [Phase 1 实现](./2026-06-01-paper-reader-config-plan.md)
- [limitations_analysis.md](../limitations_analysis.md)
- [agentskills.io 标准](https://agentskills.io)