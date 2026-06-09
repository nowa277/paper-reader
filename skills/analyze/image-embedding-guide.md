# Image Embedding Guide

## Overview

This module provides image extraction and embedding capabilities for PDF/VLM analysis output, with Obsidian-compatible markdown generation.

## Embedding Strategies

### 1. Base64 Inline (`base64_inline`)

**When to use:**
- Small images (< 50KB)
- Images with dimensions ≤ 400x400
- Inline images in transient analysis

**How it works:**
- Encodes image as base64 data URI
- Embeds directly in markdown: `![alt](data:image/png;base64,...)`
- No separate image files needed
- Portable but increases markdown file size

**Example:**
```markdown
![Figure 1](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==)
```

### 2. External File (`external_file`)

**When to use:**
- Large images (> 50KB)
- High-resolution figures
- Images that may be reused across documents

**How it works:**
- Saves image to disk in output directory
- References by relative/absolute path
- Markdown: `![](images/paper1_page1_0.png)`

### 3. Obsidian Embed (`obsidian_embed`)

**When to use:**
- **Preferred for Obsidian KB workflows**
- Images stored in the same vault
- Want to leverage Obsidian's image handling

**How it works:**
- Saves image to configured output directory
- Uses Obsidian wikilink syntax: `![[image.png]]`
- Obsidian automatically handles display

**Example:**
```markdown
![[paper1_page1_fig1.png]]
```

## Integration with L1-L4 Granularity

| Level | Image Strategy | Notes |
|-------|----------------|-------|
| **L1** (concepts) | Minimal | Few images, mostly diagrams |
| **L2** (relations) | External preferred | Figures help illustrate relations |
| **L3** (ontology) | Obsidian embed | KB use case benefits from embed |
| **L4** (evidence) | Mixed | Use base64 for small evidence images |

### L1 - Concepts
- Focus on text extraction
- Skip inline images in favor of external/obsidian
- Caption-only approach for figures

### L2 - Relations
- Embed key diagrams showing relationships
- Use external file for complex visualizations
- Reference figures in relations.md

### L3 - Ontology
- Use Obsidian embed for KB compatibility
- Organize images in dedicated folder
- Link from hierarchy.md concepts

### L4 - Evidence
- Combine strategies based on size
- Base64 for small inline evidence
- External for full-page figures

## Configuration

Edit `image_config.yaml` to customize behavior:

```yaml
# Max size for base64 inline (bytes)
max_inline_size_bytes: 51200

# Max dimensions for inline
max_inline_dimensions: [400, 400]

# Output directory for external images
output_dir: images

# Filename pattern
naming_pattern: "{paper_id}_page{page}_{index}"
```

## Anti-Patterns

### 1. Never use base64 for large images
- **Bad:** Embedding 5MB images as base64
- **Impact:** Markdown files become unusable (memory/browser issues)
- **Fix:** Use external file or Obsidian embed

### 2. Don't mix embedding strategies inconsistently
- **Bad:** Randomly using base64 for some images, external for others
- **Impact:** Inconsistent vault structure, hard to maintain
- **Fix:** Use consistent strategy per document type

### 3. Avoid hardcoded paths
- **Bad:** `![](C:/Users/name/images/...)`
- **Impact:** Not portable across machines
- **Fix:** Use relative paths or Obsidian wikilinks

### 4. Don't skip image metadata
- **Bad:** Losing track of which page/figure each image came from
- **Impact:** Can't verify accuracy, hard to update
- **Fix:** Use ImageMetadata to track page/caption/source

## API Usage

```python
from skills.analyze.image_embedder import (
    ImageEmbedder,
    ImageEmbedConfig,
    create_default_embedder,
    load_config,
)
from pathlib import Path

# Option 1: Use defaults
embedder = create_default_embedder()

# Option 2: Load from YAML config
config = load_config(Path("skills/analyze/image_config.yaml"))
embedder = ImageEmbedder(config)

# Detect images from VLM output
vlm_content = open("paper.md").read()
images = embedder.detect_images_from_vlm_output(vlm_content)

# Or from MinerU content_list.json
import json
content_list = json.loads(open("content_list.json").read())
images = embedder.detect_images_from_content_list(content_list)

# Embed images
output_dir = Path("output/paper1/")
embedded = embedder.embed_images_batch(images, output_dir, "paper1")

# Export manifest for debugging
embedder.export_image_manifest(embedded, output_dir / "image_manifest.json")
```

## File Structure

After processing, your output directory will contain:

```
output/paper1/
├── concepts.md           # Contains ![[image.png]] references
├── relations.md
├── images/
│   ├── paper1_page1_0.png
│   ├── paper1_page1_1.png
│   └── paper1_page3_fig1.png
└── image_manifest.json   # Optional: for debugging
```

## Testing

Run the test suite:

```bash
python -m pytest tests/skills/analyze/test_image_embedder.py -v
```

## See Also

- [analyzer.py](./analyzer.py) - Main analysis module
- [SKILL.md](./SKILL.md) - Skill overview
- [METHODOLOGY.md](./METHODOLOGY.md) - Decision framework