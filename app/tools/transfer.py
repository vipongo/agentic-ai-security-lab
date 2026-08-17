import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from agents import RunContextWrapper
from agents.decorators import tool

from app.context import AppContext
from app.security.tool_access import transfer_create_enabled
from app.security.audit import audit_event
from app.security.rate_limit import transfer_rate_limiter

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

        audit_event(
            event_type="AUTHZ_TRANSFER",
            username=context.username,
            outcome="DENY",
            reason="missing_transfer_permission",
        )

        return "Transfer not permitted."

    if source_customer_id not in context.authorized_customer_ids:

        audit_event(
            event_type="AUTHZ_TRANSFER",
            username=context.username,
            outcome="DENY",
            source_customer_id=source_customer_id,
            reason="customer_not_authorized",
        )

        return "Transfer not permitted."

    if amount_chf <= 0:

        return "Invalid transfer amount."

    if not re.fullmatch(
        r"DEMO-ACCOUNT-\d{3,6}",
        destination_account
    ):

        audit_event(
            event_type="AUTHZ_TRANSFER",
            username=context.username,
            outcome="DENY",
            source_customer_id=source_customer_id,
            reason="Wrong destination account format",
        )
        return "Invalid transfer request."

    """
    Rate limiting is enforced here to prevent abuse of the transfer tool.
    """

    rate_result = (
        transfer_rate_limiter.check(
            context.username
        )
    )

    if not rate_result.allowed:

        audit_event(
            event_type="TRANSFER_RATE_LIMIT",
            username=context.username,
            outcome="DENY",
            retry_after_seconds=(
                rate_result.retry_after_seconds
            ),
        )

        return (
            "Transfer request temporarily "
            "rate limited."
        )

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

    audit_event(
        event_type="TRANSFER_EXECUTION",
        username=context.username,
        outcome="SUCCESS",
        source_customer_id=source_customer_id,
        amount_chf=amount_chf,
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