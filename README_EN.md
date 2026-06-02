<!--
╔══════════════════════════════════════════════════════════════════════╗
║  DreamSeed 种梦计划 — AI创造者大赛  官方 README 模板                ║
║                                                                      ║
║  使用说明：                                                          ║
║  1. 将本模板放在参赛仓库根目录 README.md 的顶部                       ║
║  2. 头图使用 DreamField 官方公开活动图片地址                         ║
║  3. 请保留 DREAMFIELD_README_HEADER_START / END 标识                 ║
║  4. 分割线以下供创作者自由编写项目内容                               ║
╚══════════════════════════════════════════════════════════════════════╝
-->

<!-- DREAMFIELD_README_HEADER_START -->

<p align="center">
  <a href="https://www.dreamfield.top">
    <img src="https://www.dreamfield.top/dream-field/contest-readme/assets/dreamseed-readme-banner.png" alt="DreamSeed 种梦计划参赛作品" width="100%" />
  </a>
</p>

<!-- DREAMFIELD_README_HEADER_END -->

<div align="center">

# Paper Reader

### Intelligent academic paper analysis tool, supporting AI programming agents such as Claude Code.

**Search · Fetch · Analyze · Learn**

---

[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge&color=2ea44f)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Version](https://img.shields.io/badge/version-v1.10.1-blue?style=for-the-badge)](https://github.com/nowa277/paper-reader/releases)

[![Windows](https://img.shields.io/badge/Windows-Supported-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#supported-platforms)
[![macOS](https://img.shields.io/badge/macOS-Supported-A2AAAD?style=for-the-badge&logo=apple&logoColor=white)](#supported-platforms)
[![Linux](https://img.shields.io/badge/Linux-Supported-FCC434?style=for-the-badge&logo=linux&logoColor=black)](#supported-platforms)

[![arXiv](https://img.shields.io/badge/arXiv-Search-orange?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org)
[![PubMed](https://img.shields.io/badge/PubMed-Search-0099CC?style=flat-square)](https://pubmed.ncbi.nlm.nih.gov)
[![Semantic Scholar](https://img.shields.io/badge/Semantic%20Scholar-Search-8C4A8D?style=flat-square)](https://semanticscholar.org)
[![MinerU](https://img.shields.io/badge/MinerU-PDF%20Conversion-red?style=flat-square)](https://github.com/opendatalab/MinerU)

[![Claude Code](https://img.shields.io/badge/Claude_Code-Supported-8B5CF6?style=flat-square)](#supported-agents)
[![Cursor](https://img.shields.io/badge/Cursor-Supported-8B5CF6?style=flat-square)](#supported-agents)
[![Codex](https://img.shields.io/badge/Codex-Supported-8B5CF6?style=flat-square)](#supported-agents)
[![opencode](https://img.shields.io/badge/opencode-Supported-8B5CF6?style=flat-square)](#supported-agents)
[![Hermes Agent](https://img.shields.io/badge/Hermes_Agent-Supported-8B5CF6?style=flat-square)](#supported-agents)
[![Gemini CLI](https://img.shields.io/badge/Gemini_CLI-Supported-8B5CF6?style=flat-square)](#supported-agents)
[![Copilot](https://img.shields.io/badge/Copilot-Supported-8B5CF6?style=flat-square)](#supported-agents)

[**简体中文**](README.md) · [**English**](README_CN.md)

![Paper Reader Hero Banner](hero-banner.png)

</div>

---

## Overview

Paper Reader is an intelligent academic paper analysis tool designed for AI coding agents. It provides a complete workflow from paper search to deep analysis, supporting multiple academic databases and producing structured Markdown output.

**Use cases:**
- Research literature review and summarization
- Quick paper screening for relevance
- Deep analysis of methodology and findings
- Tracking research trends and gaps
- Academic writing preparation

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Source Search** | Search papers across arXiv, PubMed, Semantic Scholar, and CrossRef simultaneously |
| **Auto PDF Download** | Automatic PDF retrieval with multi-source fallback |
| **MinerU Integration** | Convert PDF to Markdown while preserving layout, figures, and tables |
| **Multi-Level Analysis** | Three analysis tiers: Basic, Academic, and Deep Research |
| **Cross-Platform** | Works on Windows, macOS, and Linux |

---

## Installation

```bash
pip install paper-reader
pipx install paper-reader
```

**Requirements:**
- Python 3.10+
- `requests` and `psutil` (installed automatically)

**Optional:** For PDF-to-Markdown conversion, install [MinerU](https://github.com/opendatalab/MinerU) separately.

---

## Quick Start

### Search for Papers

```bash
/paper-reader fetch "machine learning optimization"
```

The agent will search multiple academic databases and return a ranked list of relevant papers with metadata (title, authors, year, abstract, source).

### Analyze a Paper

```bash
/paper-reader analyze <paper-id>
```

Specify the analysis level when prompted:
- **Level A** — Basic: Summary + Key Findings
- **Level B** — Academic: + Methodology + Figures + Related Work
- **Level C** — Deep: + Limitations + Trends + Reproducibility

### Setup Commands

```bash
/paper-reader setup mineru      # Check MinerU status
/paper-reader setup mineru install  # Install MinerU
/paper-reader setup config show  # View configuration
```

---

## Analysis Levels

| Level | Use Case | Output |
|-------|----------|--------|
| **A** | Quick screening, overview | Summary, key findings, one-paragraph abstract |
| **B** | In-depth reading | Full summary, methodology, figures, related work comparison |
| **C** | Research preparation | Critical analysis, limitations, trends, reproducibility assessment |

---

## Multi-Source Search

| Source | Best For |
|--------|----------|
| **arXiv** | Computer Science, Physics, Mathematics, Quantitative Finance |
| **PubMed** | Biomedical, Life Sciences, Medicine |
| **Semantic Scholar** | Broad coverage, citation graphs, AI-powered recommendations |
| **CrossRef** | DOI-based lookup, publisher metadata |

---

## Supported Platforms

| Platform | Status |
|----------|--------|
| Linux | Supported |
| macOS | Supported |
| Windows | Supported |

---

## Supported Agents

| Agent | Status |
|-------|--------|
| Claude Code | Supported |
| Cursor | Supported |
| Codex CLI | Supported |
| opencode | Supported |
| Hermes Agent | Supported |
| Gemini CLI | Supported |
| Copilot | Supported |
| Windsurf | Supported |
| Zed | Supported |

---

## Architecture

```
paper-reader/
├── skills/
│   ├── analyze/           # Paper analysis with multi-level output
│   ├── config/            # Configuration management
│   ├── fetch/             # Paper retrieval and search
│   │   └── sources/      # arXiv, PubMed, Semantic Scholar, CrossRef
│   └── mineru/            # PDF to Markdown conversion
├── agent_adapters/         # Agent adapter implementations
└── tests/                 # Test suite
```

---

## Configuration

Config file: `~/.paper-reader/config.json`

```json
{
  "version": "1.0",
  "mineru": {
    "installed": false,
    "path": null
  },
  "fetch": {
    "default_mode": "jina"
  },
  "analyze": {
    "default_template": "default"
  }
}
```

---

## License

MIT License