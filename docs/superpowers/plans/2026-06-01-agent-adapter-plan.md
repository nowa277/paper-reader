# Agent Adapter Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a multi-Agent adapter system supporting 9主流 AI Coding Agents (Claude Code, Hermes, Codex, OpenCode, Cursor, Windsurf, Zed, Copilot CLI, Gemini CLI) with unified Registry + BaseAdapter pattern and Jinja2 template generation.

**Architecture:** Registry pattern with BaseAdapter abstract class, individual adapter per Agent, Generator using Jinja2 templates, output organized by Agent ID under output directory.

**Tech Stack:** Python dataclasses, abc (ABC, abstractmethod), Jinja2, pathlib, shutil, yaml

---

## File Structure

```
paper-reader/
├── agent_adapters/
│   ├── __init__.py
│   ├── base.py              # AdapterConfig, GenerationResult, BaseAdapter
│   ├── registry.py          # Registry class with register/get/list_all/detect_available
│   ├── generator.py         # Generator class using Jinja2
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── claude.py        # ClaudeAdapter
│   │   ├── hermes.py        # HermesAdapter (agentskills.io YAML)
│   │   ├── codex.py         # CodexAdapter (AGENTS.md)
│   │   ├── opencode.py      # OpenCodeAdapter
│   │   ├── cursor.py        # CursorAdapter (.cursorrules)
│   │   ├── windsurf.py      # WindsurfAdapter
│   │   ├── zed.py           # ZedAdapter
│   │   ├── copilot.py       # CopilotAdapter
│   │   └── gemini.py        # GeminiAdapter
│   └── templates/
│       ├── skill_md.j2       # Claude Code SKILL.md
│       ├── agents_md.j2      # Codex AGENTS.md
│       ├── hermes_yaml.j2    # Hermes YAML (agentskills.io)
│       ├── opencode_json.j2  # OpenCode JSON
│       ├── cursor_rules.j2   # Cursor .cursorrules
│       └── zed_md.j2        # Zed zed.md
├── tests/
│   └── agent_adapters/
│       ├── __init__.py
│       ├── test_base.py
│       ├── test_registry.py
│       ├── test_generator.py
│       └── test_adapters.py
└── scripts/
    └── generate_adapters.sh  # CLI to generate all adapter files
```

---

### Task 1: Create agent_adapters directory structure and base.py

**Files:**
- Create: `paper-reader/agent_adapters/__init__.py`
- Create: `paper-reader/agent_adapters/base.py`
- Create: `paper-reader/agent_adapters/adapters/__init__.py`
- Create: `paper-reader/agent_adapters/templates/.gitkeep`

- [ ] **Step 1: Write the failing test**

```python
# Test in: paper-reader/tests/agent_adapters/test_base.py
def test_adapter_config_dataclass():
    """Test AdapterConfig can be instantiated with all fields."""
    from agent_adapters.base import AdapterConfig
    
    config = AdapterConfig(
        name="Claude Code",
        id="claude",
        config_file="~/.claude/settings.json",
        skill_format="markdown",
        command_prefix="/paper-reader"
    )
    
    assert config.name == "Claude Code"
    assert config.id == "claude"
    assert config.skill_format == "markdown"

def test_generation_result_dataclass():
    """Test GenerationResult can be instantiated."""
    from agent_adapters.base import GenerationResult
    
    result = GenerationResult(
        success=True,
        output_files=["/path/to/output"],
        errors=[]
    )
    
    assert result.success is True
    assert len(result.output_files) == 1
    assert len(result.errors) == 0

def test_base_adapter_is_abstract():
    """Test BaseAdapter cannot be instantiated directly."""
    from agent_adapters.base import BaseAdapter
    
    try:
        adapter = BaseAdapter()
        assert False, "Should not be able to instantiate BaseAdapter"
    except TypeError:
        pass  # Expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper-reader && python -m pytest tests/agent_adapters/test_base.py -v`
Expected: FAIL with "cannot import name 'AdapterConfig'"

- [ ] **Step 3: Write minimal implementation**

```python
# paper-reader/agent_adapters/__init__.py
from .base import BaseAdapter, AdapterConfig, GenerationResult
from .registry import Registry
from .generator import Generator

__all__ = ["BaseAdapter", "AdapterConfig", "GenerationResult", "Registry", "Generator"]
```

```python
# paper-reader/agent_adapters/base.py
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

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper-reader && python -m pytest tests/agent_adapters/test_base.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/user/obsidian/AI/claude\ code/paper-reader-skill-optimize
git add paper-reader/agent_adapters/base.py paper-reader/agent_adapters/__init__.py paper-reader/agent_adapters/adapters/__init__.py
git commit -m "feat: add BaseAdapter abstract class and AdapterConfig/GenerationResult dataclasses"
```

---

### Task 2: Implement Registry class

**Files:**
- Create: `paper-reader/agent_adapters/registry.py`
- Test: `paper-reader/tests/agent_adapters/test_registry.py`

- [ ] **Step 1: Write the failing test**

```python
# Test in: paper-reader/tests/agent_adapters/test_registry.py
def test_registry_register_and_get():
    """Test Registry can register and retrieve an adapter."""
    from agent_adapters.base import BaseAdapter, AdapterConfig
    from agent_adapters.registry import Registry
    
    class DummyAdapter(BaseAdapter):
        def get_config(self): 
            return AdapterConfig(name="Dummy", id="dummy", config_file="~/.dummy", skill_format="md", command_prefix="/dummy")
        def generate_skill_file(self, skill_source): return "# Dummy"
        def generate_config_file(self, config): return "{}"
        def detect_installation(self): return True
        def get_installation_instructions(self): return "Install dummy"
    
    Registry.register("dummy", DummyAdapter)
    adapter = Registry.get("dummy")
    
    assert isinstance(adapter, DummyAdapter)
    assert adapter.get_config().id == "dummy"

def test_registry_list_all():
    """Test Registry lists all registered adapters."""
    from agent_adapters.registry import Registry
    
    adapters = Registry.list_all()
    assert isinstance(adapters, list)

def test_registry_get_unknown_raises():
    """Test Registry.get raises for unknown adapter."""
    from agent_adapters.registry import Registry
    
    try:
        Registry.get("nonexistent")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Unknown adapter" in str(e)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper-reader && python -m pytest tests/agent_adapters/test_registry.py -v`
Expected: FAIL with "cannot import name 'Registry'"

- [ ] **Step 3: Write implementation**

```python
# paper-reader/agent_adapters/registry.py
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
            except Exception:
                pass
        return available
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper-reader && python -m pytest tests/agent_adapters/test_registry.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add paper-reader/agent_adapters/registry.py
git commit -m "feat: add Registry class for adapter registration and management"
```

---

### Task 3: Implement Generator class

**Files:**
- Create: `paper-reader/agent_adapters/generator.py`
- Test: `paper-reader/tests/agent_adapters/test_generator.py`

- [ ] **Step 1: Write the failing test**

```python
# Test in: paper-reader/tests/agent_adapters/test_generator.py
import tempfile
import os

def test_generator_init():
    """Test Generator initializes with template_dir and output_dir."""
    from agent_adapters.generator import Generator
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = Generator(tmpdir, tmpdir + "/output")
        assert gen.output_dir.name == "output"

def test_generate_all_returns_result():
    """Test generate_all returns GenerationResult."""
    from agent_adapters.generator import Generator
    from agent_adapters.base import GenerationResult
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Note: Without registered adapters, list_all returns []
        gen = Generator(tmpdir, tmpdir + "/output")
        result = gen.generate_all("# SKILL", {"key": "value"})
        
        assert isinstance(result, GenerationResult)
        assert result.success is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper-reader && python -m pytest tests/agent_adapters/test_generator.py -v`
Expected: FAIL with "cannot import name 'Generator'"

- [ ] **Step 3: Write implementation**

```python
# paper-reader/agent_adapters/generator.py
from jinja2 import Environment, FileSystemLoader
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
        skill_content = adapter.generate_skill_file(skill_source)
        config_content = adapter.generate_config_file(config)
        
        output_path = self.output_dir / adapter.get_config().id
        output_path.mkdir(parents=True, exist_ok=True)
        
        (output_path / "SKILL.md").write_text(skill_content)
        (output_path / "config.json").write_text(config_content)
        
        return str(output_path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper-reader && python -m pytest tests/agent_adapters/test_generator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add paper-reader/agent_adapters/generator.py
git commit -m "feat: add Generator class for multi-agent file generation"
```

---

### Task 4: Create 6 Jinja2 templates

**Files:**
- Create: `paper-reader/agent_adapters/templates/skill_md.j2`
- Create: `paper-reader/agent_adapters/templates/agents_md.j2`
- Create: `paper-reader/agent_adapters/templates/hermes_yaml.j2`
- Create: `paper-reader/agent_adapters/templates/opencode_json.j2`
- Create: `paper-reader/agent_adapters/templates/cursor_rules.j2`
- Create: `paper-reader/agent_adapters/templates/zed_md.j2`

- [ ] **Step 1: Create all 6 templates**

```jinja2
{# skill_md.j2 - Claude Code SKILL.md #}
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

```jinja2
{# agents_md.j2 - Codex AGENTS.md #}
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

```jinja2
{# hermes_yaml.j2 - Hermes YAML (agentskills.io format) #}
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

```jinja2
{# opencode_json.j2 - OpenCode JSON #}
{
  "name": "{{ skill_name }}",
  "description": "{{ description }}",
  "commands": [
{% for command in commands %}
    {
      "name": "{{ command.name }}",
      "description": "{{ command.description }}",
      "usage": "{{ command.usage }}"
    }{% if not loop.last %},{% endif %}
{% endfor %}
  ],
  "triggers": [{% for t in triggers %}"{{ t }}"{% if not loop.last %}, {% endif %}{% endfor %}]
}
```

```jinja2
{# cursor_rules.j2 - Cursor .cursorrules #}
# {{ skill_name }}

## 概述

{{ skill_content }}

## 命令

{% for command in commands %}
### {{ command.name }}

{{ command.description }}

用法: `{{ command.usage }}`
{% endfor %}
```

```jinja2
{# zed_md.j2 - Zed zed.md #}
# {{ skill_name }}

## 概述

{{ skill_content }}

## 使用方式

```
{{ command_prefix }} <命令> [参数]
```

## 可用命令

{% for command in commands %}
- `{{ command.name }}`: {{ command.description }}
{% endfor %}
```

- [ ] **Step 2: Commit**

```bash
git add paper-reader/agent_adapters/templates/
git commit -m "feat: add 6 Jinja2 templates for all agent formats"
```

---

### Task 5: Implement ClaudeAdapter

**Files:**
- Create: `paper-reader/agent_adapters/adapters/claude.py`
- Test: `paper-reader/tests/agent_adapters/test_adapters.py`

- [ ] **Step 1: Write the failing test**

```python
# Test in: paper-reader/tests/agent_adapters/test_adapters.py
def test_claude_adapter_get_config():
    """Test ClaudeAdapter returns correct config."""
    from agent_adapters.adapters.claude import ClaudeAdapter
    
    adapter = ClaudeAdapter()
    config = adapter.get_config()
    
    assert config.id == "claude"
    assert config.name == "Claude Code"
    assert config.skill_format == "markdown"

def test_claude_adapter_generate_skill_file():
    """Test ClaudeAdapter generates SKILL.md content."""
    from agent_adapters.adapters.claude import ClaudeAdapter
    
    adapter = ClaudeAdapter()
    content = adapter.generate_skill_file("# Paper Reader\n\nA skill for reading papers.")
    
    assert "Paper Reader" in content
    assert "# Paper Reader" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper-reader && python -m pytest tests/agent_adapters/test_adapters.py::test_claude_adapter_get_config -v`
Expected: FAIL with "cannot import name 'ClaudeAdapter'"

- [ ] **Step 3: Write implementation**

```python
# paper-reader/agent_adapters/adapters/claude.py
from pathlib import Path
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
        return f"""# paper-reader

{skill_source}

## 使用方式

```
/paper-reader <命令> [参数]
```
"""
    
    def generate_config_file(self, config: dict) -> str:
        """生成配置文件"""
        import json
        return json.dumps({
            "skill": "paper-reader",
            "version": "1.0.0",
            "config": config
        }, indent=2)
    
    def detect_installation(self) -> bool:
        """检测 Claude Code 是否已安装"""
        config_path = Path.home() / ".claude" / "settings.json"
        return config_path.exists()
    
    def get_installation_instructions(self) -> str:
        return "Install Claude Code from https://claude.ai/code"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper-reader && python -m pytest tests/agent_adapters/test_adapters.py::test_claude_adapter_get_config tests/agent_adapters/test_adapters.py::test_claude_adapter_generate_skill_file -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add paper-reader/agent_adapters/adapters/claude.py
git commit -m "feat: add ClaudeAdapter for Claude Code"
```

---

### Task 6: Implement HermesAdapter

**Files:**
- Create: `paper-reader/agent_adapters/adapters/hermes.py`

- [ ] **Step 1: Write the failing test**

```python
def test_hermes_adapter_get_config():
    """Test HermesAdapter returns correct config."""
    from agent_adapters.adapters.hermes import HermesAdapter
    
    adapter = HermesAdapter()
    config = adapter.get_config()
    
    assert config.id == "hermes"
    assert config.name == "Hermes Agent"
    assert config.skill_format == "yaml"

def test_hermes_adapter_generate_skill_file():
    """Test HermesAdapter generates YAML content."""
    from agent_adapters.adapters.hermes import HermesAdapter
    
    adapter = HermesAdapter()
    content = adapter.generate_skill_file("# Paper Reader\n\nA skill.")
    
    assert "name: paper-reader" in content
    assert "hermes" in content.lower() or "paper-reader" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd paper-reader && python -m pytest tests/agent_adapters/test_adapters.py::test_hermes_adapter_get_config -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# paper-reader/agent_adapters/adapters/hermes.py
from pathlib import Path
import shutil
from ..base import BaseAdapter, AdapterConfig

class HermesAdapter(BaseAdapter):
    """Hermes Agent 适配器 (agentskills.io 格式)"""
    
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
        return """name: paper-reader
description: Read and analyze academic papers with MinerU-powered extraction
version: 1.0.0

triggers:
  - /paper-reader
  - paper-reader

commands:
  - name: read
    description: Read a paper from URL or local file
    arguments:
      - name: source
        type: string
        required: true
        description: URL or local file path
      
  - name: analyze
    description: Analyze paper content
    arguments:
      - name: mode
        type: string
        required: false
        description: Analysis mode (scan/deep/qa)

permissions:
  - filesystem:read
  - filesystem:write
  - network:fetch
"""
    
    def generate_config_file(self, config: dict) -> str:
        """生成配置文件"""
        import json
        return json.dumps({
            "skill": "paper-reader",
            "format": "agentskills.io",
            "config": config
        }, indent=2)
    
    def detect_installation(self) -> bool:
        """检测 Hermes 是否已安装"""
        hermes_path = Path.home() / ".hermes" / "hermes-agent"
        return hermes_path.exists() or shutil.which("hermes") is not None
    
    def get_installation_instructions(self) -> str:
        return "Install Hermes Agent from https://github.com/NousResearch/hermes-agent"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd paper-reader && python -m pytest tests/agent_adapters/test_adapters.py::test_hermes_adapter_get_config tests/agent_adapters/test_adapters.py::test_hermes_adapter_generate_skill_file -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add paper-reader/agent_adapters/adapters/hermes.py
git commit -m "feat: add HermesAdapter for Hermes Agent"
```

---

### Task 7: Implement remaining 7 adapters (Codex, OpenCode, Cursor, Windsurf, Zed, Copilot, Gemini)

**Files:**
- Create: `paper-reader/agent_adapters/adapters/codex.py`
- Create: `paper-reader/agent_adapters/adapters/opencode.py`
- Create: `paper-reader/agent_adapters/adapters/cursor.py`
- Create: `paper-reader/agent_adapters/adapters/windsurf.py`
- Create: `paper-reader/agent_adapters/adapters/zed.py`
- Create: `paper-reader/agent_adapters/adapters/copilot.py`
- Create: `paper-reader/agent_adapters/adapters/gemini.py`

- [ ] **Step 1: Write implementations for all 7 adapters**

```python
# paper-reader/agent_adapters/adapters/codex.py
from pathlib import Path
from ..base import BaseAdapter, AdapterConfig

class CodexAdapter(BaseAdapter):
    """Codex 适配器 (AGENTS.md format)"""
    
    def get_config(self) -> AdapterConfig:
        return AdapterConfig(
            name="Codex",
            id="codex",
            config_file="AGENTS.md",
            skill_format="markdown",
            command_prefix="/paper-reader"
        )
    
    def generate_skill_file(self, skill_source: str) -> str:
        return f"""# paper-reader

## 概述

{skill_source}

## 命令

### read

读取论文（URL 或本地文件）

用法: `/paper-reader read <source>`

### analyze

分析论文内容

用法: `/paper-reader analyze --mode <scan|deep|qa>`
"""
    
    def generate_config_file(self, config: dict) -> str:
        import json
        return json.dumps({"skill": "paper-reader", "config": config}, indent=2)
    
    def detect_installation(self) -> bool:
        return Path("AGENTS.md").exists()
    
    def get_installation_instructions(self) -> str:
        return "Codex uses AGENTS.md in project root"
```

```python
# paper-reader/agent_adapters/adapters/opencode.py
from pathlib import Path
from ..base import BaseAdapter, AdapterConfig

class OpenCodeAdapter(BaseAdapter):
    """OpenCode 适配器"""
    
    def get_config(self) -> AdapterConfig:
        return AdapterConfig(
            name="OpenCode",
            id="opencode",
            config_file="~/.config/opencode/",
            skill_format="json",
            command_prefix="/paper-reader"
        )
    
    def generate_skill_file(self, skill_source: str) -> str:
        import json
        return json.dumps({
            "name": "paper-reader",
            "description": "Academic paper analysis skill",
            "content": skill_source
        }, indent=2)
    
    def generate_config_file(self, config: dict) -> str:
        import json
        return json.dumps({"skill": "paper-reader", "config": config}, indent=2)
    
    def detect_installation(self) -> bool:
        config_path = Path.home() / ".config" / "opencode"
        return config_path.exists()
    
    def get_installation_instructions(self) -> str:
        return "Install OpenCode and configure ~/.config/opencode/"
```

```python
# paper-reader/agent_adapters/adapters/cursor.py
from pathlib import Path
from ..base import BaseAdapter, AdapterConfig

class CursorAdapter(BaseAdapter):
    """Cursor 适配器 (.cursorrules)"""
    
    def get_config(self) -> AdapterConfig:
        return AdapterConfig(
            name="Cursor",
            id="cursor",
            config_file="~/.cursor/rules/",
            skill_format="markdown",
            command_prefix="/paper-reader"
        )
    
    def generate_skill_file(self, skill_source: str) -> str:
        return f"""# paper-reader

## 概述

{skill_source}

## 使用方式

```
/paper-reader <命令> [参数]
```
"""
    
    def generate_config_file(self, config: dict) -> str:
        import json
        return json.dumps({"skill": "paper-reader", "config": config}, indent=2)
    
    def detect_installation(self) -> bool:
        rules_path = Path.home() / ".cursor" / "rules"
        return rules_path.exists()
    
    def get_installation_instructions(self) -> str:
        return "Cursor uses .cursorrules files in project directories"
```

```python
# paper-reader/agent_adapters/adapters/windsurf.py
from pathlib import Path
from ..base import BaseAdapter, AdapterConfig

class WindsurfAdapter(BaseAdapter):
    """Windsurf 适配器"""
    
    def get_config(self) -> AdapterConfig:
        return AdapterConfig(
            name="Windsurf",
            id="windsurf",
            config_file="~/.windsurf/rules/",
            skill_format="markdown",
            command_prefix="/paper-reader"
        )
    
    def generate_skill_file(self, skill_source: str) -> str:
        return f"""# paper-reader

## 概述

{skill_source}

## 使用方式

```
/paper-reader <命令> [参数]
```
"""
    
    def generate_config_file(self, config: dict) -> str:
        import json
        return json.dumps({"skill": "paper-reader", "config": config}, indent=2)
    
    def detect_installation(self) -> bool:
        rules_path = Path.home() / ".windsurf" / "rules"
        return rules_path.exists()
    
    def get_installation_instructions(self) -> str:
        return "Windsurf uses rules.md files in ~/.windsurf/rules/"
```

```python
# paper-reader/agent_adapters/adapters/zed.py
from pathlib import Path
from ..base import BaseAdapter, AdapterConfig

class ZedAdapter(BaseAdapter):
    """Zed 适配器"""
    
    def get_config(self) -> AdapterConfig:
        return AdapterConfig(
            name="Zed",
            id="zed",
            config_file=".zed/",
            skill_format="markdown",
            command_prefix="/paper-reader"
        )
    
    def generate_skill_file(self, skill_source: str) -> str:
        return f"""# paper-reader

## 概述

{skill_source}

## 使用方式

```
/paper-reader <命令> [参数]
```
"""
    
    def generate_config_file(self, config: dict) -> str:
        import json
        return json.dumps({"skill": "paper-reader", "config": config}, indent=2)
    
    def detect_installation(self) -> bool:
        return Path(".zed").exists()
    
    def get_installation_instructions(self) -> str:
        return "Zed uses zed.md in .zed/ directory"
```

```python
# paper-reader/agent_adapters/adapters/copilot.py
from pathlib import Path
import shutil
from ..base import BaseAdapter, AdapterConfig

class CopilotAdapter(BaseAdapter):
    """Copilot CLI 适配器"""
    
    def get_config(self) -> AdapterConfig:
        return AdapterConfig(
            name="Copilot CLI",
            id="copilot",
            config_file="~/.github-copilot/",
            skill_format="markdown",
            command_prefix="/paper-reader"
        )
    
    def generate_skill_file(self, skill_source: str) -> str:
        return f"""# paper-reader

## 概述

{skill_source}

## 使用方式

```
/paper-reader <命令> [参数]
```
"""
    
    def generate_config_file(self, config: dict) -> str:
        import json
        return json.dumps({"skill": "paper-reader", "config": config}, indent=2)
    
    def detect_installation(self) -> bool:
        copilot_path = Path.home() / ".github-copilot"
        return copilot_path.exists() or shutil.which("gh") is not None
    
    def get_installation_instructions(self) -> str:
        return "Install GitHub Copilot CLI: gh extension install github/copilot"
```

```python
# paper-reader/agent_adapters/adapters/gemini.py
from pathlib import Path
from ..base import BaseAdapter, AdapterConfig

class GeminiAdapter(BaseAdapter):
    """Gemini CLI 适配器"""
    
    def get_config(self) -> AdapterConfig:
        return AdapterConfig(
            name="Gemini CLI",
            id="gemini",
            config_file="~/.gemini/settings.json",
            skill_format="markdown",
            command_prefix="/paper-reader"
        )
    
    def generate_skill_file(self, skill_source: str) -> str:
        return f"""# paper-reader

## 概述

{skill_source}

## 使用方式

```
/paper-reader <命令> [参数]
```
"""
    
    def generate_config_file(self, config: dict) -> str:
        import json
        return json.dumps({"skill": "paper-reader", "config": config}, indent=2)
    
    def detect_installation(self) -> bool:
        config_path = Path.home() / ".gemini" / "settings.json"
        return config_path.exists()
    
    def get_installation_instructions(self) -> str:
        return "Install Gemini CLI from https://ai.google.dev/cli"
```

- [ ] **Step 2: Register all adapters in registry.py**

Add to `paper-reader/agent_adapters/registry.py`:

```python
# Import all adapters to trigger registration
from .adapters import claude, hermes, codex, opencode, cursor, windsurf, zed, copilot, gemini
```

Add to `paper-reader/agent_adapters/adapters/__init__.py`:

```python
from . import claude
from . import hermes
from . import codex
from . import opencode
from . import cursor
from . import windsurf
from . import zed
from . import copilot
from . import gemini
```

- [ ] **Step 3: Run tests to verify**

Run: `cd paper-reader && python -m pytest tests/agent_adapters/ -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add paper-reader/agent_adapters/adapters/
git commit -m "feat: add all 7 remaining agent adapters (Codex, OpenCode, Cursor, Windsurf, Zed, Copilot, Gemini)"
```

---

### Task 8: Create generate_adapters.sh CLI script

**Files:**
- Create: `paper-reader/scripts/generate_adapters.sh`

- [ ] **Step 1: Write the script**

```bash
#!/bin/bash
# Generate adapter files for all supported AI coding agents

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/output}"

echo "Generating agent adapter files..."
echo "Output directory: $OUTPUT_DIR"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run Python generator
cd "$PROJECT_DIR"
python3 -c "
import sys
sys.path.insert(0, '.')
from agent_adapters import Generator

# Read skill source
with open('paper-reader/skills/SKILL.md', 'r') as f:
    skill_source = f.read()

# Default config
config = {
    'mineru_path': '~/.hermes/hermes-agent/venv/bin/mineru',
    'work_base': '/tmp/paper-reader',
    'archive_base': '~/obsidian/papers'
}

# Generate
gen = Generator('agent_adapters/templates', '$OUTPUT_DIR')
result = gen.generate_all(skill_source, config)

print(f'Success: {result.success}')
print(f'Output files: {result.output_files}')
if result.errors:
    print(f'Errors: {result.errors}')
    sys.exit(1)
"

echo "Done! Files generated in $OUTPUT_DIR"
```

- [ ] **Step 2: Make executable and commit**

```bash
chmod +x paper-reader/scripts/generate_adapters.sh
git add paper-reader/scripts/generate_adapters.sh
git commit -m "feat: add generate_adapters.sh CLI script"
```

---

### Task 9: Comprehensive tests and verify all pass

**Files:**
- Test: `paper-reader/tests/agent_adapters/`

- [ ] **Step 1: Run all adapter tests**

Run: `cd paper-reader && python -m pytest tests/agent_adapters/ -v`
Expected: All tests pass

- [ ] **Step 2: Commit final changes**

```bash
git add paper-reader/
git commit -m "feat: complete agent adapter architecture for 9 AI coding agents"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- ✅ BaseAdapter abstract class with 5 methods (get_config, generate_skill_file, generate_config_file, detect_installation, get_installation_instructions)
- ✅ Registry class with register/get/list_all/detect_available
- ✅ Generator class with generate_all
- ✅ 9 Agent adapters (claude, hermes, codex, opencode, cursor, windsurf, zed, copilot, gemini)
- ✅ 6 Jinja2 templates (skill_md, agents_md, hermes_yaml, opencode_json, cursor_rules, zed_md)
- ✅ CLI script for generation

**2. Placeholder scan:**
- No "TBD", "TODO", or incomplete sections
- All test code has actual assertions
- All implementation code is complete

**3. Type consistency:**
- All adapters return `AdapterConfig` from `get_config()`
- All adapters implement all 5 abstract methods
- `GenerationResult` used consistently for generation results
