# Import all adapters to trigger registration with Registry
from . import claude
from . import hermes
from . import codex
from . import opencode
from . import cursor
from . import windsurf
from . import zed
from . import copilot
from . import gemini

# Now register them
from ..registry import Registry

Registry.register("claude", claude.ClaudeAdapter)
Registry.register("hermes", hermes.HermesAdapter)
Registry.register("codex", codex.CodexAdapter)
Registry.register("opencode", opencode.OpenCodeAdapter)
Registry.register("cursor", cursor.CursorAdapter)
Registry.register("windsurf", windsurf.WindsurfAdapter)
Registry.register("zed", zed.ZedAdapter)
Registry.register("copilot", copilot.CopilotAdapter)
Registry.register("gemini", gemini.GeminiAdapter)
