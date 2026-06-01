# Paper Reader Config System - Implementation Plan

**Created:** 2026-06-01  
**Phase:** 1 - Config System with Hierarchical Sub-Skill Architecture

## Objective
Implement a hierarchical sub-skill architecture for paper-reader skill with unified config management and intelligent path detection/installation.

---

## Phase 1: Core Infrastructure

### Task 1.1: Directory Structure Setup
**Objective:** Create the hierarchical sub-skill directory structure

```
paper-reader/
├── skills/
│   ├── config/
│   │   ├── SKILL.md
│   │   ├── config_manager.py
│   │   └── __init__.py
│   ├── mineru/
│   │   ├── SKILL.md
│   │   ├── detector.py
│   │   ├── installer.py
│   │   └── __init__.py
│   ├── fetch/
│   │   ├── SKILL.md
│   │   └── __init__.py
│   └── analyze/
│       ├── SKILL.md
│       └── __init__.py
├── config.json (unified config)
├── main_skill.py
└── SKILL.md
```

### Task 1.2: Config Manager Implementation
**File:** `skills/config/config_manager.py`

Create a `ConfigManager` class with:
- `load()`: Read from `~/.paper-reader/config.json`
- `save()`: Write to config file
- `get(key, default=None)`: Get config value
- `set(key, value)`: Set config value and save
- `get_all()`: Get entire config
- Path: Create `~/.paper-reader/` directory if not exists
- Error handling: Create default config if corrupted

### Task 1.3: Unified Config Structure
**File:** `~/.paper-reader/config.json`

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

### Task 1.4: Platform Detection Utility
**File:** `skills/config/platform.py`

Create platform detection with:
- `get_platform()`: Returns 'linux', 'macos', 'windows'
- `get_linux_distro()`: For Linux, returns 'ubuntu', 'debian', 'redhat', etc.
- `is_wsl()`: Detect if running under WSL

---

## Phase 2: MinerU Sub-Skill

### Task 2.1: MinerU Detector
**File:** `skills/mineru/detector.py`

Implement detection logic:
1. Check `pip show mineru` for installed version
2. Check `which magic-pdf` (CLI entry point)
3. Check common installation paths:
   - Linux: `~/.local/bin/`, `/usr/local/bin/`
   - macOS: `~/Library/Python/*/bin/`, `/usr/local/bin/`
   - Windows: `C:\Python*\Scripts\`
4. Return: `{installed: bool, path: str|null, version: str|null}`

### Task 2.2: MinerU Installer
**File:** `skills/mineru/installer.py`

Implement installation flow:
1. Check Python version (require 3.10+)
2. User confirmation prompt (required by design)
3. Platform-specific installation:
   - Linux/macOS: `pip install mineru`
   - Windows: `pip install mineru`
4. Verify installation after completion
5. Update config with installation status

### Task 2.3: MinerU Skill Entry
**File:** `skills/mineru/SKILL.md`

- `/paper-reader setup mineru` - Main entry point
- `/paper-reader setup mineru detect` - Run detection only
- `/paper-reader setup mineru install` - Run installation
- `/paper-reader setup mineru status` - Show MinerU status

---

## Phase 3: Integration & Main Skill

### Task 3.1: Main Skill Entry Point
**File:** `main_skill.py`

Implement routing:
- Parse user command after `/paper-reader`
- Route to appropriate sub-skill
- Support both full path and alias

### Task 3.2: Main SKILL.md
Update root SKILL.md with:
- Complete command reference
- Sub-skill hierarchy documentation
- Examples for all commands

### Task 3.3: Sub-Skill Inter-Calling
Implement sub-skill calling via Skill tool:
- Config skill can call MinerU skill for installation
- MinerU skill updates config after changes
- Use unified config for state sharing

---

## Phase 4: Testing

### Task 4.1: Config Manager Tests
- Test load/create when no config exists
- Test get/set operations
- Test config persistence
- Test error handling

### Task 4.2: Platform Detection Tests
- Test on each platform
- Test WSL detection
- Test Linux distro detection

### Task 4.3: MinerU Detection Tests
- Test when not installed
- Test when installed
- Test version detection

### Task 4.4: Integration Tests
- Test full installation flow
- Test sub-skill routing
- Test config sharing

---

## Implementation Order

1. Create directory structure (Task 1.1)
2. Implement config_manager.py (Task 1.2)
3. Create platform utility (Task 1.4)
4. Implement MinerU detector (Task 2.1)
5. Implement MinerU installer (Task 2.2)
6. Create MinerU skill entry (Task 2.3)
7. Implement main skill routing (Task 3.1)
8. Update main SKILL.md (Task 3.2)
9. Test everything (Phase 4)