# Fetch 搜索增强实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现论文搜索功能，用户输入关键词搜索多源数据库，选择后下载 PDF

**Architecture:** 多源并行搜索 + 串行 fallback，结果归一化后合并去重

**Tech Stack:** Python requests, 公共学术 API (arXiv/PubMed/Semantic Scholar/CrossRef)

---

## 文件结构

```
skills/fetch/
├── fetcher.py           # 更新: search_and_fetch(), fetch_paper()
├── rate_limiter.py     # 已有
├── checkpoint.py       # 已有
├── searcher.py         # 新增: 多源搜索编排
├── models.py           # 新增: PaperResult dataclass
└── sources/
    ├── __init__.py
    ├── arxiv.py        # 新增: arXiv API
    ├── pubmed.py       # 新增: PubMed API
    ├── semantic_scholar.py  # 新增
    └── crossref.py     # 新增
```

---

## Task 1: 创建 models.py - PaperResult 数据类

**Files:**
- Create: `skills/fetch/models.py`
- Test: `tests/skills/fetch/test_models.py`

- [ ] **Step 1: 创建 PaperResult dataclass**

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class PaperResult:
    """标准化论文结果"""
    paper_id: str           # 唯一标识
    title: str
    authors: list[str] = field(default_factory=list)
    year: int = 0
    venue: str = ""
    abstract: str = ""
    url: str = ""
    pdf_url: Optional[str] = None
    domain: str = "general"
    source: str = ""        # "arxiv", "pubmed", "semantic_scholar", "crossref"

    @property
    def display_name(self) -> str:
        """用于显示的名称"""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += " et al."
        return f"{self.title} — {authors_str}, {self.year} ({self.venue})"

    def to_selection_item(self, index: int) -> str:
        """返回选择列表中的条目"""
        return f"{index}. {self.display_name}"
```

- [ ] **Step 2: 写测试**

```python
def test_paper_result_display_name():
    result = PaperResult(
        paper_id="arxiv:2301.00001",
        title="Attention Is All You Need",
        authors=["Vaswani", "Shazeer", "Parmar"],
        year=2017,
        venue="NeurIPS"
    )
    assert "Attention Is All You Need" in result.display_name
    assert "Vaswani" in result.display_name
    assert "2017" in result.display_name

def test_to_selection_item():
    result = PaperResult(paper_id="x", title="Test", authors=["A"], year=2024, venue="X")
    assert result.to_selection_item(1) == "1. Test — A et al., 2024 (X)"
```

- [ ] **Step 3: 运行测试验证**

Run: `pytest tests/skills/fetch/test_models.py -v`

- [ ] **Step 4: 提交**

---

## Task 2: 创建 sources/arxiv.py - arXiv 搜索

**Files:**
- Create: `skills/fetch/sources/arxiv.py`
- Create: `skills/fetch/sources/__init__.py`
- Test: `tests/skills/fetch/test_arxiv.py`

- [ ] **Step 1: 创建 arXiv API 搜索**

```python
"""arXiv API 搜索"""
import requests
from typing import Optional
from ..models import PaperResult

ARXIV_API = "http://export.arxiv.org/api/query"

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

    # 解析 Atom feed
    results = []
    # 使用正则或 XML 解析提取论文信息
    # ...
    return results
```

**关键解析逻辑:**
```python
from xml.etree import ElementTree as ET

def _parse_atom_entry(entry) -> Optional[PaperResult]:
    """解析 Atom feed entry"""
    try:
        id_parts = entry.find("id").text.split("/")
        arxiv_id = id_parts[-1]

        title = entry.find("title").text.strip().replace("\n", " ")

        authors = [a.find("name").text for a in entry.findall("author")]

        published = entry.find("published").text
        year = int(published[:4])

        summary = entry.find("summary").text.strip()

        # 找 PDF 链接
        pdf_url = None
        for link in entry.findall("link"):
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
```

- [ ] **Step 2: 写测试**

```python
def test_parse_arxiv_id():
    # 测试从 URL 解析 arXiv ID
    assert extract_arxiv_id("http://arxiv.org/abs/2301.00001v2") == "2301.00001"
```

- [ ] **Step 3: 运行测试**

- [ ] **Step 4: 提交**

---

## Task 3: 创建 sources/pubmed.py - PubMed 搜索

**Files:**
- Create: `skills/fetch/sources/pubmed.py`
- Test: `tests/skills/fetch/test_pubmed.py`

- [ ] **Step 1: 创建 PubMed E-utilities 搜索**

```python
"""PubMed E-utilities 搜索"""
import requests
from typing import Optional
from ..models import PaperResult

PUBMED_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def search_pubmed(query: str, max_results: int = 10) -> list[PaperResult]:
    """搜索 PubMed。

    Uses ESearch for ID list, then EFetch for details.
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

    # 解析 XML 返回 PaperResult 列表
    return _parse_pubmed_xml(fetch_resp.text)
```

- [ ] **Step 2: 写测试** (使用 responses mock)

- [ ] **Step 3: 运行测试**

- [ ] **Step 4: 提交**

---

## Task 4: 创建 sources/semantic_scholar.py 和 crossref.py

**Files:**
- Create: `skills/fetch/sources/semantic_scholar.py`
- Create: `skills/fetch/sources/crossref.py`
- Test: 各一个简单测试

- [ ] **Step 1: Semantic Scholar API**

```python
"""Semantic Scholar API 搜索"""
import requests
from ..models import PaperResult

S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"

def search_semantic_scholar(
    query: str,
    max_results: int = 10,
    fields: str = "paperId,title,authors,year,venue,abstract,url,openAccessPdf"
) -> list[PaperResult]:
    """搜索 Semantic Scholar"""
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
```

- [ ] **Step 2: CrossRef API**

```python
"""CrossRef API 搜索"""
import requests
from ..models import PaperResult

CROSSREF_API = "https://api.crossref.org/works"

def search_crossref(query: str, max_results: int = 10) -> list[PaperResult]:
    """搜索 CrossRef"""
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

        results.append(PaperResult(
            paper_id=f"doi:{item.get('DOI', '')}",
            title=item.get("title", [""])[0] if item.get("title") else "",
            authors=authors,
            year=int(item.get("published-print", {}).get("date-parts", [[0]])[0][0] or 0),
            venue=item.get("container-title", [""])[0] if item.get("container-title") else "",
            abstract=item.get("abstract", ""),
            url=item.get("URL", ""),
            pdf_url=None,
            source="crossref",
        ))
    return results
```

- [ ] **Step 3: 测试 + 提交**

---

## Task 5: 创建 searcher.py - 多源搜索编排

**Files:**
- Create: `skills/fetch/searcher.py`
- Test: `tests/skills/fetch/test_searcher.py`

- [ ] **Step 1: 创建多源搜索编排器**

```python
"""多源论文搜索编排器"""
import asyncio
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
```

- [ ] **Step 2: 写测试**

- [ ] **Step 3: 运行测试**

- [ ] **Step 4: 提交**

---

## Task 6: 更新 fetcher.py - 集成搜索和获取

**Files:**
- Modify: `skills/fetch/fetcher.py`
- Test: `tests/skills/fetch/test_fetcher.py`

- [ ] **Step 1: 添加 fetch_paper 实现**

```python
def fetch_paper(identifier: str, output_dir: Optional[Path] = None) -> dict:
    """获取单篇论文 PDF

    Args:
        identifier: 论文标识符
            - arXiv ID: "2301.00001" or "arxiv:2301.00001"
            - DOI: "10.1038/nature12373" or "doi:10.1038/nature12373"
            - PMID: "12345678" or "pubmed:12345678"
            - URL: "https://..."
        output_dir: 输出目录

    Returns:
        dict: {success, path, content}
    """
    # 1. 解析 identifier 类型
    # 2. 获取 PDF URL
    # 3. 下载到 output_dir
    # 4. 返回结果
```

**关键逻辑:**
```python
from urllib.parse import urlparse

def _parse_identifier(identifier: str) -> tuple[str, str]:
    """解析 identifier 返回 (type, id)"""
    identifier = identifier.strip()

    if identifier.startswith("arxiv:"):
        return "arxiv", identifier[6:]
    elif identifier.startswith("doi:"):
        return "doi", identifier[4:]
    elif identifier.startswith("pubmed:"):
        return "pubmed", identifier[7:]
    elif identifier.startswith("http"):
        return "url", identifier
    elif "/" in identifier or len(identifier) > 20:
        # 可能是有版本号的 arXiv ID
        return "arxiv", identifier
    else:
        return "unknown", identifier

def _get_pdf_url(paper_id: str) -> Optional[str]:
    """根据 paper_id 获取 PDF URL"""
    if paper_id.startswith("arxiv:"):
        arxiv_id = paper_id[6:]
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    elif paper_id.startswith("doi:"):
        doi = paper_id[4:]
        return f"https://doi.org/{doi}"
    # ...
```

- [ ] **Step 2: 添加 search_and_fetch 函数**

```python
def search_and_fetch(
    query: str,
    domain: Optional[str] = None,
    max_results: int = 10,
    output_dir: Optional[Path] = None,
) -> dict:
    """搜索论文，用户选择后获取

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
```

- [ ] **Step 3: 更新 download_with_space_check 调用**

- [ ] **Step 4: 测试 + 提交**

---

## Task 7: 集成 rate_limiter

**Files:**
- Modify: `skills/fetch/sources/arxiv.py` 等
- Modify: `skills/fetch/searcher.py`

- [ ] **Step 1: 在 searcher.py 中添加全局 rate limiter**

```python
from .rate_limiter import RateLimiter

# 全局速率限制器: 每个源每分钟 10 个请求
_search_limiters = {
    "arxiv": RateLimiter(rpm=10),
    "pubmed": RateLimiter(rpm=10),
    "semantic_scholar": RateLimiter(rpm=10),
    "crossref": RateLimiter(rpm=10),
}

def _rate_limited_search(source: str, search_func, *args, **kwargs):
    """带速率限制的搜索"""
    limiter = _search_limiters.get(source)
    if limiter:
        limiter.acquire()
    return search_func(*args, **kwargs)
```

- [ ] **Step 2: 测试 + 提交**

---

## Task 8: 更新 SKILL.md

**Files:**
- Modify: `skills/fetch/SKILL.md`

- [ ] **Step 1: 添加搜索命令**

```markdown
### /paper-reader fetch search

Search for papers by keyword.

**Usage:**
/paper-reader fetch search <query> [--domain cs|bio|chem|physics|general] [--max 10]

**Examples:**
/paper-reader fetch search "attention mechanism in transformers"
/paper-reader fetch search "CRISPR gene editing" --domain bio
/paper-reader fetch search "quantum computing" --domain physics
```

- [ ] **Step 2: 提交**
