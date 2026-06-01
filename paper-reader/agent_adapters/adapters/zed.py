from pathlib import Path
from ..base import BaseAdapter, AdapterConfig


class ZedAdapter(BaseAdapter):
    """Zed adapter"""

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
