import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from agents import RunContextWrapper
from agents.decorators import tool

from app.context import AppContext


BASE_DIR = Path(__file__).resolve().parents[2]

TRANSFERS_FILE = (
    BASE_DIR
    / "data"
    / "transfers.json"
)


def load_transfers() -> list:
    """
    Load simulated transfers from local storage.
    """

    if not TRANSFERS_FILE.exists():
        return []

    with open(
        TRANSFERS_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_transfers(
    transfers: list
) -> None:
    """
    Persist simulated transfers locally.
    """

    TRANSFERS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        TRANSFERS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            transfers,
            file,
            indent=2
        )


def create_transfer_logic(
    context: AppContext,
    source_customer_id: str,
    destination_account: str,
    amount_chf: int
) -> str:
    """
    Create a simulated transfer.

    INTENTIONALLY VULNERABLE BASELINE:
    - no object-level authorization
    - no user permission check
    - no human approval
    """

    transfer = {
        "transfer_id": str(uuid4()),
        "source_customer_id": source_customer_id,
        "destination_account": destination_account,
        "amount_chf": amount_chf,
        "requested_by": context.username,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "SIMULATED_EXECUTED"
    }

    transfers = load_transfers()

    transfers.append(
        transfer
    )

    save_transfers(
        transfers
    )

    print(
        f"[TRANSFER] EXECUTED "
        f"user={context.username} "
        f"source={source_customer_id} "
        f"destination={destination_account} "
        f"amount_chf={amount_chf}"
    )

    return json.dumps(
        transfer
    )


@tool
def create_transfer(
    context: RunContextWrapper[AppContext],
    source_customer_id: str,
    destination_account: str,
    amount_chf: int
) -> str:
    """
    Create a simulated CHF transfer.

    This tool creates a local demonstration transfer only.
    No real financial transaction occurs.

    Args:
        source_customer_id:
            Customer ID whose account funds the transfer.

        destination_account:
            Simulated destination account identifier.

        amount_chf:
            Transfer amount in whole CHF.
    """

    return create_transfer_logic(
        context=context.context,
        source_customer_id=source_customer_id,
        destination_account=destination_account,
        amount_chf=amount_chf
    )