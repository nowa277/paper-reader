"""多源论文搜索编排器"""
import concurrent.futures
from typing import Optional
from .models import PaperResult
from .sources.arxiv import search_arxiv
from .sources.pubmed import search_pubmed
from .sources.semantic_scholar import search_semantic_scholar
from .sources.crossref import search_crossref

DOMAIN_KEYWORDS = {
    "cs": ["machine learning", "neural network", "deep learning", "attention", "transformer", "AI"],
    "bio": ["protein", "gene", "cell", "DNA", "RNA", "biology", "cancer", "genome"],
    "chem": ["molecule", "reaction", "catalyst", "polymer", "chemistry"],
    "physics": ["quantum", "particle", "cosmology", "condensed matter"],
}

def detect_domain(query: str) -> str:
    """根据查询关键词检测领域"""
    query_lower = query.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw.lower() in query_lower for kw in keywords):
            return domain
    return "general"

def search_papers(
    query: str,
    domain: Optional[str] = None,
    max_results: int = 10,
) -> list[PaperResult]:
    """搜索多源数据库并合并结果

    Args:
        query: 搜索关键词
        domain: 限定领域 (None=自动检测)
        max_results: 每源最大结果数

    Returns:
        去重后的论文列表，按相关性排序
    """
    if domain is None:
        domain = detect_domain(query)

    # 确定要搜索的来源
    sources_to_search = _get_sources_for_domain(domain)

    # 并行搜索
    all_results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(source_search, query, max_results): source
            for source, source_search in sources_to_search
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                # 单源失败不影响整体
                pass

    # 去重 + 排序
    return _deduplicate_and_sort(all_results)

def _get_sources_for_domain(domain: str) -> list:
    """根据领域返回要搜索的来源列表"""
    sources = [
        ("semantic_scholar", search_semantic_scholar),
        ("crossref", search_crossref),
    ]

    if domain in ("cs", "physics"):
        sources.insert(0, ("arxiv", search_arxiv))
    elif domain == "bio":
        sources.insert(0, ("pubmed", search_pubmed))

    return sources

def _deduplicate_and_sort(results: list[PaperResult]) -> list[PaperResult]:
    """去重并排序"""
    seen = set()
    unique = []
    for r in results:
        if r.paper_id not in seen:
            seen.add(r.paper_id)
            unique.append(r)

    # 按 year 降序
    unique.sort(key=lambda x: x.year, reverse=True)
    return unique
