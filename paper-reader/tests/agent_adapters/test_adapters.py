"""Tests for all agent adapters."""

# Imports should work via conftest.py which adds paper-reader to sys.path
from agent_adapters.adapters.claude import ClaudeAdapter
from agent_adapters.adapters.hermes import HermesAdapter
from agent_adapters.adapters.codex import CodexAdapter
from agent_adapters.adapters.opencode import OpenCodeAdapter
from agent_adapters.adapters.cursor import CursorAdapter
from agent_adapters.adapters.windsurf import WindsurfAdapter
from agent_adapters.adapters.zed import ZedAdapter
from agent_adapters.adapters.copilot import CopilotAdapter
from agent_adapters.adapters.gemini import GeminiAdapter
from agent_adapters.registry import Registry
from agent_adapters.base import AdapterConfig, BaseAdapter


# --- ClaudeAdapter tests ---

def test_claude_adapter_get_config():
    """Test ClaudeAdapter returns correct config."""
    adapter = ClaudeAdapter()
    config = adapter.get_config()
    
    assert config.id == "claude"
    assert config.name == "Claude Code"
    assert config.skill_format == "markdown"


def test_claude_adapter_generate_skill_file():
    """Test ClaudeAdapter generates SKILL.md content."""
    adapter = ClaudeAdapter()
    content = adapter.generate_skill_file("# Paper Reader\n\nA skill for reading papers.")
    
    assert "Paper Reader" in content
    assert "# paper-reader" in content


def test_claude_adapter_detect_installation():
    """Test ClaudeAdapter detect_installation returns a bool."""
    adapter = ClaudeAdapter()
    result = adapter.detect_installation()
    assert isinstance(result, bool)


# --- HermesAdapter tests ---

def test_hermes_adapter_get_config():
    """Test HermesAdapter returns correct config."""
    adapter = HermesAdapter()
    config = adapter.get_config()
    
    assert config.id == "hermes"
    assert config.name == "Hermes Agent"
    assert config.skill_format == "yaml"


def test_hermes_adapter_generate_skill_file():
    """Test HermesAdapter generates YAML content."""
    adapter = HermesAdapter()
    content = adapter.generate_skill_file("# Paper Reader\n\nA skill.")
    
    assert "name: paper-reader" in content
    assert "hermes" in content.lower() or "paper-reader" in content


# --- CodexAdapter tests ---

def test_codex_adapter_get_config():
    """Test CodexAdapter returns correct config."""
    adapter = CodexAdapter()
    config = adapter.get_config()
    
    assert config.id == "codex"
    assert config.name == "Codex"
    assert config.skill_format == "markdown"


def test_codex_adapter_generate_skill_file():
    """Test CodexAdapter generates content."""
    adapter = CodexAdapter()
    content = adapter.generate_skill_file("# Paper Reader\n\nA skill.")
    
    assert "Paper Reader" in content


# --- OpenCodeAdapter tests ---

def test_opencode_adapter_get_config():
    """Test OpenCodeAdapter returns correct config."""
    adapter = OpenCodeAdapter()
    config = adapter.get_config()
    
    assert config.id == "opencode"
    assert config.name == "OpenCode"
    assert config.skill_format == "json"


def test_opencode_adapter_generate_skill_file():
    """Test OpenCodeAdapter generates JSON content."""
    adapter = OpenCodeAdapter()
    content = adapter.generate_skill_file("# Paper Reader\n\nA skill.")
    
    assert "paper-reader" in content


# --- CursorAdapter tests ---

def test_cursor_adapter_get_config():
    """Test CursorAdapter returns correct config."""
    adapter = CursorAdapter()
    config = adapter.get_config()
    
    assert config.id == "cursor"
    assert config.name == "Cursor"
    assert config.skill_format == "markdown"


def test_cursor_adapter_generate_skill_file():
    """Test CursorAdapter generates content."""
    adapter = CursorAdapter()
    content = adapter.generate_skill_file("# Paper Reader\n\nA skill.")
    
    assert "Paper Reader" in content


# --- WindsurfAdapter tests ---

def test_windsurf_adapter_get_config():
    """Test WindsurfAdapter returns correct config."""
    adapter = WindsurfAdapter()
    config = adapter.get_config()
    
    assert config.id == "windsurf"
    assert config.name == "Windsurf"
    assert config.skill_format == "markdown"


def test_windsurf_adapter_generate_skill_file():
    """Test WindsurfAdapter generates content."""
    adapter = WindsurfAdapter()
    content = adapter.generate_skill_file("# Paper Reader\n\nA skill.")
    
    assert "Paper Reader" in content


# --- ZedAdapter tests ---

def test_zed_adapter_get_config():
    """Test ZedAdapter returns correct config."""
    adapter = ZedAdapter()
    config = adapter.get_config()
    
    assert config.id == "zed"
    assert config.name == "Zed"
    assert config.skill_format == "markdown"


def test_zed_adapter_generate_skill_file():
    """Test ZedAdapter generates content."""
    adapter = ZedAdapter()
    content = adapter.generate_skill_file("# Paper Reader\n\nA skill.")
    
    assert "Paper Reader" in content


# --- CopilotAdapter tests ---

def test_copilot_adapter_get_config():
    """Test CopilotAdapter returns correct config."""
    adapter = CopilotAdapter()
    config = adapter.get_config()
    
    assert config.id == "copilot"
    assert config.name == "Copilot CLI"
    assert config.skill_format == "markdown"


def test_copilot_adapter_generate_skill_file():
    """Test CopilotAdapter generates content."""
    adapter = CopilotAdapter()
    content = adapter.generate_skill_file("# Paper Reader\n\nA skill.")
    
    assert "Paper Reader" in content


# --- GeminiAdapter tests ---

def test_gemini_adapter_get_config():
    """Test GeminiAdapter returns correct config."""
    adapter = GeminiAdapter()
    config = adapter.get_config()
    
    assert config.id == "gemini"
    assert config.name == "Gemini CLI"
    assert config.skill_format == "markdown"


def test_gemini_adapter_generate_skill_file():
    """Test GeminiAdapter generates content."""
    adapter = GeminiAdapter()
    content = adapter.generate_skill_file("# Paper Reader\n\nA skill.")
    
    assert "Paper Reader" in content


# --- Registry integration tests ---

def test_registry_has_all_9_adapters():
    """Test Registry has all 9 adapters registered."""
    adapters = Registry.list_all()
    
    expected = ["claude", "hermes", "codex", "opencode", "cursor", "windsurf", "zed", "copilot", "gemini"]
    for adapter_id in expected:
        assert adapter_id in adapters, f"Missing adapter: {adapter_id}"


def test_registry_get_each_adapter():
    """Test Registry can get each of the 9 adapters."""
    adapter_ids = ["claude", "hermes", "codex", "opencode", "cursor", "windsurf", "zed", "copilot", "gemini"]
    
    for adapter_id in adapter_ids:
        adapter = Registry.get(adapter_id)
        assert isinstance(adapter, BaseAdapter)
        assert adapter.get_config().id == adapter_id


def test_all_adapters_implement_base_interface():
    """Test all adapters implement the BaseAdapter interface."""
    adapter_ids = ["claude", "hermes", "codex", "opencode", "cursor", "windsurf", "zed", "copilot", "gemini"]
    
    for adapter_id in adapter_ids:
        adapter = Registry.get(adapter_id)
        
        # Should have all required methods
        assert hasattr(adapter, 'get_config')
        assert hasattr(adapter, 'generate_skill_file')
        assert hasattr(adapter, 'generate_config_file')
        assert hasattr(adapter, 'detect_installation')
        assert hasattr(adapter, 'get_installation_instructions')
        
        # All should return proper types
        config = adapter.get_config()
        assert isinstance(config, AdapterConfig)
        
        skill_content = adapter.generate_skill_file("test")
        assert isinstance(skill_content, str)
        
        config_content = adapter.generate_config_file({})
        assert isinstance(config_content, str)
        
        install_result = adapter.detect_installation()
        assert isinstance(install_result, bool)
        
        instructions = adapter.get_installation_instructions()
        assert isinstance(instructions, str)
