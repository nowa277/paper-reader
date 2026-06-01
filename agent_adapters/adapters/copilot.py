import json
from pathlib import Path
import shutil
from ..base import BaseAdapter, AdapterConfig


class CopilotAdapter(BaseAdapter):
    """Copilot CLI adapter"""

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
        return json.dumps({"skill": "paper-reader", "config": config}, indent=2)

    def detect_installation(self) -> bool:
        copilot_path = Path.home() / ".github-copilot"
        return copilot_path.exists() or shutil.which("gh") is not None

    def get_installation_instructions(self) -> str:
        return "Install GitHub Copilot CLI: gh extension install github/copilot"
