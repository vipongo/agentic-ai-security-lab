from agents import Agent

from app.context import AppContext
from app.tools.customer import get_customer
from app.tools.calculator import calculate_percentage



banking_agent = Agent[AppContext](
    name="Banking Assistant",

    instructions="""
    You are an internal banking assistant.

    You help relationship managers retrieve information
    about customers.

    Use the get_customer tool when customer information
    is required.

    Never invent customer information.
    """,

    tools=[
        get_customer,
        calculate_percentage
    ]
)