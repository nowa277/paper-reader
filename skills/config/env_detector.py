"""Environment detector for Python version and virtual environments."""

import os
from typing import Optional


def detect_venv_type() -> str:
    """Detect the current virtual environment type.

    Returns:
        'venv' | 'conda' | 'uv' | 'system'
    """
    if os.environ.get("VIRTUAL_ENV"):
        return "venv"
    if os.environ.get("CONDA_DEFAULT_ENV"):
        return "conda"
    if os.environ.get("UV_CACHE_DIR"):
        return "uv"
    return "system"


def check_venv_compatibility() -> tuple[bool, str]:
    """Check virtual environment compatibility.

    Returns:
        (ok, warning_message)
    """
    venv_type = detect_venv_type()

    if venv_type == "conda":
        return False, (
            "Conda environment detected. MinerU dependencies may conflict with Conda. "
            "Consider using venv or system Python instead."
        )

    if venv_type == "system":
        return True, ""

    # venv and uv are generally fine
    return True, f"{venv_type} environment detected"


def check_python_version() -> tuple[bool, str]:
    """Check Python version meets requirements.

    Returns:
        (ok, message)
    """
    import sys
    MIN_VERSION = (3, 10)
    current = sys.version_info[:2]
    if current >= MIN_VERSION:
        return True, f"Python {current[0]}.{current[1]} OK"
    return False, f"Python {current[0]}.{current[1]} too old; requires 3.10+"
