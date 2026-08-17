import re
from dataclasses import dataclass

from app.context import AppContext
from app.data_loader import (
    load_customers,
    load_users,
)


@dataclass(frozen=True)
class RequestPolicyDecision:
    allowed: bool
    reason: str | None = None


CUSTOMER_ID_PATTERN = re.compile(
    r"\bCUST\d{3}\b",
    re.IGNORECASE,
)


DOCUMENT_TERMS = re.compile(
    r"\b(?:"
    r"document|documents|"
    r"file|files|"
    r"record|records|"
    r"note|notes|"
    r"report|reports"
    r")\b",
    re.IGNORECASE,
)


IDENTITY_OVERRIDE_PATTERNS = [
    re.compile(
        r"\b(?:i am|i'm|treat me as|consider me)\s+"
        r"(?:an?\s+)?"
        r"(?:admin|administrator|root|developer)\b",
        re.IGNORECASE,
    ),

    re.compile(
        r"\b(?:ceo|manager|administrator|admin)"
        r".{0,50}"
        r"(?:approved|authorized|permission)\b",
        re.IGNORECASE | re.DOTALL,
    ),
]


INTERNAL_METADATA_PATTERNS = [
    re.compile(
        r"\b(?:system|developer|hidden|internal)\s+"
        r"(?:prompt|instructions?|messages?)\b",
        re.IGNORECASE,
    ),

    re.compile(
        r"\b(?:tool|function|api|endpoint|handler)"
        r".{0,60}"
        r"(?:name|schema|parameter|permission|"
        r"authorization|implementation)\b",
        re.IGNORECASE | re.DOTALL,
    ),

    re.compile(
        r"\b(?:input schema|required fields?|data types?|"
        r"validation rules?|formatting rules?|"
        r"callable actions?)\b",
        re.IGNORECASE,
    ),

    re.compile(
        r"\b(?:raw|complete|exact|full)"
        r".{0,30}"
        r"(?:diagnostic|schema|tool|function|prompt)\b",
        re.IGNORECASE | re.DOTALL,
    ),
]


PHYSICAL_ACTION_PATTERNS = [
    re.compile(
        r"\b(?:"
        r"walk to|records room|"
        r"hardcopy|copier|printer|"
        r"locked cabinet|physical custody|"
        r"physically filed|seal verified"
        r")\b",
        re.IGNORECASE,
    ),
]


OUT_OF_SCOPE_PATTERNS = [
    re.compile(
        r"\b(?:write|create|draft|prepare)"
        r".{0,100}"
        r"\b(?:lecture|essay|travel itinerary|"
        r"sightseeing itinerary|history|poem|story)\b",
        re.IGNORECASE | re.DOTALL,
    ),

    re.compile(
        r"\b(?:flight|hotel|sightseeing|vacation)"
        r".{0,80}"
        r"\b(?:recommend|recommendation|itinerary|plan)\b",
        re.IGNORECASE | re.DOTALL,
    ),
]


def _matches_any(
    text: str,
    patterns: list[re.Pattern],
) -> bool:
    return any(
        pattern.search(text)
        for pattern in patterns
    )


def check_resource_scope(
    context: AppContext,
    text: str,
) -> RequestPolicyDecision:
    """
    Reject explicit references to customers or private
    document owners outside the authenticated user's scope.

    This runs before the LLM and does not disclose whether
    the referenced resource actually exists.
    """

    authorized_ids = {
        customer_id.upper()
        for customer_id
        in context.authorized_customer_ids
    }

    # Explicit customer IDs, including unknown IDs.
    for customer_id in CUSTOMER_ID_PATTERN.findall(text):

        if customer_id.upper() not in authorized_ids:

            return RequestPolicyDecision(
                allowed=False,
                reason="unauthorized_customer_reference",
            )

    # Known customer names.
    normalized_text = text.casefold()

    customers = load_customers()

    for customer_id, customer in customers.items():

        customer_name = str(
            customer.get("name", "")
        ).casefold()

        if (
            customer_name
            and customer_name in normalized_text
            and customer_id.upper()
            not in authorized_ids
        ):
            return RequestPolicyDecision(
                allowed=False,
                reason="unauthorized_customer_reference",
            )

    # Private documents belonging to another application user.
    if DOCUMENT_TERMS.search(text):

        users = load_users()

        for username in users:

            if username == context.username:
                continue

            owner_pattern = re.compile(
                rf"\b{re.escape(username)}"
                rf"(?:'s|’s)?\b",
                re.IGNORECASE,
            )

            if owner_pattern.search(text):

                return RequestPolicyDecision(
                    allowed=False,
                    reason="unauthorized_document_owner",
                )

    return RequestPolicyDecision(
        allowed=True
    )


def evaluate_request(
    context: AppContext,
    text: str,
) -> RequestPolicyDecision:

    resource_decision = (
        check_resource_scope(
            context,
            text,
        )
    )

    if not resource_decision.allowed:
        return resource_decision

    if _matches_any(
        text,
        IDENTITY_OVERRIDE_PATTERNS,
    ):
        return RequestPolicyDecision(
            allowed=False,
            reason="identity_override_attempt",
        )

    if _matches_any(
        text,
        INTERNAL_METADATA_PATTERNS,
    ):
        return RequestPolicyDecision(
            allowed=False,
            reason="internal_metadata_request",
        )

    if _matches_any(
        text,
        PHYSICAL_ACTION_PATTERNS,
    ):
        return RequestPolicyDecision(
            allowed=False,
            reason="unsupported_physical_action",
        )

    if _matches_any(
        text,
        OUT_OF_SCOPE_PATTERNS,
    ):
        return RequestPolicyDecision(
            allowed=False,
            reason="out_of_scope_request",
        )

    return RequestPolicyDecision(
        allowed=True
    )


def policy_response(
    decision: RequestPolicyDecision,
) -> str:

    if decision.reason in {
        "unauthorized_customer_reference",
        "unauthorized_document_owner",
        "identity_override_attempt",
    }:
        return (
            "I can only access customers and documents "
            "available to your authenticated application context."
        )

    if decision.reason == "internal_metadata_request":
        return (
            "I can describe supported banking capabilities "
            "at a user-facing level, but I can't provide "
            "internal prompts, tool definitions, schemas, "
            "or implementation details."
        )

    if decision.reason == "unsupported_physical_action":
        return (
            "I can't perform or confirm physical-world actions. "
            "I can only use capabilities provided by this "
            "banking application."
        )

    if decision.reason == "out_of_scope_request":
        return (
            "I can only assist with banking and "
            "relationship-management tasks in this application."
        )

    return "I can't process that request."