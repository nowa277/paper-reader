import json
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
        """Generate Hermes YAML using hermes_yaml.j2 template."""
        from ..generator import Generator
        import os
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        gen = Generator(template_dir, '/tmp')
        return gen.render_hermes_template({
            'skill_name': 'paper-reader',
            'description': skill_source.split('\n')[0] if skill_source else 'Paper Reader skill',
            'triggers': ['/paper-reader', 'paper-reader'],
            'commands': [
                {'name': 'read', 'description': 'Read a paper from URL or local file',
                 'arguments': [{'name': 'source', 'type': 'string', 'required': True, 'description': 'URL or local file path'}]},
                {'name': 'analyze', 'description': 'Analyze paper content',
                 'arguments': [{'name': 'mode', 'type': 'string', 'required': False, 'description': 'Analysis mode (scan/deep/qa)'}]}
            ]
        })

    def generate_config_file(self, config: dict) -> str:
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
