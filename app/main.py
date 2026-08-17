import argparse
import asyncio

from agents import Runner

from app.agent import banking_agent
from app.data_loader import get_user_context
from app.session_manager import get_session
from app.security.audit import audit_event
from app.security.prompt_security import (
    scan_agent_output,
    scan_user_prompt,
    should_block_prompt,
)
from app.security.rate_limit import agent_rate_limiter


def ask_for_approval(
    tool_name: str,
    arguments: str | None
) -> bool:
    """
    Ask the local human operator whether a sensitive
    tool invocation should proceed.
    """

    print()
    print("=== HUMAN APPROVAL REQUIRED ===")
    print(f"Tool: {tool_name}")
    print(f"Arguments: {arguments}")
    print()

    decision = input(
        "Approve this action? [y/N]: "
    ).strip().lower()

    return decision in {
        "y",
        "yes",
    }


async def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--user",
        required=True,
        choices=["alice", "bob"],
    )

    args = parser.parse_args()

    user_context = get_user_context(
        args.user
    )

    session = get_session(
        user_context.username
    )

    print(
        f"Logged in as: "
        f"{user_context.username}"
    )

    print("Type 'exit' to quit.")
    print()

    while True:

        message = input("You: ")

        # Exit before applying rate limiting.
        if message.lower() == "exit":
            break

        # --------------------------------------------------
        # RATE LIMITING
        # --------------------------------------------------

        rate_result = (
            agent_rate_limiter.check(
                user_context.username
            )
        )

        if not rate_result.allowed:

            audit_event(
                event_type="RATE_LIMIT",
                username=user_context.username,
                outcome="DENY",
                retry_after_seconds=(
                    rate_result.retry_after_seconds
                ),
            )

            print()
            print(
                "Assistant:",
                (
                    "Too many requests. "
                    "Try again in approximately "
                    f"{rate_result.retry_after_seconds} "
                    "seconds."
                ),
            )
            print()

            continue

        audit_event(
            event_type="RATE_LIMIT",
            username=user_context.username,
            outcome="ALLOW",
            remaining=rate_result.remaining,
        )

        # --------------------------------------------------
        # INPUT / PROMPT SECURITY
        # --------------------------------------------------

        prompt_scan = scan_user_prompt(
            message
        )

        if prompt_scan.suspicious:

            audit_event(
                event_type="PROMPT_SECURITY",
                username=user_context.username,
                outcome="DETECTED",
                rule=prompt_scan.matched_rule,
                prompt_length=len(message),
            )

            if should_block_prompt(
                prompt_scan
            ):

                audit_event(
                    event_type="PROMPT_SECURITY",
                    username=user_context.username,
                    outcome="BLOCK",
                    rule=prompt_scan.matched_rule,
                )

                print()
                print(
                    "Assistant:",
                    "I can't process that request.",
                )
                print()

                continue

        # --------------------------------------------------
        # AGENT EXECUTION
        # --------------------------------------------------

        result = await Runner.run(
            banking_agent,
            message,
            context=user_context,
            session=session,
        )

        # --------------------------------------------------
        # HUMAN-IN-THE-LOOP APPROVAL
        # --------------------------------------------------

        while result.interruptions:

            state = result.to_state()

            for interruption in result.interruptions:

                tool_name = (
                    getattr(
                        interruption,
                        "tool_name",
                        None,
                    )
                    or getattr(
                        interruption,
                        "name",
                        "unknown_tool",
                    )
                )

                arguments = getattr(
                    interruption,
                    "arguments",
                    None,
                )

                approved = ask_for_approval(
                    tool_name=tool_name,
                    arguments=arguments,
                )

                if approved:

                    audit_event(
                        event_type="HUMAN_APPROVAL",
                        username=user_context.username,
                        outcome="APPROVED",
                        tool=tool_name,
                    )

                    print(
                        f"[APPROVAL] APPROVED "
                        f"tool={tool_name}"
                    )

                    state.approve(
                        interruption
                    )

                else:

                    audit_event(
                        event_type="HUMAN_APPROVAL",
                        username=user_context.username,
                        outcome="REJECTED",
                        tool=tool_name,
                    )

                    print(
                        f"[APPROVAL] REJECTED "
                        f"tool={tool_name}"
                    )

                    state.reject(
                        interruption,
                        rejection_message=(
                            "The requested high-impact "
                            "action was rejected by the "
                            "human approver."
                        ),
                    )

            result = await Runner.run(
                banking_agent,
                state,
                session=session,
            )

        # --------------------------------------------------
        # OUTPUT SECURITY
        # --------------------------------------------------

        final_output = str(
            result.final_output
        )

        output_scan = scan_agent_output(
            final_output
        )

        if not output_scan.safe:

            audit_event(
                event_type="OUTPUT_SECURITY",
                username=user_context.username,
                outcome="BLOCK",
                rule=output_scan.matched_rule,
            )


            final_output = (
                "I can't provide internal application "
                "instructions or configuration."
            )

        # --------------------------------------------------
        # USER OUTPUT
        # --------------------------------------------------

        print()
        print(
            "Assistant:",
            final_output,
        )
        print()


if __name__ == "__main__":
    asyncio.run(main())