from pathlib import Path
import shutil
from ..base import BaseAdapter, AdapterConfig


class HermesAdapter(BaseAdapter):
    """Hermes Agent adapter (agentskills.io format)"""

    def get_config(self) -> AdapterConfig:
        return AdapterConfig(
            name="Hermes Agent",
            id="hermes",
            config_file="~/.hermes/skills/",
            skill_format="yaml",
            command_prefix="/paper-reader"
        )

    def generate_skill_file(self, skill_source: str) -> str:
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
        import json
        return json.dumps({
            "skill": "paper-reader",
            "format": "agentskills.io",
            "config": config
        }, indent=2)

    def detect_installation(self) -> bool:
        hermes_path = Path.home() / ".hermes" / "hermes-agent"
        return hermes_path.exists() or shutil.which("hermes") is not None

    def get_installation_instructions(self) -> str:
        return "Install Hermes Agent from https://github.com/NousResearch/hermes-agent"
