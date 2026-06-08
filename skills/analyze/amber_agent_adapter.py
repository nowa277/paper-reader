"""amber-agent KB adapter for paper-reader.

Bridges amber-agent's pre-parsed MinerU output (under
``mineru_output/<doc>/vlm/`` or ``mineru_output/<doc>/hybrid_auto/``)
to paper-reader's analyze sub-skill, avoiding a redundant MinerU re-run.

Two naming schemes are supported:

* ``vlm/``       — amber-agent's renamed standard output.
* ``hybrid_auto/`` — MinerU 2.5 raw subdir name (vllm 0.13.0+).

Public API:

* :class:`AmberAgentVLMNotFound` — exception for missing dirs.
* :func:`detect_amber_agent_vlm_output` — boolean probe.
* :func:`read_vlm_output` — read markdown + metadata tuple.
"""

from __future__ import annotations

import json
from pathlib import Path


# Subdir names amber-agent / MinerU may use to hold the parsed output.
_VLM_SUBDIR = "vlm"
_HYBRID_AUTO_SUBDIR = "hybrid_auto"


class AmberAgentVLMNotFound(Exception):
    """Raised when amber-agent VLM output is not found at the given path."""


def _candidate_vlm_dirs(path: Path) -> list[Path]:
    """Return the two candidate subdirs (vlm/ then hybrid_auto/) for ``path``."""
    return [path / _VLM_SUBDIR, path / _HYBRID_AUTO_SUBDIR]


def detect_amber_agent_vlm_output(path: str | Path) -> bool:
    """Detect whether the given path contains amber-agent VLM output.

    Checks for either ``vlm/`` or ``hybrid_auto/`` subdir under ``path``.
    Returns ``True`` if a matching directory is found, ``False`` otherwise
    (including for nonexistent ``path`` — never raises on missing input).
    """
    try:
        base = Path(path)
    except TypeError:
        return False

    for candidate in _candidate_vlm_dirs(base):
        try:
            if candidate.is_dir():
                return True
        except OSError:
            # Permission errors, broken symlinks, etc. — treat as not found.
            continue
    return False


def _resolve_vlm_dir(path: Path) -> Path:
    """Return the existing vlm/ or hybrid_auto/ subdir under ``path``.

    Raises:
        AmberAgentVLMNotFound: when neither subdir exists.
    """
    for candidate in _candidate_vlm_dirs(path):
        if candidate.is_dir():
            return candidate
    raise AmberAgentVLMNotFound(
        f"No 'vlm/' or 'hybrid_auto/' subdir found under {path}. "
        "Run MinerU first, or pass a path that already contains amber-agent's parsed output."
    )


def _read_metadata(vlm_dir: Path, basename: str) -> dict:
    """Read the content_list.json metadata, or return ``{}`` if absent/invalid.

    Looks for ``<basename>_content_list.json`` (amber-agent convention) and
    falls back to ``content_list.json`` if the suffixed variant is missing.
    A missing or malformed file yields an empty dict — never raises.
    """
    candidates = [
        vlm_dir / f"{basename}_content_list.json",
        vlm_dir / "content_list.json",
    ]
    for json_path in candidates:
        if not json_path.is_file():
            continue
        try:
            with json_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return {}
        if isinstance(data, dict):
            return data
        # amber-agent's content_list.json is a list of element dicts; wrap it
        # so the return type is always a dict.
        return {"elements": data}
    return {}


def read_vlm_output(path: str | Path) -> tuple[str, dict]:
    """Read VLM output from the given path.

    Auto-detects ``vlm/`` vs ``hybrid_auto/`` subdir naming and reads the
    primary markdown + metadata pair.

    Args:
        path: Parent directory containing either a ``vlm/`` or
            ``hybrid_auto/`` subdir.

    Returns:
        A ``(markdown_content, metadata_dict)`` tuple where:

        * ``markdown_content`` is the text of ``<basename>.md`` inside the
          detected subdir (where ``<basename>`` is ``path.name``).
        * ``metadata_dict`` is the parsed ``content_list.json`` content, or
          an empty dict if the file is absent.

    Raises:
        AmberAgentVLMNotFound: if no ``vlm/`` or ``hybrid_auto/`` subdir.
        FileNotFoundError: if ``<basename>.md`` is missing inside the
            detected subdir.
    """
    base = Path(path)
    vlm_dir = _resolve_vlm_dir(base)
    basename = base.name

    md_path = vlm_dir / f"{basename}.md"
    if not md_path.is_file():
        raise FileNotFoundError(
            f"Expected markdown file not found: {md_path}"
        )

    markdown_content = md_path.read_text(encoding="utf-8")
    metadata_dict = _read_metadata(vlm_dir, basename)

    return markdown_content, metadata_dict
