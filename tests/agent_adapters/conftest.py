# conftest.py for tests/agent_adapters
import sys
from pathlib import Path

# Ensure the paper-reader directory is in sys.path BEFORE any other imports
# This allows absolute imports like 'from agent_adapters.generator import Generator'
paper_reader_dir = Path(__file__).parent.parent.parent.absolute()
if str(paper_reader_dir) not in sys.path:
    sys.path.insert(0, str(paper_reader_dir))
