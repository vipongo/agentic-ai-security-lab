# SEC-003 — Indirect Prompt Injection / RAG Poisoning

**Severity:** High  
**Status:** Mitigated  
**Component:** RAG pipeline / agent context  
**Category:** Prompt Injection / Data Poisoning

## Description

Retrieved documents are attacker-influenceable input and may contain instructions designed to manipulate the agent.

A malicious public document was deliberately inserted into the RAG knowledge base containing instructions attempting to influence tool usage.

Example malicious content included instructions to invoke a customer lookup for an unauthorized customer.

## Attack Path

```text
Malicious document
       ↓
RAG ingestion
       ↓
Vector retrieval
       ↓
Agent context
       ↓
LLM interprets document
       ↓
Potential tool/action manipulation
```

## Observation

The malicious document was successfully retrievable through the normal authorized RAG path.

This demonstrated that authorization alone does not make retrieved content trustworthy.

The tested model did not consistently execute the malicious tool instruction, illustrating the probabilistic nature of prompt-injection exploitation.

## Security Impact

Potential consequences include:

- manipulated responses;
- unauthorized tool-call attempts;
- altered agent goals;
- misleading customer advice;
- excessive agency;
- attempted authorization bypass.

## Root Cause

Retrieved natural-language content and trusted application instructions originally shared the same model context without a strong trust distinction.

## Remediation

Multiple controls were introduced:

1. retrieved documents are explicitly wrapped as untrusted content;
2. agent instructions state that retrieved content cannot grant authorization or instruct tool execution;
3. suspicious retrieved content is scanned before reaching the model;
4. customer and tool authorization remains enforced outside the LLM;
5. high-impact actions remain protected by human approval.

Example:

```text
<UNTRUSTED_RETRIEVED_CONTENT>
...
</UNTRUSTED_RETRIEVED_CONTENT>
```

## Verification

Known poisoned documents are detected and excluded:

```text
RAG_CONTENT_SCAN
outcome=BLOCK
```

Unauthorized tool actions remain blocked even if malicious content influences the LLM.

## Residual Risk

Prompt-injection detection is inherently incomplete.

Attackers may use:

- obfuscation;
- encoding;
- multilingual instructions;
- indirect semantic manipulation;
- previously unseen attack patterns.

Therefore this finding is classified as **Mitigated**, not fully remediated.

The primary security boundary remains deterministic authorization outside the model.
