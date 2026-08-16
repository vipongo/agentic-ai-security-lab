import pytest

from app.data_loader import get_user_context
from app.tools.customer import lookup_customer


@pytest.mark.xfail(
    strict=True,
    reason="SEC-001: customer lookup does not enforce authorization"
)
def test_alice_cannot_access_bobs_customer():

    alice = get_user_context("alice")

    result = lookup_customer(
        context=alice,
        customer_id="CUST002"
    )

    assert result == "ACCESS DENIED"