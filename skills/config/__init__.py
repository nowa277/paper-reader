"""skills.config - Configuration modules for paper-reader skill."""

from skills.config.env_detector import (
    detect_venv_type,
    check_venv_compatibility,
    check_python_version,
)

from skills.config.system_deps import (
    Dependency,
    SYSTEM_DEPS,
    check_dependency,
    check_all_dependencies,
    get_missing_required,
    get_installation_instructions,
)

__all__ = [
    "detect_venv_type",
    "check_venv_compatibility",
    "check_python_version",
    "Dependency",
    "SYSTEM_DEPS",
    "check_dependency",
    "check_all_dependencies",
    "get_missing_required",
    "get_installation_instructions",
]
