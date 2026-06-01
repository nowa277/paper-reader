"""CrossRef API 搜索"""
import requests
from ..models import PaperResult

CROSSREF_API = "https://api.crossref.org/works"


def search_crossref(query: str, max_results: int = 10) -> list[PaperResult]:
    """搜索 CrossRef

    Args:
        query: 搜索关键词
        max_results: 最大结果数

    Returns:
        PaperResult 列表
    """
    params = {
        "query": query,
        "rows": max_results,
    }
    resp = requests.get(CROSSREF_API, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("message", {}).get("items", []):
        authors = []
        for author in item.get("author", []):
            name = author.get("given", "") + " " + author.get("family", "")
            if name.strip():
                authors.append(name.strip())

        # 尝试从 published-print 或 published-online 获取年份
        year = 0
        for date_key in ("published-print", "published-online", "created"):
            date_parts = item.get(date_key, {}).get("date-parts", [])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]
                break

        results.append(PaperResult(
            paper_id=f"doi:{item.get('DOI', '')}",
            title=item.get("title", [""])[0] if item.get("title") else "",
            authors=authors,
            year=int(year) if year else 0,
            venue=item.get("container-title", [""])[0] if item.get("container-title") else "",
            abstract=item.get("abstract", ""),
            url=item.get("URL", ""),
            pdf_url=None,
            source="crossref",
        ))
    return results
