"""Tests for Q&A Logger."""

import tempfile
from pathlib import Path

from skills.analyze.qa_logger import QALogger


def test_create_session():
    """Test session creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = QALogger(log_dir=Path(tmpdir))

        session_id = logger.create_session("arxiv:2401.12345", "Test Paper")
        assert session_id.startswith("arxiv:2401.12345_")

        session = logger.get_session(session_id)
        assert session is not None
        assert session["paper_id"] == "arxiv:2401.12345"
        assert session["paper_title"] == "Test Paper"
        assert session["exchanges"] == []


def test_add_exchange():
    """Test adding Q&A exchange."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = QALogger(log_dir=Path(tmpdir))

        session_id = logger.create_session("test_paper")
        result = logger.add_exchange(
            session_id,
            "What is this paper about?",
            "It describes a new method for...",
            {"mode": "qa"},
        )
        assert result is True

        session = logger.get_session(session_id)
        assert len(session["exchanges"]) == 1
        assert session["exchanges"][0]["question"] == "What is this paper about?"
        assert session["exchanges"][0]["metadata"]["mode"] == "qa"


def test_list_sessions():
    """Test listing sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = QALogger(log_dir=Path(tmpdir))

        s1 = logger.create_session("paper_a")
        s2 = logger.create_session("paper_b")

        sessions = logger.list_sessions()
        assert len(sessions) == 2

        sessions_a = logger.list_sessions(paper_id="paper_a")
        assert len(sessions_a) == 1
        assert sessions_a[0]["paper_id"] == "paper_a"


def test_delete_session():
    """Test session deletion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = QALogger(log_dir=Path(tmpdir))

        session_id = logger.create_session("test_paper")
        assert logger.get_session(session_id) is not None

        result = logger.delete_session(session_id)
        assert result is True
        assert logger.get_session(session_id) is None


def test_module_level_functions():
    """Test module-level convenience functions."""
    import importlib
    with tempfile.TemporaryDirectory() as tmpdir:
        import skills.analyze.qa_logger as qa_logger

        # Override log dir for testing
        qa_logger._logger = QALogger(log_dir=Path(tmpdir))

        session_id = qa_logger.create_session("test_paper")
        assert session_id is not None

        qa_logger.add_exchange(session_id, "Q", "A")
        session = qa_logger.get_session(session_id)
        assert len(session["exchanges"]) == 1

        sessions = qa_logger.list_sessions()
        assert len(sessions) == 1
