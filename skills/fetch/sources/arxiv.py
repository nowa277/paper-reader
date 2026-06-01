"""arXiv API 搜索"""
import re
import requests
from typing import Optional
from xml.etree import ElementTree as ET

from ..models import PaperResult

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = "http://www.w3.org/2005/Atom"


def extract_arxiv_id(url: str) -> Optional[str]:
    """从 arXiv URL 中提取 arXiv ID。

    Args:
        url: arXiv URL (如 "http://arxiv.org/abs/2301.00001v2")

    Returns:
        arXiv ID 字符串，或 None
    """
    # 匹配 /abs/ 后面的 ID 部分
    match = re.search(r"/abs/([0-9]+\.[0-9]+[v][0-9]+)", url)
    if match:
        return match.group(1)
    # 也匹配不带版本的 ID
    match = re.search(r"/abs/([0-9]+\.[0-9]+)", url)
    if match:
        return match.group(1)
    return None


def _parse_atom_entry(entry) -> Optional[PaperResult]:
    """解析 Atom feed entry。

    Args:
        entry: xml.etree.ElementTree Element representing an Atom entry

    Returns:
        PaperResult 或 None（解析失败时）
    """
    try:
        id_text = entry.find(f"{{{ATOM_NS}}}id").text
        id_parts = id_text.split("/")
        arxiv_id = id_parts[-1]

        title = entry.find(f"{{{ATOM_NS}}}title").text.strip().replace("\n", " ")

        authors = [a.find(f"{{{ATOM_NS}}}name").text for a in entry.findall(f"{{{ATOM_NS}}}author")]

        published = entry.find(f"{{{ATOM_NS}}}published").text
        year = int(published[:4])

        summary = entry.find(f"{{{ATOM_NS}}}summary").text.strip()

        # 找 PDF 链接
        pdf_url = None
        for link in entry.findall(f"{{{ATOM_NS}}}link"):
            if link.get("title") == "pdf":
                pdf_url = link.get("href")
                break

        return PaperResult(
            paper_id=f"arxiv:{arxiv_id}",
            title=title,
            authors=authors,
            year=year,
            abstract=summary[:500],  # 截断
            url=f"https://arxiv.org/abs/{arxiv_id}",
            pdf_url=pdf_url,
            source="arxiv",
        )
    except Exception:
        return None


def search_arxiv(query: str, max_results: int = 10) -> list[PaperResult]:
    """搜索 arXiv。

    Args:
        query: 搜索关键词
        max_results: 最大结果数

    Returns:
        PaperResult 列表
    """
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
    }
    response = requests.get(ARXIV_API, params=params, timeout=30)
    response.raise_for_status()

    # 解析 Atom feed（处理 XML 命名空间）
    root = ET.fromstring(response.content)
    results = []
    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        paper = _parse_atom_entry(entry)
        if paper is not None:
            results.append(paper)

    return results
