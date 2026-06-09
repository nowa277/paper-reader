---
name: paper-reader
description: Academic paper analysis tool with v2.0 decision-driven workflow. Uses MinerU for PDF extraction and provides L1-L4 granularity analysis. Use when analyzing papers, extracting content from PDFs, or building knowledge graphs from academic documents.
version: "2.0.0"
metadata:
  homepage: "https://github.com/nowa277/paper-reader"
  requires:
    bins:
      - python3
    anyBins:
      - pip
      - pip3
---

# Paper Reader

Claude Code skill for academic paper analysis with decision-driven workflow.

## Trigger

`/paper-reader` — Invoke paper reader skill

## Overview

Paper Reader v2.0 — intelligent academic paper analysis tool with hierarchical granularity (L1-L4).

## Usage

```
/paper-reader <command> [args]
```

## Commands

- `/paper-reader setup config` — Configuration management
- `/paper-reader setup mineru` — MinerU PDF parser management
- `/paper-reader fetch <url>` — Retrieve papers
- `/paper-reader analyze <path>` — Analyze papers (v2.0 workflow)

## v2.0 Analysis Workflow

1. Read `METHODOLOGY.md` — decision framework
2. Answer 4 questions — doc type / scale / intent / output
3. Run decision prompts — granularity/chunking/graph/output
4. Call `analyze_with_decision(decision)`

## Installation

```bash
git clone https://github.com/nowa277/paper-reader.git
cd paper-reader
pip install -e .
```

Or use Docker: `docker build -t paper-reader .`