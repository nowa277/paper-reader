from pathlib import Path
from ..base import BaseAdapter, AdapterConfig


class OpenCodeAdapter(BaseAdapter):
    """OpenCode adapter"""

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
