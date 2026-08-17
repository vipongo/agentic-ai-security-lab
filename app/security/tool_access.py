from agents import AgentBase, RunContextWrapper

from app.context import AppContext


def customer_read_enabled(
    context: RunContextWrapper[AppContext],
    agent: AgentBase
) -> bool:
    enabled = (
        "customer:read"
        in context.context.permissions
    )


    return enabled


def document_read_enabled(
    context: RunContextWrapper[AppContext],
    agent: AgentBase
) -> bool:
    enabled = (
        "document:read"
        in context.context.permissions
    )


    return enabled 


def transfer_create_enabled(
    context: RunContextWrapper[AppContext],
    agent: AgentBase
) -> bool:
    enabled = (
        "transfer:create"
        in context.context.permissions
    )

    return enabled