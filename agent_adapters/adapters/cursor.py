import json
from pathlib import Path
from ..base import BaseAdapter, AdapterConfig


class CursorAdapter(BaseAdapter):
    """Cursor adapter (.cursorrules)"""

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
        return json.dumps({"skill": "paper-reader", "config": config}, indent=2)

    def detect_installation(self) -> bool:
        rules_path = Path.home() / ".cursor" / "rules"
        return rules_path.exists()

    def get_installation_instructions(self) -> str:
        return "Cursor uses .cursorrules files in project directories"
