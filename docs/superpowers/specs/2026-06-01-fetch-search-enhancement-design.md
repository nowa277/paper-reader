# Fetch 模块增强设计 - 论文搜索功能

**日期:** 2026-06-01
**状态:** 设计完成

---

## 1. 概述

将 fetch 模块从"被动获取"升级为"主动搜索"，支持用户通过关键词/主题搜索论文，并提供交互式选择。

**核心目标:**
- 用户输入主题关键词 → Agent 搜索多源数据库 → 展示结果列表 → 用户选择 → 下载分析

---

## 2. 领域优先级划分

### 2.1 领域定义

| 领域 ID | 名称 | 主要数据库 | Fallback |
|---------|------|-----------|----------|
| `cs` | 计算机/AI/ML | arXiv → Semantic Scholar | CrossRef |
| `bio` | 生物/医学 | PubMed → bioRxiv | Semantic Scholar |
| `chem` | 化学/材料 | CrossRef → RSC | Semantic Scholar |
| `physics` | 物理 | arXiv → NASA ADS | CrossRef |
| `general` | 通用 | Semantic Scholar → CrossRef | arXiv |

### 2.2 领域检测策略

```python
DOMAIN_PRIORITY = {
    "cs": ["cs.AI", "cs.LG", "cs.CL"],  # arXiv categories
    "bio": ["q-bio", "bioinformatics"],
    "physics": ["hep", "cond-mat", "astro-ph"],
}
```

---

## 3. 核心 API 设计

### 3.1 搜索入口

**文件:** `skills/fetch/searcher.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class PaperResult:
    """标准化论文结果"""
    paper_id: str           # 唯一标识 (arXiv ID / DOI / PMID)
    title: str
    authors: list[str]
    year: int
    venue: str              # 期刊/会议名称
    abstract: str
    url: str                # 论文页面 URL
    pdf_url: Optional[str]  # PDF 下载 URL
    domain: str             # 检测到的领域
    source: str             # 来源数据库

def search_papers(
    query: str,
    domain: Optional[str] = None,
    max_results: int = 10,
) -> list[PaperResult]:
    """搜索论文。

    Args:
        query: 搜索关键词
        domain: 限定领域 (None=自动检测)
        max_results: 最大返回数量

    Returns:
        论文结果列表，按相关性排序
    """
    ...
```

### 3.2 多源搜索策略

```python
# 并行搜索 + 串行 fallback
async def _search_arxiv(query: str, category: str) -> list[PaperResult]:
    """搜索 arXiv (仅 CS/Physics)"""

async def _search_pubmed(query: str) -> list[PaperResult]:
    """搜索 PubMed (仅 Bio/Medical)"""

async def _search_semantic_scholar(query: str) -> list[PaperResult]:
    """搜索 Semantic Scholar (通用)"""

async def _search_crossref(query: str) -> list[PaperResult]:
    """搜索 CrossRef (跨学科)"""
```

**优先级:**
1. 如果 domain == "cs" 或 "physics" → arXiv 优先
2. 如果 domain == "bio" → PubMed 优先
3. 否则 → Semantic Scholar 优先
4. 各源结果合并去重 (按 paper_id)

### 3.3 结果归一化

```python
def normalize_paper(raw: dict, source: str) -> PaperResult:
    """将各数据库的原始结果转为标准格式。"""
    # 统一字段名: title, authors, year, abstract, url, pdf_url
    # 统一 ID 格式: "arxiv:2301.00001", "doi:10.1038/nature12373"
```

---

## 4. Fetch 模块更新

### 4.1 更新后的 fetcher.py

```python
def fetch_paper(identifier: str, output_dir: Optional[Path] = None) -> dict:
    """获取单篇论文。

    Args:
        identifier: 论文标识符 (URL / arXiv ID / DOI / PMID)
        output_dir: 输出目录

    Returns:
        dict with keys: success, path, content
    """
    # 1. 解析 identifier 类型
    # 2. 调用对应来源获取 PDF
    # 3. 保存到 output_dir
    ...

def search_and_fetch(
    query: str,
    domain: Optional[str] = None,
    max_results: int = 10,
    output_dir: Optional[Path] = None,
) -> dict:
    """搜索论文，用户选择后获取。

    Returns:
        dict with keys: success, selected, path
    """
    # 1. search_papers() 获取结果
    # 2. 展示列表供用户选择
    # 3. fetch_paper() 获取选中论文
    ...
```

---

## 5. 文件结构

```
skills/fetch/
├── __init__.py
├── fetcher.py           # 更新: search_and_fetch(), fetch_paper()
├── rate_limiter.py      # 已有
├── checkpoint.py        # 已有
├── searcher.py          # 新增: 多源搜索
├── models.py            # 新增: PaperResult dataclass
└── sources/
    ├── __init__.py
    ├── arxiv.py         # 新增: arXiv API
    ├── pubmed.py        # 新增: PubMed API
    ├── semantic_scholar.py  # 新增: Semantic Scholar API
    └── crossref.py      # 新增: CrossRef API
```

---

## 6. 已有模块复用

| 模块 | 用途 | 复用方式 |
|------|------|----------|
| `rate_limiter.py` | API 速率限制 | 限制各源 API 调用频率 |
| `checkpoint.py` | 断点续传 | 记录已下载的 paper_id |
| `ensure_dir()` | 目录创建 | 复用 |
| `check_disk_space()` | 磁盘检查 | 复用 |

---

## 7. 验收标准

- [ ] `search_papers("attention mechanism")` 返回标准格式结果
- [ ] 领域自动检测正确 (cs → arXiv, bio → PubMed)
- [ ] 结果去重 (相同 paper_id 只保留一条)
- [ ] `fetch_paper("arxiv:2301.00001")` 正确下载 PDF
- [ ] Rate limiter 防止 API 超限
- [ ] checkpoint 防止重复下载
- [ ] 用户选择后能正确获取 PDF
