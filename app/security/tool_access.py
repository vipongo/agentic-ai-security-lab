from agents import AgentBase, RunContextWrapper

from app.context import AppContext

from app.security.audit import audit_event


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
    audit_event(
        event_type="TOOL_ACCESS",
        username=context.context.username,
        outcome="ALLOW" if enabled else "DENY",
        tool="create_transfer",
        reason=(
            None
            if enabled
            else "missing_transfer_permission"
        ),
    )

    return enabled