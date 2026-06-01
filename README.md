<div align="center">

# Paper Reader Skill

**智能学术论文分析工具，支持 Claude Code 等 AI 编程 Agent**

*Search · Fetch · Analyze · Learn*

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)

</div>

---

## Overview

Paper Reader is an intelligent academic paper analysis tool for AI coding agents. It enables seamless searching, fetching, and analyzing of academic papers from multiple sources with structured Markdown output.

**Key capabilities:**
- Multi-source paper search (arXiv, PubMed, Semantic Scholar, CrossRef)
- Automatic PDF download and conversion via MinerU
- Three-tier analysis (Basic / Academic / Deep Research)
- Cross-platform support (Linux, macOS, Windows)

---

## Get Started

```bash
# Search papers
/paper-reader fetch "machine learning optimization"

# Analyze papers
/paper-reader analyze <paper-id>
```

**Installation:**

```bash
# Install dependencies
pip install requests psutil

# Install MinerU (optional, for PDF conversion)
paper-reader setup mineru install
```

---

## Analysis Levels

| Level | Description |
|-------|-------------|
| **A** | Basic — Summary + Key Findings |
| **B** | Academic — + Methodology + Figures + Related Work |
| **C** | Deep — + Limitations + Trends + Reproducibility |

---

## Multi-Source Search

| Source | Coverage |
|--------|----------|
| arXiv | Physics, Math, CS, Quantitative Biology, Quantitative Finance, Statistics |
| PubMed | Biomedical literature |
| Semantic Scholar | CS, Medicine, arXiv open-access |
| CrossRef | DOI-based metadata for academic publishers |

---

## Architecture

```
paper-reader/
├── skills/
│   ├── analyze/       # Paper analysis
│   ├── config/        # Configuration management
│   ├── fetch/         # Paper retrieval
│   │   └── sources/  # arXiv, PubMed, Semantic Scholar, CrossRef
│   └── mineru/        # PDF parsing
├── agent_adapters/     # Agent adapters
└── tests/             # Test suite
```

---

## License

MIT License
