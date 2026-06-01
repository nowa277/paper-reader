"""Tests for agent_adapters base classes."""

import sys
from pathlib import Path
import importlib.util

# Dynamically load the base module to avoid import conflicts
base_file = Path(__file__).parent.parent.parent / "agent_adapters" / "base.py"
spec = importlib.util.spec_from_file_location("agent_adapters_base", base_file)
base_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_module)

AdapterConfig = base_module.AdapterConfig
GenerationResult = base_module.GenerationResult
BaseAdapter = base_module.BaseAdapter


def test_adapter_config_dataclass():
    """Test AdapterConfig can be instantiated with all fields."""
    config = AdapterConfig(
        name="Claude Code",
        id="claude",
        config_file="~/.claude/settings.json",
        skill_format="markdown",
        command_prefix="/paper-reader"
    )

    assert config.name == "Claude Code"
    assert config.id == "claude"
    assert config.skill_format == "markdown"


def test_generation_result_dataclass():
    """Test GenerationResult can be instantiated."""
    result = GenerationResult(
        success=True,
        output_files=["/path/to/output"],
        errors=[]
    )

    assert result.success is True
    assert len(result.output_files) == 1
    assert len(result.errors) == 0


def test_base_adapter_is_abstract():
    """Test BaseAdapter cannot be instantiated directly."""
    try:
        adapter = BaseAdapter()
        assert False, "Should not be able to instantiate BaseAdapter"
    except TypeError:
        pass  # Expected
