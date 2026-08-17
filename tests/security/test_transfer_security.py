import json

import app.tools.transfer as transfer_module

from app.context import AppContext
from app.main import ask_for_approval


DESTINATION_ACCOUNT = "CH9300000000000000000"


def create_alice_context(
    permissions=None
) -> AppContext:
    """
    Create an isolated Alice context for deterministic tests.
    """

    if permissions is None:
        permissions = ["transfer:create"]

    return AppContext(
        username="alice",
        user_id="USR001",
        role="advisor",
        authorized_customer_ids=["CUST001"],
        permissions=permissions
    )


def configure_test_storage(
    tmp_path,
    monkeypatch
):
    """
    Redirect transfer persistence to temporary pytest storage.
    """

    test_file = tmp_path / "transfers.json"

    monkeypatch.setattr(
        transfer_module,
        "TRANSFERS_FILE",
        test_file
    )

    return test_file


def test_authorized_transfer_logic_executes(
    tmp_path,
    monkeypatch
):
    """
    Post-authorization execution requirement:

    Alice has transfer:create permission and owns CUST001,
    therefore the underlying transfer logic may execute.

    HITL is enforced by the decorated tool before this logic
    is invoked through the agent.
    """

    configure_test_storage(
        tmp_path,
        monkeypatch
    )

    alice = create_alice_context()

    result = transfer_module.create_transfer_logic(
        context=alice,
        source_customer_id="CUST001",
        destination_account=DESTINATION_ACCOUNT,
        amount_chf=1000
    )

    transfer = json.loads(result)

    assert transfer["source_customer_id"] == "CUST001"
    assert transfer["requested_by"] == "alice"
    assert transfer["amount_chf"] == 1000
    assert transfer["status"] == "SIMULATED_EXECUTED"

    transfers = transfer_module.load_transfers()

    assert len(transfers) == 1
    assert transfers[0]["transfer_id"] == transfer["transfer_id"]


def test_alice_cannot_transfer_from_bobs_customer(
    tmp_path,
    monkeypatch
):
    """
    SEC-008 regression test.

    Alice is authorized for CUST001 only.
    A transfer using CUST002 must be denied.
    """

    configure_test_storage(
        tmp_path,
        monkeypatch
    )

    alice = create_alice_context()

    result = transfer_module.create_transfer_logic(
        context=alice,
        source_customer_id="CUST002",
        destination_account=DESTINATION_ACCOUNT,
        amount_chf=50000
    )

    assert result == "Transfer not permitted."

    transfers = transfer_module.load_transfers()

    assert transfers == []


def test_user_without_transfer_permission_is_denied(
    tmp_path,
    monkeypatch
):
    """
    Action-authorization requirement.

    Possession of the customer relationship alone must not
    authorize the transfer action.
    """

    configure_test_storage(
        tmp_path,
        monkeypatch
    )

    alice = create_alice_context(
        permissions=[]
    )

    result = transfer_module.create_transfer_logic(
        context=alice,
        source_customer_id="CUST001",
        destination_account=DESTINATION_ACCOUNT,
        amount_chf=1000
    )

    assert result == "Transfer not permitted."

    transfers = transfer_module.load_transfers()

    assert transfers == []


def test_transfer_tool_requires_human_approval():
    """
    SEC-007 regression test.

    The agent-facing transfer tool must be configured as a
    human-approval-gated operation.
    """

    assert (
        transfer_module.create_transfer.needs_approval
        is True
    )


def test_human_can_reject_transfer(
    monkeypatch
):
    """
    HITL rejection decision must return False.
    """

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "n"
    )

    approved = ask_for_approval(
        tool_name="create_transfer",
        arguments=(
            '{"source_customer_id":"CUST001",'
            '"destination_account":'
            '"CH9300000000000000000",'
            '"amount_chf":1000}'
        )
    )

    assert approved is False


def test_human_can_approve_transfer(
    monkeypatch
):
    """
    HITL approval decision must return True.
    """

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "yes"
    )

    approved = ask_for_approval(
        tool_name="create_transfer",
        arguments=(
            '{"source_customer_id":"CUST001",'
            '"destination_account":'
            '"CH9300000000000000000",'
            '"amount_chf":1000}'
        )
    )

    assert approved is True