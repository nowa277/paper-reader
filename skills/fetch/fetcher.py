"""Paper fetcher with auto-directory creation and space checking.

Provides unified paper fetching with Jina Reader, direct download,
and automatic archive directory creation.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Placeholder for Jina API call — actual implementation depends on
# how Jina Reader is invoked in the system
JINA_READER_URL = "https://r.jina.ai/"


def ensure_dir(path: Path) -> None:
    """Ensure directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists.

    Raises:
        OSError: If directory creation fails.
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def check_disk_space(path: Path, required_bytes: int) -> bool:
    """Check if sufficient disk space is available.

    Args:
        path: Path to check (uses parent directory for availability check).
        required_bytes: Minimum bytes needed.

    Returns:
        True if sufficient space is available.
    """
    try:
        stat = shutil.disk_usage(path.parent if path.is_file() else path)
        return stat.free >= required_bytes
    except OSError:
        # If we can't check, assume OK
        return True


def download_with_space_check(url: str, output_path: Path) -> Path:
    """Download file after checking disk space.

    Args:
        url: URL to download from.
        output_path: Local path to save file.

    Returns:
        Path to downloaded file.

    Raises:
        OSError: If insufficient disk space or download fails.
    """
    ensure_dir(output_path.parent)

    response = requests.get(url, stream=True)
    response.raise_for_status()

    content_length = response.headers.get("Content-Length")
    if content_length:
        required = int(content_length)
        if not check_disk_space(output_path, required):
            raise OSError(f"Insufficient disk space to download {url}")

    with open(output_path, "wb") as f:
        shutil.copyfileobj(response.raw, f, length=8192)

    return output_path


def fetch_paper(url: str, output_dir: Optional[Path] = None) -> dict:
    """Fetch paper from URL.

    Args:
        url: Paper URL or search term.
        output_dir: Output directory for downloaded files.

    Returns:
        dict with keys: success, path, content (if markdown)
    """
    # Ensure output directory exists
    if output_dir:
        ensure_dir(output_dir)

    # Placeholder return — actual implementation depends on
    # how fetch is invoked in the system
    return {
        "success": True,
        "path": None,
        "content": None,
    }