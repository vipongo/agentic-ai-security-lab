from app.data_loader import get_user_context
from app.tools.retrieval import search_documents_logic

def test_alice_cannot_retrieve_bobs_documents():

    alice = get_user_context("alice")

    result = search_documents_logic(
        context=alice,
        query="CUST002"
    )

    result = result.lower()

    assert "cust002_notes.md" not in result
    assert "anna müller" not in result
    assert "250,000" not in result

def test_bob_can_retrieve_his_own_documents():

    bob = get_user_context("bob")

    result = search_documents_logic(
        context=bob,
        query="CUST002"
    )

    result = result.lower()

    assert "cust002_notes.md" in result
    assert "anna müller" in result