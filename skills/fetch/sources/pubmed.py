"""PubMed E-utilities 搜索"""
import requests
from typing import Optional
from xml.etree import ElementTree as ET

from ..models import PaperResult

PUBMED_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# PubMed MedlineXML namespace
MEDLINE_NS = "http://www.ncbi.nlm.nih.gov/NLM/Vedscape/dtd"


def _parse_pubmed_xml(xml_text: str) -> list[PaperResult]:
    """解析 PubMed EFetch 返回的 XML。

    Args:
        xml_text: EFetch 返回的 XML 字符串

    Returns:
        PaperResult 列表
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    results = []
    # 处理 PubMed 文章
    for article in root.iter("PubmedArticle"):
        paper = _parse_article(article)
        if paper is not None:
            results.append(paper)

    return results


def _parse_article(article) -> Optional[PaperResult]:
    """解析单个 PubmedArticle 元素。

    Args:
        article: PubmedArticle XML 元素

    Returns:
        PaperResult 或 None
    """
    try:
        # 获取 PMID
        pmid_elem = article.find(".//PMID")
        if pmid_elem is None or not pmid_elem.text:
            return None
        pmid = pmid_elem.text.strip()

        # 获取文章标题
        title_elem = article.find(".//ArticleTitle")
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""

        # 获取作者列表
        authors = []
        for author in article.findall(".//Author"):
            last_name = author.find("LastName")
            fore_name = author.find("ForeName")
            if last_name is not None and last_name.text:
                name = last_name.text.strip()
                if fore_name is not None and fore_name.text:
                    name = f"{fore_name.text.strip()} {name}"
                authors.append(name)

        # 获取发表年份
        year = 0
        pub_date_elem = article.find(".//PubDate")
        if pub_date_elem is not None:
            year_elem = pub_date_elem.find("Year")
            if year_elem is not None and year_elem.text:
                try:
                    year = int(year_elem.text.strip())
                except ValueError:
                    pass
        # 备选：从 Article/Journal/JournalIssue/PubDate 获取
        if year == 0:
            journal_date = article.find(".//Journal/JournalIssue/PubDate")
            if journal_date is not None:
                year_elem = journal_date.find("Year")
                if year_elem is not None and year_elem.text:
                    try:
                        year = int(year_elem.text.strip())
                    except ValueError:
                        pass

        # 获取摘要
        abstract_parts = []
        for abstract_text in article.findall(".//AbstractText"):
            if abstract_text.text:
                abstract_parts.append(abstract_text.text.strip())
        abstract = " ".join(abstract_parts)

        # 获取 DOI
        doi = None
        for article_id in article.findall(".//ArticleId"):
            if article_id.get("IdType") == "doi" and article_id.text:
                doi = article_id.text.strip()
                break

        # 构建 URL 和 PDF URL
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        pdf_url = None
        if doi:
            pdf_url = f"https://doi.org/{doi}"

        return PaperResult(
            paper_id=f"pubmed:{pmid}",
            title=title,
            authors=authors,
            year=year,
            abstract=abstract[:500] if abstract else "",
            url=url,
            pdf_url=pdf_url,
            source="pubmed",
        )
    except Exception:
        return None


def search_pubmed(query: str, max_results: int = 10) -> list[PaperResult]:
    """搜索 PubMed。

    Uses ESearch for ID list, then EFetch for details.

    Args:
        query: 搜索关键词
        max_results: 最大结果数

    Returns:
        PaperResult 列表
    """
    # Step 1: Search for IDs
    search_url = f"{PUBMED_API}/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
    }
    search_resp = requests.get(search_url, params=params, timeout=30)
    search_resp.raise_for_status()
    data = search_resp.json()
    id_list = data.get("esearchresult", {}).get("idlist", [])

    if not id_list:
        return []

    # Step 2: Fetch details
    fetch_url = f"{PUBMED_API}/efetch.fcgi"
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "xml",
    }
    fetch_resp = requests.get(fetch_url, params=fetch_params, timeout=30)
    fetch_resp.raise_for_status()

    return _parse_pubmed_xml(fetch_resp.text)
