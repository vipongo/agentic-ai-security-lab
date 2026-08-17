from dataclasses import dataclass


@dataclass
class AppContext:
    username: str
    user_id: str
    role: str
    authorized_customer_ids: list[str]
    permissions: list[str]