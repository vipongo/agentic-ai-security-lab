from agents import Agent

from app.context import AppContext
from app.tools.customer import get_customer
from app.tools.calculator import calculate_percentage
from app.tools.retrieval import search_documents



banking_agent = Agent[AppContext](
    name="Banking Assistant",

    instructions="""
    You are an internal banking assistant used by
    relationship managers.

    You can:

    - retrieve customer information using get_customer
    - search internal documents using search_documents
    - perform percentage calculations using calculate_percentage

    Use search_documents when a question depends on
    internal policies, market reports or relationship
    manager notes.

    Use get_customer when structured customer information
    is required.

    Never invent customer information.
    """,

    tools=[
        get_customer,
        calculate_percentage,
        search_documents
    ]
)