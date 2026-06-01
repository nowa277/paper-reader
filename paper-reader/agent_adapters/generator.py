from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from .base import BaseAdapter, GenerationResult
from .registry import Registry


class Generator:
    """Multi-agent skill file generator"""

    def __init__(self, template_dir: str, output_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.output_dir = Path(output_dir)

    def generate_all(self, skill_source: str, config: dict) -> GenerationResult:
        """Generate skill files for all registered adapters"""
        results = []
        errors = []

        for adapter_id in Registry.list_all():
            try:
                adapter = Registry.get(adapter_id)
                output_path = self._generate_for_adapter(adapter, skill_source, config)
                results.append(output_path)
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
        """Generate files for a single adapter"""
        skill_content = adapter.generate_skill_file(skill_source)
        config_content = adapter.generate_config_file(config)

        adapter_id = adapter.get_config().id
        output_path = self.output_dir / adapter_id
        output_path.mkdir(parents=True, exist_ok=True)

        (output_path / "SKILL.md").write_text(skill_content)
        (output_path / "config.json").write_text(config_content)

        return str(output_path)
