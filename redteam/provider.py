import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


from agents import Runner, SQLiteSession
from app.agent import banking_agent
from app.data_loader import get_user_context

from app.security.audit import audit_event

from app.security.prompt_security import (
    scan_user_prompt,
    scan_agent_output,
    should_block_prompt,
)

from app.security.request_policy import (
    evaluate_request,
    policy_response,
)

SESSION_DB = (
    PROJECT_ROOT
    / "data"
    / "promptfoo_sessions"
    / "sessions.db"
)


async def call_api(
    prompt: str,
    options: dict,
    context: dict
) -> dict:
    """
    Promptfoo target adapter for the hardened banking agent.

    Important:
    - Uses the real banking agent
    - Uses the real authorization controls
    - Uses the real prompt/output security controls
    - Automatically rejects HITL actions during automated testing
    - Does NOT enforce the general chat rate limit, because that
      would prevent the red-team scan from exercising the agent
    """

    config = options.get(
        "config",
        {}
    )

    username = config.get(
        "user",
        "alice"
    )

    user_context = get_user_context(
        username
    )

    # Each Promptfoo test receives an isolated session.
    #
    # Multi-turn attacks using the same test case can keep
    # conversation state without contaminating unrelated tests.
    test_case_id = (
        context.get("testCaseId")
        or str(uuid4())
    )

    user_context.request_id = str(
    test_case_id
    )

    SESSION_DB.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    session = SQLiteSession(
        session_id=(
            f"promptfoo:"
            f"{username}:"
            f"{test_case_id}"
        ),
        db_path=SESSION_DB
    )

    # ---------------------------------
    # INPUT SECURITY
    # ---------------------------------

    policy_decision = evaluate_request(
        user_context,
        prompt,
    )

    if not policy_decision.allowed:

        audit_event(
            event_type="REQUEST_POLICY",
            username=username,
            outcome="DENY",
            reason=policy_decision.reason,
            source="promptfoo",
            test_case_id=test_case_id,
        )

        return {
            "output": policy_response(
                policy_decision
            )
        }


    prompt_scan = scan_user_prompt(
        prompt
    )

    if prompt_scan.suspicious:

        audit_event(
            event_type="PROMPT_SECURITY",
            username=username,
            outcome="DETECTED",
            rule=prompt_scan.matched_rule,
            source="promptfoo",
            prompt_length=len(prompt),
        )

        if should_block_prompt(
            prompt_scan
        ):

            audit_event(
                event_type="PROMPT_SECURITY",
                username=username,
                outcome="BLOCK",
                rule=prompt_scan.matched_rule,
                source="promptfoo",
            )

            return {
                "output": (
                    "I can't process that request."
                )
            }

    # ---------------------------------
    # RUN REAL AGENT
    # ---------------------------------

    result = await Runner.run(
        banking_agent,
        prompt,
        context=user_context,
        session=session
    )

    # ---------------------------------
    # HUMAN APPROVAL
    #
    # Automated security testing must
    # never approve sensitive actions.
    # ---------------------------------

    while result.interruptions:

        state = result.to_state()

        for interruption in (
            result.interruptions
        ):

            tool_name = (
                getattr(
                    interruption,
                    "tool_name",
                    None
                )
                or getattr(
                    interruption,
                    "name",
                    "unknown_tool"
                )
            )

            audit_event(
                event_type="HUMAN_APPROVAL",
                username=username,
                outcome="REJECTED",
                tool=tool_name,
                source="promptfoo",
                reason="automated_redteam",
            )

            state.reject(
                interruption,
                rejection_message=(
                    "High-impact actions are "
                    "automatically rejected during "
                    "automated security testing."
                )
            )

        result = await Runner.run(
            banking_agent,
            state,
            session=session
        )

    # ---------------------------------
    # OUTPUT SECURITY
    # ---------------------------------

    final_output = str(
        result.final_output or ""
    )

    output_scan = scan_agent_output(
        final_output
    )

    if not output_scan.safe:

        audit_event(
            event_type="OUTPUT_SECURITY",
            username=username,
            outcome="BLOCK",
            rule=output_scan.matched_rule,
            source="promptfoo",
        )

        final_output = (
            "I can't provide internal "
            "application instructions "
            "or configuration."
        )

    return {
        "output": final_output
    }