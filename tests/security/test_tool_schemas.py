import pytest

from pydantic import (
    TypeAdapter,
    ValidationError,
)

from app.security.tool_schemas import (
    CustomerId,
    DestinationAccount,
    DocumentSearchQuery,
    TransferAmountCHF,
)
from app.tools.customer import get_customer
from app.tools.retrieval import search_documents
from app.tools.transfer import create_transfer


customer_id_adapter = TypeAdapter(
    CustomerId
)

destination_account_adapter = TypeAdapter(
    DestinationAccount
)

transfer_amount_adapter = TypeAdapter(
    TransferAmountCHF
)

document_query_adapter = TypeAdapter(
    DocumentSearchQuery
)


# ---------------------------------------------------------
# Customer ID
# ---------------------------------------------------------

@pytest.mark.parametrize(
    "customer_id",
    [
        "CUST001",
        "CUST123",
        "CUST999",
    ],
)
def test_valid_customer_ids_are_accepted(
    customer_id,
):
    result = customer_id_adapter.validate_python(
        customer_id
    )

    assert result == customer_id


@pytest.mark.parametrize(
    "customer_id",
    [
        "CUST01",
        "CUST0001",
        "cust001",
        "CUSTABC",
        " CUST001",
        "CUST001 ",
        "",
    ],
)
def test_invalid_customer_ids_are_rejected(
    customer_id,
):
    with pytest.raises(
        ValidationError
    ):
        customer_id_adapter.validate_python(
            customer_id
        )


# ---------------------------------------------------------
# Destination account
# ---------------------------------------------------------

@pytest.mark.parametrize(
    "account",
    [
        "DEMO-ACCOUNT-001",
        "DEMO-ACCOUNT-999",
        "DEMO-ACCOUNT-123456",
    ],
)
def test_valid_destination_accounts_are_accepted(
    account,
):
    result = destination_account_adapter.validate_python(
        account
    )

    assert result == account


@pytest.mark.parametrize(
    "account",
    [
        "DEMO-ACCOUNT-12",
        "DEMO-ACCOUNT-1234567",
        "DEMO-ACCOUNT-ABC",
        "ACCOUNT-999",
        "CH9300000000000000000",
        "",
    ],
)
def test_invalid_destination_accounts_are_rejected(
    account,
):
    with pytest.raises(
        ValidationError
    ):
        destination_account_adapter.validate_python(
            account
        )


# ---------------------------------------------------------
# Transfer amount
# ---------------------------------------------------------

@pytest.mark.parametrize(
    "amount",
    [
        1,
        1000,
        50000,
        100000,
    ],
)
def test_valid_transfer_amounts_are_accepted(
    amount,
):
    result = transfer_amount_adapter.validate_python(
        amount
    )

    assert result == amount


@pytest.mark.parametrize(
    "amount",
    [
        0,
        -1,
        -50000,
        100001,
        1000000,
    ],
)
def test_invalid_transfer_amounts_are_rejected(
    amount,
):
    with pytest.raises(
        ValidationError
    ):
        transfer_amount_adapter.validate_python(
            amount
        )


# ---------------------------------------------------------
# RAG search query
# ---------------------------------------------------------

@pytest.mark.parametrize(
    "query",
    [
        "Q3",
        "CUST001 investment preferences",
        "a" * 500,
    ],
)
def test_valid_document_queries_are_accepted(
    query,
):
    result = document_query_adapter.validate_python(
        query
    )

    assert result == query


@pytest.mark.parametrize(
    "query",
    [
        "",
        "A",
        "a" * 501,
    ],
)
def test_invalid_document_queries_are_rejected(
    query,
):
    with pytest.raises(
        ValidationError
    ):
        document_query_adapter.validate_python(
            query
        )


# ---------------------------------------------------------
# Actual Agents SDK tool schemas
# ---------------------------------------------------------

def test_customer_tool_exposes_customer_id_schema():
    schema = (
        get_customer
        .params_json_schema[
            "properties"
        ][
            "customer_id"
        ]
    )

    assert (
        schema["pattern"]
        == r"^CUST\d{3}$"
    )

    assert schema["minLength"] == 7
    assert schema["maxLength"] == 7


def test_transfer_tool_exposes_validation_schema():
    properties = (
        create_transfer
        .params_json_schema[
            "properties"
        ]
    )

    assert (
        properties[
            "source_customer_id"
        ][
            "pattern"
        ]
        == r"^CUST\d{3}$"
    )

    assert (
        properties[
            "destination_account"
        ][
            "pattern"
        ]
        == r"^DEMO-ACCOUNT-\d{3,6}$"
    )

    assert (
        properties[
            "amount_chf"
        ][
            "minimum"
        ]
        == 1
    )

    assert (
        properties[
            "amount_chf"
        ][
            "maximum"
        ]
        == 100000
    )


def test_rag_tool_exposes_query_limits():
    query_schema = (
        search_documents
        .params_json_schema[
            "properties"
        ][
            "query"
        ]
    )

    assert query_schema["minLength"] == 2
    assert query_schema["maxLength"] == 500