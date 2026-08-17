from typing import Annotated

from pydantic import Field


CustomerId = Annotated[
    str,
    Field(
        pattern=r"^CUST\d{3}$",
        min_length=7,
        max_length=7,
        description=(
            "Customer identifier in the form CUST001."
        ),
    ),
]


DestinationAccount = Annotated[
    str,
    Field(
        pattern=r"^DEMO-ACCOUNT-\d{3,6}$",
        description=(
            "Simulated destination account, for example "
            "DEMO-ACCOUNT-999."
        ),
    ),
]


TransferAmountCHF = Annotated[
    int,
    Field(
        ge=1,
        le=100_000,
        description=(
            "Transfer amount in whole CHF. "
            "Must be between CHF 1 and CHF 100000."
        ),
    ),
]


DocumentSearchQuery = Annotated[
    str,
    Field(
        min_length=2,
        max_length=500,
        description=(
            "Search query for authorized internal documents."
        ),
    ),
]