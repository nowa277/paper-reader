import json
from pathlib import Path
from ..base import BaseAdapter, AdapterConfig


class CodexAdapter(BaseAdapter):
    """Codex adapter (AGENTS.md format)"""

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
        return json.dumps({"skill": "paper-reader", "config": config}, indent=2)

    def detect_installation(self) -> bool:
        return Path("AGENTS.md").exists()

    def get_installation_instructions(self) -> str:
        return "Codex uses AGENTS.md in project root"
