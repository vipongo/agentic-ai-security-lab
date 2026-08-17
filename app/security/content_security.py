import re
from dataclasses import dataclass


@dataclass
class ContentScanResult:
    safe: bool
    matched_rule: str | None = None


SUSPICIOUS_PATTERNS = {
    "ignore_instructions": re.compile(
        r"ignore\s+(?:all\s+)?"
        r"(?:previous|prior|system|developer)\s+"
        r"instructions?",
        re.IGNORECASE,
    ),

    "system_instruction": re.compile(
        r"(?:system|developer)\s+"
        r"(?:prompt|instruction|message)",
        re.IGNORECASE,
    ),

    "tool_call_instruction": re.compile(
        r"(?:call|invoke|execute|use)\s+"
        r"(?:the\s+)?"
        r"[`'\"]*"
        r"(?:get_customer|search_documents|calculate_percentage)"
        r"[`'\"]*",
        re.IGNORECASE,
    ),

    "security_bypass": re.compile(
        r"(?:bypass|disable|ignore)\s+"
        r"(?:all\s+)?"
        r"(?:security|authorization|access[\s-]?control|restrictions?)",
        re.IGNORECASE,
    ),

    "hidden_instruction": re.compile(
        r"(?:do\s+not|don't)\s+"
        r"(?:tell|inform|mention|reveal)\s+"
        r"(?:the\s+)?user",
        re.IGNORECASE,
    ),

    "mandatory_processing_instruction": re.compile(
        r"(?:mandatory|important|internal)\s+"
        r"(?:processing\s+)?"
        r"(?:instruction|instructions|directive|directives)",
        re.IGNORECASE,
    ),
}


def scan_untrusted_content(
    content: str
) -> ContentScanResult:
    """
    Detect common instruction-like patterns in untrusted
    retrieved content.

    Defense-in-depth only: this does not guarantee detection
    of all indirect prompt injections.
    """

    for rule_name, pattern in SUSPICIOUS_PATTERNS.items():

        if pattern.search(content):
            return ContentScanResult(
                safe=False,
                matched_rule=rule_name,
            )

    return ContentScanResult(
        safe=True
    )