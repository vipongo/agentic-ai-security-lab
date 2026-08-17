import re
from dataclasses import dataclass

SYSTEM_PROMPT_CANARY = (
    "POLICY-CANARY-7F3A92"
)

INTERNAL_OUTPUT_PATTERNS = {
    "system_prompt_canary": re.compile(
        re.escape(
            SYSTEM_PROMPT_CANARY
        ),
        re.IGNORECASE,
    ),

    "internal_tool_name": re.compile(
        r"\b(?:"
        r"get_customer|"
        r"search_documents|"
        r"calculate_percentage|"
        r"create_transfer|"
        r"multi_tool_use\.parallel"
        r")\b",
        re.IGNORECASE,
    ),

    "internal_parameter_name": re.compile(
        r"\b(?:"
        r"source_customer_id|"
        r"destination_account|"
        r"amount_chf"
        r")\b",
        re.IGNORECASE,
    ),
}

@dataclass
class OutputScanResult:
    safe: bool
    matched_rule: str | None = None


def scan_agent_output(
    output: str
) -> OutputScanResult:

    for (
        rule_name,
        pattern,
    ) in INTERNAL_OUTPUT_PATTERNS.items():

        if pattern.search(output):

            return OutputScanResult(
                safe=False,
                matched_rule=rule_name,
            )

    return OutputScanResult(
        safe=True
    )

@dataclass
class PromptScanResult:
    suspicious: bool
    matched_rule: str | None = None


SUSPICIOUS_PROMPT_PATTERNS = {
    "instruction_override": re.compile(
        r"ignore\s+(?:all\s+)?"
        r"(?:previous|prior|system|developer)\s+"
        r"instructions?",
        re.IGNORECASE,
    ),

    "role_override": re.compile(
        r"(?:you are now|act as|switch to)\s+"
        r"(?:an?\s+)?"
        r"(?:administrator|admin|developer|system|root)",
        re.IGNORECASE,
    ),

    "fake_authorization": re.compile(
        r"(?:ceo|administrator|admin|management)"
        r".{0,40}"
        r"(?:approved|authorized|permission)",
        re.IGNORECASE | re.DOTALL,
    ),

    "security_bypass": re.compile(
        r"(?:bypass|disable|ignore|override)\s+"
        r"(?:all\s+)?"
        r"(?:security|authorization|access[\s-]?control|restrictions?)",
        re.IGNORECASE,
    ),

    "system_prompt_request": re.compile(
        r"(?:show|print|reveal|repeat|display|provide)"
        r".{0,40}"
        r"(?:system|developer|hidden|internal)"
        r".{0,20}"
        r"(?:prompt|instructions?|message|configuration)",
        re.IGNORECASE | re.DOTALL,
    ),

    "previous_instruction_request": re.compile(
        r"(?:repeat|show|print|reveal)"
        r".{0,50}"
        r"(?:everything|instructions?)"
        r".{0,30}"
        r"(?:above|before|previously)",
        re.IGNORECASE | re.DOTALL,
    ),

    "approval_bypass": re.compile(
        r"(?:do\s+not|don't|never)\s+"
        r"(?:ask|request|require)"
        r".{0,30}"
        r"(?:approval|confirmation|human)",
        re.IGNORECASE | re.DOTALL,
    ),
    "system_prompt_request": re.compile(
        r"(?:show|print|reveal|repeat|display|provide|"
        r"reproduce|quote|dump|output|expose)"
        r".{0,60}"
        r"(?:system|developer|hidden|internal)"
        r".{0,30}"
        r"(?:prompt|instructions?|messages?|configuration)",
        re.IGNORECASE | re.DOTALL,
    ),
    "indirect_instruction_extraction": re.compile(
        r"(?:system|developer)\s+instructions?"
        r"|"
        r"(?:design|draft|write)"
        r".{0,80}"
        r"(?:banking assistant|similar system)"
        r".{0,80}"
        r"(?:instructions?|prompt|policy)",
        re.IGNORECASE | re.DOTALL,
    ),
}


def scan_user_prompt(
    prompt: str
) -> PromptScanResult:
    """
    Detect common direct prompt-injection and system-prompt
    extraction patterns.

    This is a defense-in-depth control only. It must not be
    relied upon for authorization or permission enforcement.
    """

    for rule_name, pattern in SUSPICIOUS_PROMPT_PATTERNS.items():

        if pattern.search(prompt):

            return PromptScanResult(
                suspicious=True,
                matched_rule=rule_name,
            )

    return PromptScanResult(
        suspicious=False
    )

def should_block_prompt(
    scan_result: PromptScanResult
) -> bool:
    """
    Decide which detected patterns should be rejected before
    reaching the model.
    """

    HIGH_CONFIDENCE_BLOCK_RULES = {
        "instruction_override",
        "role_override",
        "security_bypass",
        "system_prompt_request",
        "approval_bypass",
        "indirect_instruction_extraction",
    }

    return (
        scan_result.suspicious
        and scan_result.matched_rule
        in HIGH_CONFIDENCE_BLOCK_RULES
    )