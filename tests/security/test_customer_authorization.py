import json

from app.data_loader import get_user_context
from app.tools.customer import lookup_customer


def test_alice_can_access_her_customer():

    alice = get_user_context("alice")

    result = lookup_customer(
        context=alice,
        customer_id="CUST001"
    )

    customer = json.loads(result)

    assert customer["customer_id"] == "CUST001"


def test_alice_cannot_access_bobs_customer():

    alice = get_user_context("alice")

    result = lookup_customer(
        context=alice,
        customer_id="CUST002"
    )

    assert result == "Customer not found or access denied."


def test_bob_can_access_his_customer():

    bob = get_user_context("bob")

    result = lookup_customer(
        context=bob,
        customer_id="CUST002"
    )

    customer = json.loads(result)

    assert customer["customer_id"] == "CUST002"


def test_bob_cannot_access_alices_customer():

    bob = get_user_context("bob")

    result = lookup_customer(
        context=bob,
        customer_id="CUST001"
    )

    assert result == "Customer not found or access denied."