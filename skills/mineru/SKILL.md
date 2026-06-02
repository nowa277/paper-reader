# MinerU Sub-Skill

Handles MinerU PDF parser detection, installation, and management.

## Commands

### /paper-reader setup mineru
Main entry point - runs detection and shows MinerU status.

### /paper-reader setup mineru detect
Run MinerU detection only. Returns:
- `installed`: Whether MinerU is installed
- `path`: Path to magic-pdf executable (if found)
- `version`: Installed version (if found)

### /paper-reader setup mineru install
Install MinerU. Requires user confirmation before proceeding.

**Prerequisites:**
- Python 3.10 or higher
- User consent (installation will not proceed without it)

### /paper-reader setup mineru status
Show detailed MinerU status including:
- Installation status
- Version
- Executable path
- Last check timestamp

## Usage Examples

```
/paper-reader setup mineru
/paper-reader setup mineru detect
/paper-reader setup mineru install
/paper-reader setup mineru status
```

## Technical Details

- **Detection:** Uses multiple methods (pip show, which command, common paths)
- **Installation:** Uses pip to install mineru package
- **Config:** Installation status is stored in `~/.paper-reader/config.json`