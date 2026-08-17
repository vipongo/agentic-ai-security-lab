import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from agents import RunContextWrapper
from agents.decorators import tool

from app.context import AppContext
from app.security.tool_access import transfer_create_enabled

from app.security.tool_schemas import (
    CustomerId,
    DestinationAccount,
    TransferAmountCHF,
)


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
    Create a simulated transfer after enforcing
    deterministic authorization.
    """

    if "transfer:create" not in context.permissions:

        print(
            f"[AUTHZ] DENY transfer permission "
            f"user={context.username}"
        )

        return "Transfer not permitted."

    if source_customer_id not in context.authorized_customer_ids:

        print(
            f"[AUTHZ] DENY transfer source "
            f"user={context.username} "
            f"customer_id={source_customer_id}"
        )

        return "Transfer not permitted."

    if amount_chf <= 0:

        return "Invalid transfer amount."

    if not re.fullmatch(
        r"DEMO-ACCOUNT-\d{3,6}",
        destination_account
    ):

        print(
            f"[VALIDATION] DENY destination "
            f"user={context.username}"
        )

        return "Invalid transfer request."

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


@tool(
    is_enabled=transfer_create_enabled,
    needs_approval=True
)
def create_transfer(
    context: RunContextWrapper[AppContext],
    source_customer_id: CustomerId,
    destination_account: DestinationAccount,
    amount_chf: TransferAmountCHF
) -> str:
    """
    Create a simulated CHF transfer.

    This tool creates a local demonstration transfer only.
    No real financial transaction occurs.

    Human approval is required before execution.

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