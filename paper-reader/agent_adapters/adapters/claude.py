from pathlib import Path
from ..base import BaseAdapter, AdapterConfig


class ClaudeAdapter(BaseAdapter):
    """Claude Code adapter"""

    def get_config(self) -> AdapterConfig:
        return AdapterConfig(
            name="Claude Code",
            id="claude",
            config_file="~/.claude/settings.json",
            skill_format="markdown",
            command_prefix="/paper-reader"
        )

    def generate_skill_file(self, skill_source: str) -> str:
        return f"""# paper-reader

{skill_source}

## 使用方式

```
/paper-reader <命令> [参数]
```
"""

    def generate_config_file(self, config: dict) -> str:
        import json
        return json.dumps({
            "skill": "paper-reader",
            "version": "1.0.0",
            "config": config
        }, indent=2)

    def detect_installation(self) -> bool:
        config_path = Path.home() / ".claude" / "settings.json"
        return config_path.exists()

    def get_installation_instructions(self) -> str:
        return "Install Claude Code from https://claude.ai/code"
