import asyncio

import pytest

import app.session_manager as session_manager


@pytest.mark.xfail(
    strict=True,
    reason="SEC-004: Alice and Bob currently share the same session ID"
)
def test_alice_and_bob_have_separate_session_ids(
    tmp_path,
    monkeypatch
):
    """
    Security requirement:
    different authenticated users must not share a session ID.
    """

    # Use a temporary database so the test does not modify
    # the application's real conversation history.
    test_db = tmp_path / "agent_sessions.db"

    monkeypatch.setattr(
        session_manager,
        "SESSION_DB",
        test_db
    )

    alice_session = session_manager.get_session("alice")
    bob_session = session_manager.get_session("bob")

    assert alice_session.session_id != bob_session.session_id

@pytest.mark.xfail(
    strict=True,
    reason="Bob can read items stored in Alice's shared session"
)
def test_bob_cannot_read_alices_session_history(
    tmp_path,
    monkeypatch
):
    """
    Security requirement:
    conversation history belonging to Alice must not be visible
    through Bob's session.
    """

    test_db = tmp_path / "agent_sessions.db"

    monkeypatch.setattr(
        session_manager,
        "SESSION_DB",
        test_db
    )

    alice_session = session_manager.get_session("alice")
    bob_session = session_manager.get_session("bob")

    confidential_marker = (
        "CONFIDENTIAL_ALICE_SESSION_MARKER"
    )

    async def run_test():

        await alice_session.add_items([
            {
                "role": "user",
                "content": confidential_marker
            }
        ])

        bob_history = await bob_session.get_items()

        assert confidential_marker not in str(bob_history)

    asyncio.run(run_test())

def test_alice_can_read_her_own_session_history(
    tmp_path,
    monkeypatch
):
    """
    Functional requirement:
    a user's own session should preserve their conversation history.
    """

    test_db = tmp_path / "agent_sessions.db"

    monkeypatch.setattr(
        session_manager,
        "SESSION_DB",
        test_db
    )

    alice_session = session_manager.get_session("alice")

    marker = "ALICE_SESSION_MEMORY_TEST"

    async def run_test():

        await alice_session.add_items([
            {
                "role": "user",
                "content": marker
            }
        ])

        alice_history = await alice_session.get_items()

        assert marker in str(alice_history)

    asyncio.run(run_test())