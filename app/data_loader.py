import json
from pathlib import Path

from app.context import AppContext


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_users():
    with open(DATA_DIR / "users.json", "r", encoding="utf-8") as file:
        return json.load(file)


def load_customers():
    with open(DATA_DIR / "customers.json", "r", encoding="utf-8") as file:
        return json.load(file)


def get_user_context(username: str) -> AppContext:
    users = load_users()

    if username not in users:
        raise ValueError(f"Unknown user: {username}")

    user = users[username]

    return AppContext(
        username=username,
        user_id=user["user_id"],
        role=user["role"],
        authorized_customer_ids=user["authorized_customer_ids"],
    )