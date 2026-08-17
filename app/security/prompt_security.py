import re
from dataclasses import dataclass

SYSTEM_PROMPT_CANARY = (
    "POLICY-CANARY-7F3A92"
)
@dataclass
class OutputScanResult:
    safe: bool
    matched_rule: str | None = None


def scan_agent_output(
    output: str
) -> OutputScanResult:
    """
    Detect known internal markers in model output.

    This protects controlled security-test markers from being
    returned to the user.

    It is not a general solution for sensitive-data detection.
    """

    if SYSTEM_PROMPT_CANARY.lower() in output.lower():

        return OutputScanResult(
            safe=False,
            matched_rule="system_prompt_canary"
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
    }

    return (
        scan_result.suspicious
        and scan_result.matched_rule
        in HIGH_CONFIDENCE_BLOCK_RULES
    )