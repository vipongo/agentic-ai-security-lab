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
    Return an isolated conversation session for the
    authenticated application user.
    """

    SESSION_DB.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # SECURITY CONTROL:
    # Bind persistent conversation history to the
    # authenticated application identity.
    session_id = (
        f"user:{username}:default"
    )

    print(
        f"[SESSION] user={username} "
        f"session_id={session_id}"
    )

    return SQLiteSession(
        session_id=session_id,
        db_path=SESSION_DB
    )