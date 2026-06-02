import sys
from pathlib import Path

import pytest

# Ensure the paper-reader directory is in sys.path for imports
paper_reader_path = Path(__file__).parent.parent
if str(paper_reader_path) not in sys.path:
    sys.path.insert(0, str(paper_reader_path))


@pytest.fixture
def temp_config_dir(tmp_path):
    """Temporary config directory fixture.

    Creates a temporary ~/.paper-reader-style directory structure.
    """
    config_dir = tmp_path / ".paper-reader"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_home(tmp_path, monkeypatch):
    """Mock HOME directory for isolated testing.

    Sets HOME to a temp directory and returns the path.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


@pytest.fixture
def system_deps():
    """System dependencies checker fixture.

    Returns the SYSTEM_DEPS dict and check functions.
    """
    from skills.config import system_deps
    return {
        "deps": system_deps.SYSTEM_DEPS,
        "check": system_deps.check_dependency,
        "check_all": system_deps.check_all_dependencies,
        "get_missing": system_deps.get_missing_required,
    }
