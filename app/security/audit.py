import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


BASE_DIR = Path(__file__).resolve().parents[2]

AUDIT_LOG = (
    BASE_DIR
    / "data"
    / "logs"
    / "security-audit.jsonl"
)


def audit_event(
    event_type: str,
    username: str,
    outcome: str,
    **details
) -> None:
    """
    Write one structured security event as JSON Lines.

    Do not pass secrets, full prompts, customer records,
    or other sensitive content in details.
    """

    AUDIT_LOG.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    event = {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "event_type": event_type,
        "username": username,
        "outcome": outcome,
        "details": details,
    }

    with open(
        AUDIT_LOG,
        "a",
        encoding="utf-8"
    ) as file:
        file.write(
            json.dumps(event)
            + "\n"
        )