"""System dependency detection for paper-reader skill.

Detects external tools: curl, pandoc, tesseract.
"""

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class Dependency:
    """System dependency definition."""
    name: str           # Display name
    command: str        # Command to check
    required: bool      # Whether this is required
    version_args: Optional[list[str]] = None  # Args for version check


SYSTEM_DEPS = {
    "curl": Dependency("curl", "curl", True, ["--version"]),
    "pandoc": Dependency("Pandoc", "pandoc", True, ["--version"]),
    "tesseract": Dependency("Tesseract OCR", "tesseract", False, ["--version"]),
}


def check_dependency(dep_id: str) -> tuple[bool, Optional[str]]:
    """Check if a dependency is installed.

    Args:
        dep_id: Key in SYSTEM_DEPS

    Returns:
        (is_installed, version_info_or_error_message)
    """
    if dep_id not in SYSTEM_DEPS:
        return False, f"Unknown dependency: {dep_id}"

    dep = SYSTEM_DEPS[dep_id]
    path = shutil.which(dep.command)
    if path is None:
        return False, f"{dep.name} not found in PATH"

    if dep.version_args:
        try:
            result = subprocess.run(
                [dep.command] + dep.version_args,
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0] if result.stdout.strip() else "Unknown version"
                return True, version_line[:100]
            return True, "Installed (version check failed)"
        except (OSError, subprocess.TimeoutExpired):
            return True, "Installed (version check failed)"

    return True, path


def check_all_dependencies() -> dict[str, dict]:
    """Check all system dependencies.

    Returns:
        {dep_id: {"installed": bool, "version": str, "required": bool}}
    """
    results = {}
    for dep_id in SYSTEM_DEPS:
        installed, version = check_dependency(dep_id)
        results[dep_id] = {
            "installed": installed,
            "version": version,
            "required": SYSTEM_DEPS[dep_id].required,
        }
    return results


def get_missing_required() -> list[str]:
    """Return list of missing required dependency IDs."""
    missing = []
    for dep_id, dep in SYSTEM_DEPS.items():
        if dep.required:
            installed, _ = check_dependency(dep_id)
            if not installed:
                missing.append(dep_id)
    return missing


def get_installation_instructions(dep_id: str) -> str:
    """Get installation instructions for a dependency."""
    instructions = {
        "curl": "Ubuntu/Debian: sudo apt install curl | macOS: brew install curl",
        "pandoc": "Ubuntu/Debian: sudo apt install pandoc | macOS: brew install pandoc",
        "tesseract": "Ubuntu/Debian: sudo apt install tesseract-ocr | macOS: brew install tesseract",
    }
    return instructions.get(dep_id, f"Install {dep_id} using your system's package manager")
