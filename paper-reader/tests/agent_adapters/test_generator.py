"""Tests for agent_adapters Generator class."""

import sys
from pathlib import Path
import importlib.util
import tempfile

# Dynamically load the base module to avoid import conflicts
base_file = Path(__file__).parent.parent.parent / "agent_adapters" / "base.py"
spec = importlib.util.spec_from_file_location("agent_adapters_base", base_file)
base_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_module)

GenerationResult = base_module.GenerationResult

# Now dynamically load generator, which imports from .base using relative imports
# We need to first make base available as a module
sys.modules['agent_adapters.base'] = base_module

generator_file = Path(__file__).parent.parent.parent / "agent_adapters" / "generator.py"
gen_spec = importlib.util.spec_from_file_location("agent_adapters.generator", generator_file)
generator_module = importlib.util.module_from_spec(gen_spec)
gen_spec.loader.exec_module(generator_module)

Generator = generator_module.Generator


def test_generator_init():
    """Test Generator initializes with template_dir and output_dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = Generator(tmpdir, tmpdir + "/output")
        assert gen.output_dir.name == "output"


def test_generate_all_returns_result():
    """Test generate_all returns GenerationResult."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Note: Without registered adapters, list_all returns []
        gen = Generator(tmpdir, tmpdir + "/output")
        result = gen.generate_all("# SKILL", {"key": "value"})

        assert isinstance(result, GenerationResult)
        assert result.success is True