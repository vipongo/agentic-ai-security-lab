import json

from agents import RunContextWrapper
from agents.decorators import tool

from app.context import AppContext
from app.data_loader import load_customers


def lookup_customer(
    context: AppContext,
    customer_id: str
) -> str:
    """
    Core customer lookup logic.

    Intentionally vulnerable baseline:
    authorization is not enforced yet.
    """

    customers = load_customers()

    if customer_id not in customers:
        return "Customer not found."

    return json.dumps(customers[customer_id])


@tool
def get_customer(
    context: RunContextWrapper[AppContext],
    customer_id: str
) -> str:
    """
    Retrieve information about a customer by customer ID.
    """

    return lookup_customer(
        context=context.context,
        customer_id=customer_id
    )