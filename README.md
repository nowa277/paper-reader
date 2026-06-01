# Paper Reader Skill

An intelligent academic paper analysis tool for Claude Code and other AI coding agents.

## Features

- **Multi-Source Paper Search** - Search across arXiv, PubMed, Semantic Scholar, and CrossRef
- **Automatic PDF Download** - Download papers from various sources
- **MinerU Integration** - Convert PDF papers to Markdown for analysis
- **Multi-Level Analysis** - Three levels of analysis (Basic, Academic, Deep Research)
- **Cross-Platform Support** - Works on Linux, macOS, and Windows

## Installation

1. Install dependencies:
```bash
pip install requests psutil
```

2. Install MinerU (optional, for PDF conversion):
```bash
paper-reader setup mineru install
```

## Usage

### Search and Download Papers

```
/paper-reader fetch <topic-or-keywords>
```

### Analyze Papers

```
/paper-reader analyze <paper-id>
```

### Analysis Levels

- **Level A (Basic)** - Summary + Key Findings
- **Level B (Academic)** - Summary + Key Findings + Methodology + Figures + Related Work
- **Level C (Deep)** - Full Academic + Limitations + Trends + Reproducibility

## Architecture

```
paper-reader/
├── skills/
│   ├── config/        # Configuration management
│   ├── mineru/        # MinerU PDF parser
│   ├── fetch/         # Paper retrieval
│   │   └── sources/   # arXiv, PubMed, Semantic Scholar, CrossRef
│   └── analyze/       # Paper analysis
├── agent_adapters/    # Adapter templates for other AI agents
├── docs/             # Design documents
└── tests/            # Test suite
```

## Configuration

Configuration is stored at `~/.paper-reader/config.json`.

## License

MIT
