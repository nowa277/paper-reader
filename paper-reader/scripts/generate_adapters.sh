#!/bin/bash
# Generate adapter files for all supported AI coding agents

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/output}"

echo "Generating agent adapter files..."
echo "Output directory: $OUTPUT_DIR"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run Python generator
cd "$PROJECT_DIR"
python3 -c "
import sys
sys.path.insert(0, '.')
from agent_adapters import Generator

# Read skill source
with open('paper-reader/SKILL.md', 'r') as f:
    skill_source = f.read()

# Default config
config = {
    'mineru_path': '~/.hermes/hermes-agent/venv/bin/mineru',
    'work_base': '/tmp/paper-reader',
    'archive_base': '~/obsidian/papers'
}

# Generate
gen = Generator('paper-reader/agent_adapters/templates', '$OUTPUT_DIR')
result = gen.generate_all(skill_source, config)

print(f'Success: {result.success}')
print(f'Output files: {result.output_files}')
if result.errors:
    print(f'Errors: {result.errors}')
    sys.exit(1)
"

echo "Done! Files generated in $OUTPUT_DIR"
