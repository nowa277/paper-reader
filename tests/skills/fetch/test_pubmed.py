"""Tests for PubMed API source."""
import pytest
from unittest.mock import patch, MagicMock
from xml.etree import ElementTree as ET

from skills.fetch.sources.pubmed import (
    _parse_pubmed_xml,
    _parse_article,
    search_pubmed,
)


# --- _parse_pubmed_xml tests ---

PUBmed_XML = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>Test Paper Title</ArticleTitle>
        <AuthorList>
          <Author>
            <LastName>Smith</LastName>
            <ForeName>John</ForeName>
          </Author>
          <Author>
            <LastName>Doe</LastName>
            <ForeName>Jane</ForeName>
          </Author>
        </AuthorList>
        <Abstract>
          <AbstractText>This is a test abstract for the paper. It contains details about the methodology and results.</AbstractText>
        </Abstract>
      </Article>
      <PubDate>
        <Year>2023</Year>
        <Month>Jan</Month>
        <Day>15</Day>
      </PubDate>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="doi">10.1234/abc</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


class TestParsePubmedXml:
    def test_parses_valid_xml(self):
        papers = _parse_pubmed_xml(PUBmed_XML)

        assert len(papers) == 1
        paper = papers[0]
        assert paper.paper_id == "pubmed:12345678"
        assert paper.title == "Test Paper Title"
        assert paper.authors == ["John Smith", "Jane Doe"]
        assert paper.year == 2023
        assert paper.abstract == "This is a test abstract for the paper. It contains details about the methodology and results."
        assert paper.url == "https://pubmed.ncbi.nlm.nih.gov/12345678/"
        assert paper.pdf_url == "https://doi.org/10.1234/abc"
        assert paper.source == "pubmed"

    def test_handles_empty_xml(self):
        papers = _parse_pubmed_xml("<?xml version=\"1.0\"?><PubmedArticleSet/>")
        assert papers == []

    def test_handles_malformed_xml(self):
        papers = _parse_pubmed_xml("not valid xml at all")
        assert papers == []


class TestParseArticle:
    def test_returns_none_when_pmid_missing(self):
        xml = """<PubmedArticle>
            <MedlineCitation>
                <Article><ArticleTitle>No PMID</ArticleTitle></Article>
            </MedlineCitation>
        </PubmedArticle>"""
        article = ET.fromstring(xml)
        assert _parse_article(article) is None

    def test_handles_journal_pubdate_fallback(self):
        """Year can come from Journal/JournalIssue/PubDate when Article PubDate is absent."""
        xml = """<?xml version="1.0"?>
        <PubmedArticleSet>
          <PubmedArticle>
            <MedlineCitation>
              <PMID>99999999</PMID>
              <Article>
                <ArticleTitle>Paper with Journal Date</ArticleTitle>
                <Journal>
                  <JournalIssue>
                    <PubDate>
                      <Year>2021</Year>
                      <Month>Mar</Month>
                    </PubDate>
                  </JournalIssue>
                </Journal>
              </Article>
            </MedlineCitation>
            <PubmedData/>
          </PubmedArticle>
        </PubmedArticleSet>"""
        papers = _parse_pubmed_xml(xml)
        assert len(papers) == 1
        assert papers[0].year == 2021

    def test_handles_missing_abstract(self):
        xml = """<?xml version="1.0"?>
        <PubmedArticleSet>
          <PubmedArticle>
            <MedlineCitation>
              <PMID>11111111</PMID>
              <Article>
                <ArticleTitle>No Abstract Paper</ArticleTitle>
                <AuthorList>
                  <Author><LastName>Test</LastName></Author>
                </AuthorList>
              </Article>
              <PubDate><Year>2022</Year></PubDate>
            </MedlineCitation>
            <PubmedData/>
          </PubmedArticle>
        </PubmedArticleSet>"""
        papers = _parse_pubmed_xml(xml)
        assert len(papers) == 1
        assert papers[0].abstract == ""
        assert papers[0].pdf_url is None


# --- search_pubmed integration with mocked HTTP ---

MOCK_ESearch_RESPONSE = {
    "esearchresult": {
        "idlist": ["12345678", "87654321"],
    }
}

MOCK_EFetch_XML = """<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>First Result Paper</ArticleTitle>
        <AuthorList>
          <Author><LastName>Alpha</LastName><ForeName>A.</ForeName></Author>
        </AuthorList>
        <Abstract><AbstractText>Abstract of first result.</AbstractText></Abstract>
      </Article>
      <PubDate><Year>2023</Year></PubDate>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="doi">10.1000/first</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>87654321</PMID>
      <Article>
        <ArticleTitle>Second Result Paper</ArticleTitle>
        <AuthorList>
          <Author><LastName>Beta</LastName><ForeName>B.</ForeName></Author>
        </AuthorList>
        <Abstract><AbstractText>Abstract of second result.</AbstractText></Abstract>
      </Article>
      <PubDate><Year>2022</Year></PubDate>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="doi">10.1000/second</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


class TestSearchPubmed:
    @patch("skills.fetch.sources.pubmed.requests.get")
    def test_search_pubmed_returns_results(self, mock_get):
        # 第一次调用：ESearch，第二次调用：EFetch
        mock_get.side_effect = [
            _mock_json_response(MOCK_ESearch_RESPONSE),
            _mock_response(MOCK_EFetch_XML),
        ]

        results = search_pubmed("cancer", max_results=10)

        assert len(results) == 2
        assert results[0].title == "First Result Paper"
        assert results[0].authors == ["A. Alpha"]
        assert results[0].year == 2023
        assert results[0].paper_id == "pubmed:12345678"
        assert results[1].title == "Second Result Paper"
        assert results[1].year == 2022
        assert results[1].source == "pubmed"

    @patch("skills.fetch.sources.pubmed.requests.get")
    def test_search_pubmed_returns_empty_when_no_results(self, mock_get):
        empty_response = {"esearchresult": {"idlist": []}}
        mock_get.return_value = _mock_json_response(empty_response)

        results = search_pubmed("xyznonexistent", max_results=5)

        assert results == []
        # EFetch should not be called when idlist is empty
        assert mock_get.call_count == 1

    @patch("skills.fetch.sources.pubmed.requests.get")
    def test_search_pubmed_api_params(self, mock_get):
        mock_get.return_value = _mock_json_response({"esearchresult": {"idlist": []}})

        search_pubmed("machine learning", max_results=5)

        assert mock_get.call_count == 1
        call_args = mock_get.call_args
        assert "esearch.fcgi" in call_args[0][0]
        assert call_args[1]["params"]["term"] == "machine learning"
        assert call_args[1]["params"]["retmax"] == 5
        assert call_args[1]["params"]["retmode"] == "json"
        assert call_args[1]["timeout"] == 30


# --- helpers ---

def _mock_response(text: str):
    mock = MagicMock()
    mock.text = text
    mock.raise_for_status = MagicMock()
    return mock


def _mock_json_response(data: dict):
    mock = MagicMock()
    mock.json = MagicMock(return_value=data)
    mock.raise_for_status = MagicMock()
    return mock
