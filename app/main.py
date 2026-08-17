import argparse
import asyncio

from agents import Runner

from app.agent import banking_agent
from app.data_loader import get_user_context
from app.session_manager import get_session

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

        print()
        print("Assistant:", result.final_output)
        print()


if __name__ == "__main__":
    asyncio.run(main())