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
