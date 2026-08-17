import json

import pytest

import app.tools.transfer as transfer_module
from app.data_loader import get_user_context


@pytest.mark.xfail(
    strict=True,
    reason=(
        "SEC-005: transfer tool does not enforce "
        "source-customer authorization"
    )
)
def test_alice_cannot_transfer_from_bobs_customer(
    tmp_path,
    monkeypatch
):
    """
    Security requirement:
    Alice must not be able to initiate a transfer using
    a customer outside her authorization scope.
    """

    test_file = tmp_path / "transfers.json"

    monkeypatch.setattr(
        transfer_module,
        "TRANSFERS_FILE",
        test_file
    )

    alice = get_user_context("alice")

    result = transfer_module.create_transfer_logic(
        context=alice,
        source_customer_id="CUST002",
        destination_account="CH9300000000000000000",
        amount_chf=50000
    )

    transfer = json.loads(result)

    assert transfer["status"] == "ACCESS_DENIED"

@pytest.mark.xfail(
    strict=True,
    reason=(
        "SEC-005: unauthorized transfer requests currently "
        "produce persistent side effects"
    )
)
def test_unauthorized_transfer_does_not_create_record(
    tmp_path,
    monkeypatch
):
    """
    Security requirement:
    a denied transfer must not create a transfer record.
    """

    test_file = tmp_path / "transfers.json"

    monkeypatch.setattr(
        transfer_module,
        "TRANSFERS_FILE",
        test_file
    )

    alice = get_user_context("alice")

    transfer_module.create_transfer_logic(
        context=alice,
        source_customer_id="CUST002",
        destination_account="CH9300000000000000000",
        amount_chf=50000
    )

    transfers = transfer_module.load_transfers()

    assert transfers == []

def test_transfer_record_contains_requesting_user(
    tmp_path,
    monkeypatch
):
    """
    Functional requirement:
    simulated transfers should record who requested them.
    """

    test_file = tmp_path / "transfers.json"

    monkeypatch.setattr(
        transfer_module,
        "TRANSFERS_FILE",
        test_file
    )

    alice = get_user_context("alice")

    result = transfer_module.create_transfer_logic(
        context=alice,
        source_customer_id="CUST001",
        destination_account="CH9300000000000000000",
        amount_chf=1000
    )

    transfer = json.loads(result)

    assert transfer["requested_by"] == "alice"