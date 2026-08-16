import pytest

from app.data_loader import get_user_context
from app.tools.retrieval import search_documents_logic


@pytest.mark.xfail(
    strict=True,
    reason="SEC-002: RAG retrieval does not enforce document ownership"
)
def test_alice_cannot_retrieve_bobs_documents():

    alice = get_user_context("alice")

    result = search_documents_logic(
        context=alice,
        query="CUST002"
    )

    assert "owner: bob" not in result.lower()