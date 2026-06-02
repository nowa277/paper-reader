"""Q&A Session Logger for Paper Reader.

Persists Q&A sessions to JSON log files for later review.
Logs are stored in ~/.paper-reader/logs/qa/
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default log directory
DEFAULT_LOG_DIR = Path.home() / ".paper-reader" / "logs" / "qa"


class QALogger:
    """Logger for Q&A sessions."""

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or DEFAULT_LOG_DIR
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """Ensure log directory exists."""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self, session_id: str) -> Path:
        """Get log file path for a session."""
        # Sanitize session_id for filename
        safe_id = session_id.replace("/", "_").replace("\\", "_")
        return self.log_dir / f"session_{safe_id}.json"

    def create_session(self, paper_id: str, paper_title: str = "") -> str:
        """Create a new Q&A session.

        Args:
            paper_id: Unique paper identifier (e.g., arXiv ID, filename)
            paper_title: Optional paper title

        Returns:
            session_id: Unique session identifier
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{paper_id}_{timestamp}"

        session_data = {
            "session_id": session_id,
            "paper_id": paper_id,
            "paper_title": paper_title,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "exchanges": [],
        }

        session_file = self._get_session_file(session_id)
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Created Q&A session: {session_id}")
        return session_id

    def add_exchange(
        self,
        session_id: str,
        question: str,
        answer: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Add a Q&A exchange to a session.

        Args:
            session_id: Session identifier
            question: User question
            answer: Answer provided
            metadata: Optional metadata (e.g., mode, page_refs)

        Returns:
            True if successful, False otherwise
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            logger.error(f"Session not found: {session_id}")
            return False

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            exchange = {
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "answer": answer,
                "metadata": metadata or {},
            }

            session_data["exchanges"].append(exchange)
            session_data["updated_at"] = datetime.now().isoformat()

            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Added exchange to session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add exchange: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data dict or None if not found
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return None

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read session: {e}")
            return None

    def list_sessions(self, paper_id: Optional[str] = None) -> list[dict]:
        """List all sessions, optionally filtered by paper_id.

        Args:
            paper_id: Optional paper ID to filter by

        Returns:
            List of session summary dicts
        """
        self._ensure_log_dir()
        sessions = []

        for session_file in self.log_dir.glob("session_*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if paper_id and data.get("paper_id") != paper_id:
                    continue

                sessions.append({
                    "session_id": data["session_id"],
                    "paper_id": data.get("paper_id", ""),
                    "paper_title": data.get("paper_title", ""),
                    "created_at": data.get("created_at", ""),
                    "exchanges_count": len(data.get("exchanges", [])),
                })
            except Exception as e:
                logger.warning(f"Failed to read {session_file}: {e}")

        # Sort by created_at descending
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return False

        try:
            session_file.unlink()
            logger.info(f"Deleted session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False


# Module-level convenience functions
_logger: Optional[QALogger] = None


def get_logger() -> QALogger:
    """Get or create the global QALogger instance."""
    global _logger
    if _logger is None:
        _logger = QALogger()
    return _logger


def create_session(paper_id: str, paper_title: str = "") -> str:
    """Create a new Q&A session."""
    return get_logger().create_session(paper_id, paper_title)


def add_exchange(
    session_id: str,
    question: str,
    answer: str,
    metadata: Optional[dict] = None,
) -> bool:
    """Add a Q&A exchange to a session."""
    return get_logger().add_exchange(session_id, question, answer, metadata)


def get_session(session_id: str) -> Optional[dict]:
    """Get a session by ID."""
    return get_logger().get_session(session_id)


def list_sessions(paper_id: Optional[str] = None) -> list[dict]:
    """List all sessions."""
    return get_logger().list_sessions(paper_id)


def delete_session(session_id: str) -> bool:
    """Delete a session."""
    return get_logger().delete_session(session_id)
