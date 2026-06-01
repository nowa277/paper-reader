# Paper Reader

Academic paper analysis skill with hierarchical sub-skill architecture.

## Overview

Paper Reader is an intelligent academic paper analysis tool that uses MinerU for PDF extraction. It provides a 3-tier content acquisition system and 5-stage processing pipeline.

## Sub-Skill Hierarchy

```
/paper-reader
├── setup
│   ├── config    → Configuration management
│   └── mineru    → MinerU detection/installation
├── fetch         → Paper retrieval
└── analyze       → Paper analysis
```

## Commands

### Setup Commands

#### /paper-reader setup config
Manage configuration settings.

**Sub-commands:**
- `/paper-reader setup config show` — Display current configuration
- `/paper-reader setup config set <key> <value>` — Set configuration value

#### /paper-reader setup mineru
Manage MinerU PDF parser.

**Sub-commands:**
- `/paper-reader setup mineru` — Run detection and show status
- `/paper-reader setup mineru detect` — Run detection only
- `/paper-reader setup mineru install` — Install MinerU (requires user consent)
- `/paper-reader setup mineru status` — Show detailed MinerU status

**Aliases:** `mineru` → `setup mineru`, `mu` → `setup mineru`

### Fetch Commands

#### /paper-reader fetch
Retrieve papers from various sources.

**Sources (in priority order):**
1. Jina Reader — Web page to markdown
2. Direct Download — URL to PDF
3. Web Search — Search and download

**Usage:**
```
/paper-reader fetch <url-or-search-term>
```

**Aliases:** `f`, `get`

### Analyze Commands

#### /paper-reader analyze
Analyze downloaded papers.

**Usage:**
```
/paper-reader analyze <paper-path>
```

**Aliases:** `a`, `analysis`

## Quick Start

1. **Check MinerU status:**
   ```
   /paper-reader setup mineru
   ```

2. **Install MinerU (first time only):**
   ```
   /paper-reader setup mineru install
   ```

3. **Fetch a paper:**
   ```
   /paper-reader fetch https://arxiv.org/abs/xxxx.xxxxx
   ```

4. **Analyze a paper:**
   ```
   /paper-reader analyze ./papers/paper.pdf
   ```

## Configuration

Configuration is stored at `~/.paper-reader/config.json`.

**Structure:**
```json
{
  "version": "1.0",
  "initialized_skills": [],
  "mineru": {
    "installed": false,
    "path": null,
    "version": null,
    "last_check": null
  },
  "fetch": {
    "default_mode": "jina"
  },
  "analyze": {
    "default_template": "default"
  }
}
```

## Platform Support

- **Linux** (Ubuntu, Debian, RedHat)
- **macOS**
- **Windows**

MinerU auto-detection and installation works across all platforms.

## Sub-Skills

- **config** — Configuration management sub-skill
- **mineru** — MinerU PDF parser management sub-skill  
- **fetch** — Paper retrieval sub-skill
- **analyze** — Paper analysis sub-skill

Each sub-skill can be invoked directly via the Skill tool using the format `paper-reader:sub-skill-name`.