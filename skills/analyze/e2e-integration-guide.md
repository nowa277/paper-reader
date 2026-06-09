# E2E Integration Guide

**Plan 5: amber-agent end-to-end integration for paper-reader**

This guide covers how to run the full pipeline from PDF to verified knowledge graph output.

---

## Overview

The E2E integration module (`e2e_integration.py`) orchestrates the complete analysis pipeline:

```
PDF → VLM (MinerU) → subagent analysis → verification → output
```

### Supported Configurations

| Document | Pages | Tokens | Target Level | Trigger Mode |
|----------|-------|--------|--------------|--------------|
| amber26 | 1112 | 2.5M | L3/L4 | HIERARCHICAL |
| alphafold | 27 | 60K | L1/L2 | SINGLE |
| colabfold | 50 | 100K | L2 | SINGLE |
| amber_tutorials | 150 | 300K | L2/L3 | SINGLE |
| go_best_practices | 80 | 200K | L2 | SINGLE |

---

## Quick Start

### Basic Usage

```python
from pathlib import Path
from skills.analyze.e2e_integration import run_full_pipeline, create_e2e_integration
from skills.analyze.analyzer import Decision

# Minimal usage with just level
result = run_full_pipeline(
    paper_id="my-paper",
    vlm_path="mineru_output/my-paper/",
    level="L2",
)

print(f"Status: {result.status}")
print(f"Files: {list(result.output_files.keys())}")
```

### With Custom Configuration

```python
from skills.analyze.e2e_integration import E2EIntegration, E2EConfig, PDFConfig
from skills.analyze.analyzer import Decision

# Custom configuration
config = E2EConfig(
    default_output_dir=Path("~/obsidian/AI/amber-agent/kb/"),
    enable_verification=True,
    enable_image_embedding=True,
)

e2e = E2EIntegration(config)

# Load PDF-specific config
pdf_config = e2e.load_pdf_config(
    Path("skills/analyze/verification/config_amber26.yaml")
)

# Create decision
decision = Decision(
    level="L3",
    base_dir=Path("~/obsidian/AI/amber-agent/kb/amber26/"),
    doc_name="amber26",
    format="markdown",
    use_case="kb",
    relations=True,
    hierarchy=True,
)

# Run pipeline
result = e2e.run_pipeline(
    paper_id="amber26",
    vlm_path="mineru_output/amber26/",
    decision=decision,
    config=pdf_config,
)

print(f"Pipeline completed: {result.success}")
print(f"Duration: {result.total_duration_seconds:.2f}s")
```

---

## Pipeline Stages

The pipeline executes in 7 stages:

1. **DETECT** - Check for amber-agent VLM output (`vlm/` or `hybrid_auto/` subdir)
2. **PARSE** - Read markdown content and metadata from VLM output
3. **DECIDE** - Validate Decision against PDF configuration
4. **ANALYZE** - Generate scaffold files based on level (L1-L4)
5. **VERIFY** - Run L1/L2/L3 verification checks
6. **EMBED_IMAGES** - Embed images with strategy selection
7. **OUTPUT** - Write final output files

### Stage Results

Each stage returns a `StageResult` with:
- `stage`: PipelineStage enum
- `status`: PipelineStatus (COMPLETED, PARTIAL, FAILED)
- `duration_seconds`: Execution time
- `message`: Human-readable status
- `data`: Stage-specific data

---

## Verification Levels

Based on spec §15.2-15.4:

| Level | Purpose | Checks |
|-------|---------|--------|
| L1 | Format self-check | wikilink_format, frontmatter_exists, callout_format, image_syntax |
| L2 | Content sampling | concept_definitions (80% pass), backlinks_exist |
| L3 | Completeness check | no_orphan_nodes, hierarchy_levels, kg_schema_compliance |

### Retry Logic

- **L1 failure**: Subagent retries with shuffled prompt (1 time max)
- **L2 failure > 20%**: Retry with failure samples
- **L3 failure**: Auto-retry once, then ask user

---

## Image Embedding Strategy

Images are embedded using one of three strategies based on size/dimensions:

| Strategy | Condition | Output |
|----------|-----------|--------|
| BASE64_INLINE | < 50KB, < 400x400px | Data URI in markdown |
| EXTERNAL_FILE | Large images | File saved to disk |
| OBSIDIAN_EMBED | Default | `![[filename.png]]` wikilink |

---

## Configuration Files

### E2E Pipeline Config (`e2e_config.yaml`)

```yaml
stages:
  - name: detect
    enabled: true
    timeout_seconds: 30

verification:
  default_levels:
    - L1
    - L2
    - L3

image_embedding:
  enabled: true
  max_inline_size_bytes: 51200
  max_inline_dimensions: [400, 400]
```

### PDF Config (Plan 3)

Located in `skills/analyze/verification/config_*.yaml`:
- `config_amber26.yaml` - 1112 pages, L3/L4
- `config_alphafold.yaml` - 27 pages, L1/L2
- `config_colabfold.yaml` - 50 pages, L2
- `config_amber_tutorials.yaml` - 150 pages, L2/L3
- `config_go_best_practices.yaml` - 80 pages, L2

---

## Troubleshooting

### VLM Output Not Found

```
Error: No 'vlm/' or 'hybrid_auto/' subdir found under <path>
```

**Solution**: Ensure amber-agent/MinerU has been run first:
```bash
# Run MinerU on your PDF first
mineru parse --input paper.pdf --output mineru_output/paper/
```

### Verification Failures

**L1 failures**: Check YAML frontmatter format:
```markdown
---
title: My Paper
author: Author Name
---
```

**L2 failures**: Ensure concepts have definitions after wikilinks:
```markdown
[[Concept]]: Definition here
```

**L3 failures**: Check for orphan concepts (appearing only once).

### Memory/Performance Issues

For large documents (>500K tokens):
- Use HIERARCHICAL trigger mode
- Enable checkpointing
- Increase subagent timeout

---

## Performance Considerations

### Token-Based Triggers

| Token Count | Mode | Subagents |
|-------------|------|-----------|
| < 50K | SINGLE | 1 |
| 50K-200K | MAP_REDUCE | 3-5 |
| 200K-500K | MAP_REDUCE_OR_HIERARCHICAL | 5-10 |
| > 500K | HIERARCHICAL | 11+ (sub-masters) |

### Caching

Enable caching to speed up repeated runs:
```python
config = E2EConfig(
    enable_caching=True,
    cache_dir=".cache/paper-reader",
)
```

---

## API Reference

### Core Classes

- `E2EIntegration`: Main orchestrator class
- `E2EConfig`: Pipeline configuration
- `PDFConfig`: Document-specific configuration
- `PipelineResult`: Full pipeline execution result
- `StageResult`: Individual stage result

### Key Functions

```python
# Create configured integration
create_e2e_integration(output_dir, enable_verification, enable_image_embedding)

# One-shot pipeline execution
run_full_pipeline(paper_id, vlm_path, level, output_dir, config_path)

# Load PDF configuration
e2e.load_pdf_config(config_path)
```

### Enums

- `PipelineStage`: DETECT, PARSE, DECIDE, ANALYZE, VERIFY, EMBED_IMAGES, OUTPUT
- `PipelineStatus`: PENDING, RUNNING, COMPLETED, FAILED, PARTIAL
- `VerificationLevel`: L1, L2, L3
- `EmbeddingStrategy`: BASE64_INLINE, EXTERNAL_FILE, OBSIDIAN_EMBED

---

## Examples

### Analyze a User Guide (L2)

```python
result = run_full_pipeline(
    paper_id="user-guide",
    vlm_path="mineru_output/user-guide/",
    level="L2",  # concepts + relations
)
```

### Build a Knowledge Base (L3)

```python
e2e = create_e2e_integration(
    output_dir=Path("~/obsidian/AI/kb/"),
    enable_verification=True,
)

pdf_config = e2e.load_pdf_config(
    Path("skills/analyze/verification/config_amber26.yaml")
)

decision = Decision(
    level="L3",
    base_dir=Path("~/obsidian/AI/kb/amber26/"),
    doc_name="amber26",
    format="markdown",
    use_case="kb",
    relations=True,
    hierarchy=True,
)

result = e2e.run_pipeline(
    paper_id="amber26",
    vlm_path="mineru_output/amber26/",
    decision=decision,
    config=pdf_config,
)
```

### Run Without Verification (Fast Mode)

```python
config = E2EConfig(
    enable_verification=False,
    enable_image_embedding=False,
)
e2e = E2EIntegration(config)
# ... run pipeline
```

---

## Related Documentation

- [METHODOLOGY.md](./METHODOLOGY.md) - Decision framework
- [SKILL.md](./SKILL.md) - Full skill documentation
- [verification/](./verification/) - Verification configs and levels
- [image_embedder.py](./image_embedder.py) - Image embedding details
- [amber_agent_adapter.py](./amber_agent_adapter.py) - VLM output detection