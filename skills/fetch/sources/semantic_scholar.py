"""Semantic Scholar API 搜索"""
import requests
from ..models import PaperResult

S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"


def search_semantic_scholar(
    query: str,
    max_results: int = 10,
    fields: str = "paperId,title,authors,year,venue,abstract,url,openAccessPdf"
) -> list[PaperResult]:
    """搜索 Semantic Scholar

    Args:
        query: 搜索关键词
        max_results: 最大结果数
        fields: API 返回字段

    Returns:
        PaperResult 列表
    """
    params = {
        "query": query,
        "limit": max_results,
        "fields": fields,
    }
    resp = requests.get(S2_API, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("data", []):
        if not item.get("paperId"):
            continue
        results.append(PaperResult(
            paper_id=f"ss:{item['paperId']}",
            title=item.get("title", ""),
            authors=[a.get("name", "") for a in item.get("authors", [])],
            year=item.get("year", 0),
            venue=item.get("venue", ""),
            abstract=item.get("abstract", ""),
            url=item.get("url", ""),
            pdf_url=item.get("openAccessPdf", {}).get("url") if item.get("openAccessPdf") else None,
            source="semantic_scholar",
        ))
    return results
