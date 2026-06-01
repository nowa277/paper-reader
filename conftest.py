# conftest.py - ensure paper-reader is in sys.path for pytest
import sys
from pathlib import Path

# Add paper-reader directory to path if not already there
paper_reader = Path(__file__).parent.absolute()
if str(paper_reader) not in sys.path:
    sys.path.insert(0, str(paper_reader))
