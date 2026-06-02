# Fetch Sub-Skill

Handles paper retrieval from various sources.

## Commands

### /paper-reader fetch search

Search for papers by keyword across multiple academic databases.

**Usage:**
/paper-reader fetch search <query> [--domain cs|bio|chem|physics|general] [--max 10]

**Arguments:**
- query: Search keywords
- --domain: Limit to specific domain (cs, bio, chem, physics, general). Auto-detected if omitted.
- --max: Maximum results per source (default: 10)

**Examples:**
/paper-reader fetch search "attention mechanism in transformers"
/paper-reader fetch search "CRISPR gene editing" --domain bio
/paper-reader fetch search "quantum computing" --domain physics

### /paper-reader fetch

Fetch a paper by identifier.

**Usage:**
/paper-reader fetch <identifier>

**Supported identifiers:**
- arXiv ID: "2301.00001" or "arxiv:2301.00001"
- DOI: "10.1038/nature12373" or "doi:10.1038/nature12373"
- PubMed ID: "12345678" or "pubmed:12345678"
- URL: "https://..."

**Examples:**
/paper-reader fetch arxiv:2301.00001
/paper-reader fetch doi:10.1038/nature12373
/paper-reader fetch https://arxiv.org/abs/2301.00001

## Supported Sources

The fetch module searches multiple academic databases:
- **arXiv** (cs, physics) - Free open-access papers
- **PubMed** (bio, medical) - Biomedical literature
- **Semantic Scholar** - AI-powered academic search
- **CrossRef** - Cross-disciplinary metadata

Results are deduplicated and sorted by year.
