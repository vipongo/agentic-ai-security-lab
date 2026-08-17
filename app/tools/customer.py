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
    Retrieve customer information after enforcing
    object-level authorization.
    """

    if customer_id not in context.authorized_customer_ids:
        print(
            f"[AUTHZ] DENY "
            f"user={context.username} "
            f"customer_id={customer_id}"
        )
        return "Customer not found or access denied."

    customers = load_customers()

    if customer_id not in customers:
        return "Customer not found or access denied."

    print(
        f"[AUTHZ] ALLOW "
        f"user={context.username} "
        f"customer_id={customer_id}"
    )

    return json.dumps(customers[customer_id])

@tool
def get_customer(
    context: RunContextWrapper[AppContext],
    customer_id: str
) -> str:
    """
    Retrieve structured customer information using an exact customer ID.

    The customer_id argument must be an ID such as "CUST001".
    Never pass a person's name such as "John Smith" as customer_id.

    Use search_documents instead when the user provides a customer name
    or asks about relationship-manager notes, investment preferences,
    intentions, or other unstructured information.
    """
    print(
        f"[TOOL] get_customer called by "
        f"user={context.context.username} "
        f"customer_id={customer_id}"
    )
    return lookup_customer(
        context=context.context,
        customer_id=customer_id
    )