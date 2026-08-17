import argparse
import asyncio

from agents import Runner

from app.agent import banking_agent
from app.data_loader import get_user_context
from app.session_manager import get_session

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
        "yes"
    }

async def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--user",
        required=True,
        choices=["alice", "bob"]
    )

    args = parser.parse_args()

    user_context = get_user_context(args.user)
    session = get_session(
        user_context.username
    )

    print(f"Logged in as: {user_context.username}")
    print("Type 'exit' to quit.")
    print()

    while True:

        message = input("You: ")

        if message.lower() == "exit":
            break

        result = await Runner.run(
            banking_agent,
            message,
            context=user_context,
            session=session
        )

        while result.interruptions:

            state = result.to_state()

            for interruption in result.interruptions:

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

                arguments = getattr(
                    interruption,
                    "arguments",
                    None
                )

                approved = ask_for_approval(
                    tool_name=tool_name,
                    arguments=arguments
                )

                if approved:

                    print(
                        "[APPROVAL] APPROVED "
                        f"tool={tool_name}"
                    )

                    state.approve(
                        interruption
                    )

                else:

                    print(
                        "[APPROVAL] REJECTED "
                        f"tool={tool_name}"
                    )

                    state.reject(
                        interruption,
                        rejection_message=(
                            "The requested high-impact action "
                            "was rejected by the human approver."
                        )
                    )

            result = await Runner.run(
                banking_agent,
                state,
                session=session
            )


        print()
        print(
            "Assistant:",
            result.final_output
        )


if __name__ == "__main__":
    asyncio.run(main())