from pathlib import Path

from agents import SQLiteSession


BASE_DIR = Path(__file__).resolve().parent.parent

SESSION_DB = (
    BASE_DIR
    / "data"
    / "sessions"
    / "agent_sessions.db"
)


def get_session(
    username: str
) -> SQLiteSession:
    """
    Return the conversation session used by the application.

    WARNING:
    This initial implementation intentionally uses one shared
    session ID to demonstrate cross-user memory leakage.
    """

    SESSION_DB.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # INTENTIONALLY VULNERABLE
    session_id = "default"

    return SQLiteSession(
        session_id=session_id,
        db_path=SESSION_DB
    )