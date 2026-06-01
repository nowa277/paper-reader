import sys
from pathlib import Path

# Ensure the paper-reader directory is in sys.path for imports
paper_reader_path = Path(__file__).parent.parent
if str(paper_reader_path) not in sys.path:
    sys.path.insert(0, str(paper_reader_path))
