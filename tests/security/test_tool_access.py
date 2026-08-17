import asyncio
from types import SimpleNamespace

import pytest

from agents import RunContextWrapper

from app.agent import banking_agent
from app.context import AppContext
from app.security.tool_access import (
    customer_read_enabled,
    document_read_enabled,
    transfer_create_enabled,
)
from app.tools.customer import get_customer
from app.tools.retrieval import search_documents
from app.tools.transfer import create_transfer


def make_context(
    permissions: list[str]
) -> AppContext:
    return AppContext(
        username="alice",
        user_id="USR001",
        role="advisor",
        authorized_customer_ids=["CUST001"],
        permissions=permissions,
    )


def make_wrapper(
    permissions: list[str]
):
    return SimpleNamespace(
        context=make_context(permissions)
    )


@pytest.mark.parametrize(
    ("permission", "callback"),
    [
        (
            "customer:read",
            customer_read_enabled,
        ),
        (
            "document:read",
            document_read_enabled,
        ),
        (
            "transfer:create",
            transfer_create_enabled,
        ),
    ],
)
def test_tool_enabled_with_required_permission(
    permission,
    callback,
):
    context = make_wrapper([permission])

    assert callback(
        context,
        agent=None,
    ) is True


@pytest.mark.parametrize(
    "callback",
    [
        customer_read_enabled,
        document_read_enabled,
        transfer_create_enabled,
    ],
)
def test_tool_disabled_without_required_permission(
    callback,
):
    context = make_wrapper([])

    assert callback(
        context,
        agent=None,
    ) is False


def test_tool_permissions_enforce_least_privilege():
    """
    A user with document:read only must not automatically
    gain customer or transfer capabilities.
    """

    context = make_wrapper([
        "document:read",
    ])

    assert (
        customer_read_enabled(
            context,
            agent=None,
        )
        is False
    )

    assert (
        document_read_enabled(
            context,
            agent=None,
        )
        is True
    )

    assert (
        transfer_create_enabled(
            context,
            agent=None,
        )
        is False
    )


def test_tools_are_wired_to_correct_access_controls():
    """
    Regression test:

    The decorated tools must continue using the expected
    runtime permission callbacks.
    """

    assert (
        get_customer.is_enabled
        is customer_read_enabled
    )

    assert (
        search_documents.is_enabled
        is document_read_enabled
    )

    assert (
        create_transfer.is_enabled
        is transfer_create_enabled
    )


def test_agent_hides_tools_without_permissions():
    """
    Integration test:

    Disabled tools must not appear in the tool set exposed
    to the model.
    """

    context = make_context([
        "document:read",
    ])

    wrapper = RunContextWrapper(
        context
    )

    tools = asyncio.run(
        banking_agent.get_all_tools(
            wrapper
        )
    )

    tool_names = {
        tool.name
        for tool in tools
    }

    assert "search_documents" in tool_names

    assert "get_customer" not in tool_names
    assert "create_transfer" not in tool_names