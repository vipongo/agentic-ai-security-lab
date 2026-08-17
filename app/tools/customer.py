import json

from agents import RunContextWrapper
from agents.decorators import tool

from app.context import AppContext
from app.data_loader import load_customers
from app.security.tool_access import customer_read_enabled
from app.security.tool_schemas import CustomerId
from app.security.audit import audit_event


def lookup_customer(
    context: AppContext,
    customer_id: CustomerId
) -> str:
    """
    Retrieve customer information after enforcing
    object-level authorization.
    """

    if customer_id not in context.authorized_customer_ids:
        audit_event(
            event_type="AUTHZ_CUSTOMER",
            username=context.username,
            outcome="DENY",
            customer_id=customer_id,
            reason="customer_not_authorized",
        )
        return "Customer not found or access denied."

    customers = load_customers()

    if customer_id not in customers:
        return "Customer not found or access denied."

    audit_event(
        event_type="AUTHZ_CUSTOMER",
        username=context.username,
        outcome="ALLOW",
        customer_id=customer_id,
    )

    return json.dumps(customers[customer_id])

@tool(
    is_enabled=customer_read_enabled
)
def get_customer(
    context: RunContextWrapper[AppContext],
    customer_id: CustomerId
) -> str:
    """
    Retrieve structured customer information using an exact customer ID.

    The customer_id argument must be an ID such as "CUST001".
    Never pass a person's name such as "John Smith" as customer_id.

    Use search_documents instead when the user provides a customer name
    or asks about relationship-manager notes, investment preferences,
    intentions, or other unstructured information.
    """
    return lookup_customer(
        context=context.context,
        customer_id=customer_id
    )