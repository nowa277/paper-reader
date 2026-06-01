from pathlib import Path
from ..base import BaseAdapter, AdapterConfig


class WindsurfAdapter(BaseAdapter):
    """Windsurf adapter"""

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
