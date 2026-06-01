"""skills.config - Configuration modules for paper-reader skill."""

from skills.config.system_deps import (
    Dependency,
    SYSTEM_DEPS,
    check_dependency,
    check_all_dependencies,
    get_missing_required,
    get_installation_instructions,
)

__all__ = [
    "Dependency",
    "SYSTEM_DEPS",
    "check_dependency",
    "check_all_dependencies",
    "get_missing_required",
    "get_installation_instructions",
]
