"""Paper Reader main skill entry point.

Routes commands to appropriate sub-skills based on command path.
Supports both full paths and aliases.

Commands:
- setup config <action>  - Configuration management
- setup mineru <action>  - MinerU PDF parser management (detect, install, status)
- fetch <source>         - Paper retrieval from various sources
- analyze <action>      - Paper analysis and summarization
"""

import logging

logger = logging.getLogger(__name__)

# Command routing table
# Maps command paths to sub-skill names that can be invoked via Skill tool
_ROUTES = {
    # Setup commands
    "setup": {
        "config": "paper-reader:config",
        "mineru": "paper-reader:mineru",
    },
    # Direct sub-skill commands
    "config": "paper-reader:config",
    "mineru": "paper-reader:mineru",
    "fetch": "paper-reader:fetch",
    "analyze": "paper-reader:analyze",
}

# Alias mappings
_ALIASES = {
    "cfg": "config",
    "c": "config",
    "m": "mineru",
    "mu": "mineru",
    "f": "fetch",
    "get": "fetch",
    "a": "analyze",
    "analysis": "analyze",
}


def _normalize_command(command: str) -> list[str]:
    """Normalize command string to list of parts.

    Handles:
    - Empty string → []
    - Single words → ["word"]
    - Multiple words → ["word1", "word2", ...]
    - Extra whitespace → trimmed
    """
    if not command:
        return []
    return [part.strip() for part in command.strip().split() if part.strip()]


def _resolve_alias(word: str) -> str:
    """Resolve command alias to full command name."""
    return _ALIASES.get(word.lower(), word.lower())


def _build_skill_args(parts: list[str]) -> str:
    """Build arguments string for sub-skill from command parts."""
    if not parts:
        return ""
    # Join remaining parts as arguments for the sub-skill
    return " ".join(parts)


def route_command(command: str) -> tuple[str | None, str]:
    """Route command to appropriate sub-skill.

    Args:
        command: Command string after /paper-reader (e.g., "setup mineru detect")

    Returns:
        Tuple of (sub_skill_name, args_for_skill)
        Returns (None, error_message) if no valid route found
    """
    parts = _normalize_command(command)

    if not parts:
        return None, "No command provided. Use: setup, config, mineru, fetch, or analyze"

    # First word - resolve aliases
    first = _resolve_alias(parts[0])
    remaining = parts[1:] if len(parts) > 1 else []

    # Check if it's a setup command
    if first == "setup":
        if not remaining:
            return None, "Setup requires a target. Use: setup config or setup mineru"

        target = _resolve_alias(remaining[0])
        sub_args = remaining[1:] if len(remaining) > 1 else []

        if target in _ROUTES.get("setup", {}):
            skill_name = _ROUTES["setup"][target]
            args = _build_skill_args(sub_args)
            return skill_name, args
        else:
            return None, f"Unknown setup target: {target}. Use: setup config or setup mineru"

    # Direct command (config, mineru, fetch, analyze)
    if first in _ROUTES:
        skill_name = _ROUTES[first]
        args = _build_skill_args(remaining)
        return skill_name, args

    return None, f"Unknown command: {first}. Use: setup, config, mineru, fetch, or analyze"


def get_available_commands() -> dict:
    """Return all available commands and their descriptions."""
    return {
        "setup config": "Configuration management",
        "setup mineru": "MinerU detection (default)",
        "setup mineru detect": "Run MinerU detection",
        "setup mineru install": "Install MinerU",
        "setup mineru status": "Show MinerU status",
        "config": "Configuration management (alias for setup config)",
        "mineru": "MinerU management (alias for setup mineru)",
        "fetch": "Paper retrieval from various sources",
        "analyze": "Paper analysis and summarization",
    }


# Main skill entry point - called when /paper-reader is invoked
def execute(command: str) -> dict:
    """Execute paper-reader skill with given command.

    Args:
        command: Command string after /paper-reader

    Returns:
        Dict with:
        - skill: Sub-skill name to invoke via Skill tool
        - args: Arguments to pass to the sub-skill
        - error: Error message if routing failed (skill will be None)
    """
    logger.info(f"Routing command: {command}")

    skill_name, args = route_command(command)

    if skill_name is None:
        # Return error info - the skill should display help
        return {
            "skill": None,
            "args": "",
            "error": args,
            "available_commands": get_available_commands(),
        }

    logger.info(f"Routed to skill: {skill_name} with args: {args}")

    return {
        "skill": skill_name,
        "args": args,
        "error": None,
    }


# For direct testing
if __name__ == "__main__":
    # Test routing
    test_commands = [
        "",
        "setup",
        "setup config",
        "setup config show",
        "setup mineru",
        "setup mineru detect",
        "setup mineru install",
        "setup mineru status",
        "config",
        "config show",
        "mineru",
        "mineru detect",
        "fetch",
        "fetch arxiv 2401.12345",
        "analyze",
        "analyze summary paper.pdf",
        "cfg show",  # alias test
        "m detect",  # alias test
    ]

    print("Testing command routing:")
    print("-" * 60)
    for cmd in test_commands:
        result = execute(cmd)
        print(f"\nCommand: '{cmd}'")
        if result["error"]:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Skill: {result['skill']}")
            print(f"  Args: '{result['args']}'")