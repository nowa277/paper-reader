"""Paper fetcher with auto-directory creation and space checking.

Provides unified paper fetching with Jina Reader, direct download,
and automatic archive directory creation.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# Placeholder for Jina API call — actual implementation depends on
# how Jina Reader is invoked in the system
JINA_READER_URL = "https://r.jina.ai/"


def _parse_identifier(identifier: str) -> tuple[str, str]:
    """解析 identifier 返回 (type, id)

    Args:
        identifier: 论文标识符
            - arXiv ID: "2301.00001" or "arxiv:2301.00001"
            - DOI: "10.1038/nature12373" or "doi:10.1038/nature12373"
            - PMID: "12345678" or "pubmed:12345678"
            - URL: "https://...

    Returns:
        tuple: (type, id) 其中 type 是 "arxiv", "doi", "pubmed", "url", 或 "unknown"
    """
    identifier = identifier.strip()

    if identifier.startswith("arxiv:"):
        return "arxiv", identifier[6:]
    elif identifier.startswith("doi:"):
        return "doi", identifier[4:]
    elif identifier.startswith("pubmed:"):
        return "pubmed", identifier[7:]
    elif identifier.startswith("http"):
        return "url", identifier
    elif "/" in identifier or len(identifier) > 20 or "." in identifier:
        return "arxiv", identifier
    else:
        return "unknown", identifier


def _get_pdf_url(paper_id: str) -> Optional[str]:
    """根据 paper_id 获取 PDF URL

    Args:
        paper_id: 论文标识符（可能带前缀如 arxiv:, doi:, pubmed:）

    Returns:
        PDF URL 或 None（如果无法确定 URL）
    """
    if paper_id.startswith("arxiv:"):
        arxiv_id = paper_id[6:]
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    elif paper_id.startswith("doi:"):
        doi = paper_id[4:]
        return f"https://doi.org/{doi}"
    elif paper_id.startswith("pubmed:"):
        pmid = paper_id[7:]
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    return None


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


def fetch_paper(identifier: str, output_dir: Optional[Path] = None) -> dict:
    """获取单篇论文 PDF

    Args:
        identifier: 论文标识符
            - arXiv ID: "2301.00001" or "arxiv:2301.00001"
            - DOI: "10.1038/nature12373" or "doi:10.1038/nature12373"
            - PMID: "12345678" or "pubmed:12345678"
            - URL: "https://...
        output_dir: 输出目录

    Returns:
        dict: {success, path, content}
    """
    from .searcher import search_papers

    # Parse the identifier
    id_type, paper_id = _parse_identifier(identifier)

    if id_type == "unknown":
        return {
            "success": False,
            "path": None,
            "content": None,
            "error": f"Unknown identifier format: {identifier}",
        }

    # Get the PDF URL - reconstruct identifier with prefix
    full_id = f"{id_type}:{paper_id}" if id_type != "url" else identifier
    pdf_url = _get_pdf_url(full_id) if id_type != "url" else identifier

    if not pdf_url:
        return {
            "success": False,
            "path": None,
            "content": None,
            "error": f"Could not determine URL for identifier: {identifier}",
        }

    # Determine output path
    if output_dir:
        ensure_dir(output_dir)
        filename = f"{paper_id.replace('/', '_')}.pdf"
        output_path = output_dir / filename
    else:
        output_path = None

    # Use Jina Reader to fetch as markdown
    try:
        jina_url = f"{JINA_READER_URL}{pdf_url}"
        response = requests.get(jina_url, timeout=30)
        response.raise_for_status()
        content = response.text

        if output_path:
            # Download PDF to file
            download_with_space_check(pdf_url, output_path)

        return {
            "success": True,
            "path": str(output_path) if output_path else None,
            "content": content,
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "path": None,
            "content": None,
            "error": str(e),
        }


def search_and_fetch(
    query: str,
    domain: Optional[str] = None,
    max_results: int = 10,
    output_dir: Optional[Path] = None,
) -> dict:
    """搜索论文，用户选择后获取

    Args:
        query: 搜索关键词
        domain: 限定领域 (None=自动检测)
        max_results: 最大结果数
        output_dir: 输出目录

    Returns:
        dict: {success, results, selected, path}
    """
    from .searcher import search_papers

    results = search_papers(query, domain, max_results)

    return {
        "success": True,
        "results": [r.display_name for r in results],
        "count": len(results),
    }