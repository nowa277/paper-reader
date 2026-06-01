"""Tests for agent_adapters registry."""
import sys
from pathlib import Path

# Prepend paper-reader path to sys.path BEFORE any other imports
_paper_reader_path = str(Path(__file__).parent.parent.parent)
if _paper_reader_path not in sys.path:
    sys.path.insert(0, _paper_reader_path)

from agent_adapters.base import BaseAdapter, AdapterConfig
from agent_adapters.registry import Registry


def test_registry_register_and_get():
    """Test Registry can register and retrieve an adapter."""
    class DummyAdapter(BaseAdapter):
        def get_config(self):
            return AdapterConfig(name="Dummy", id="dummy", config_file="~/.dummy", skill_format="md", command_prefix="/dummy")
        def generate_skill_file(self, skill_source): return "# Dummy"
        def generate_config_file(self, config): return "{}"
        def detect_installation(self): return True
        def get_installation_instructions(self): return "Install dummy"

    Registry.register("dummy", DummyAdapter)
    adapter = Registry.get("dummy")

    assert isinstance(adapter, DummyAdapter)
    assert adapter.get_config().id == "dummy"


def test_registry_list_all():
    """Test Registry lists all registered adapters."""
    adapters = Registry.list_all()
    assert isinstance(adapters, list)


def test_registry_get_unknown_raises():
    """Test Registry.get raises for unknown adapter."""
    try:
        Registry.get("nonexistent")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Unknown adapter" in str(e)
