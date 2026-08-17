# Agentic AI Security Lab

A hands-on AI security engineering project focused on identifying, reproducing, testing, and mitigating security risks in LLM-based agentic applications.

The project implements a simplified enterprise-style banking assistant with:

- Structured customer data
- Multiple agent tools
- Retrieval-Augmented Generation (RAG)
- Public and user-specific documents
- Persistent multi-turn memory
- Simulated high-impact financial actions
- Human-in-the-loop approval
- Direct and indirect prompt-security controls
- Permission-scoped tool exposure
- Structured tool-call validation
- Rate limiting
- Structured security audit logging

The application is deliberately developed through **vulnerable and hardened iterations**.

```text
Build
  ↓
Exploit
  ↓
Test
  ↓
Mitigate
  ↓
Retest
  ↓
Document residual risk
```

> **Important:** All users, customers, documents, accounts, conversations, and transfers in this project are fictional. No real financial transaction is performed.

---

# Security Philosophy

A central design principle of this project is:

> **The LLM is not a security boundary.**

The model is treated as a potentially manipulable component that may:

- Follow malicious user instructions
- Follow malicious retrieved instructions
- Request inappropriate tools
- Generate malformed tool arguments
- Attempt unauthorized actions
- Attempt high-impact actions autonomously
- Expose internal information
- Carry information across conversation state
- Consume excessive application resources

Security-critical properties are therefore enforced through deterministic application controls wherever possible.

```text
LLM request
    │
    ▼
Application Security Controls
    │
 ┌──┴────┐
 │       │
ALLOW   DENY
```

The project distinguishes between:

```text
Authentication
     ≠
Authorization
     ≠
Tool availability
     ≠
Input validation
     ≠
Human approval
     ≠
Rate limiting
     ≠
Auditability
```

Each addresses a different security property.

---

# Current Release

## `v0.9-audit-rate-limit-controls`

The current hardened release adds:

- Structured JSONL security audit logging
- Unique event identifiers
- UTC event timestamps
- User-attributed security decisions
- Rate-limit audit events
- Prompt-security audit events
- HITL approval audit events
- Output-security audit events
- Customer authorization audit events
- RAG retrieval/content-security audit events
- Transfer authorization and execution audit events
- Per-user agent request rate limiting
- Transfer-specific rate limiting
- Tests verifying rate-limit isolation and expiry
- Tests verifying rate-limited actions create no protected side effect
- Tests verifying sensitive raw RAG queries are not written to audit events

Previously implemented controls remain active.

---

# Current Architecture

```text
                                  User
                                   │
                                   ▼
                            Agent Rate Limit
                                   │
                           ┌───────┴───────┐
                           │               │
                         DENY            ALLOW
                           │               │
                           ▼               ▼
                       Audit Event   Prompt Security
                                           │
                                           ▼
                                      AI Agent / LLM
                                           │
                                    Permission-Scoped
                                        Tool Set
                                           │
                      ┌────────────────────┼─────────────────────┐
                      │                    │                     │
                      ▼                    ▼                     ▼
               get_customer()      search_documents()     create_transfer()
                      │                    │                     │
                      ▼                    ▼                     ▼
                Object AuthZ         Retrieval ACL          HITL Approval
                      │                    │                     │
                      ▼                    ▼                     ▼
                 Audit Event        Content Scanner       Action AuthZ
                                           │                     │
                                           ▼                     ▼
                                      Audit Events        Transfer Rate Limit
                                                                 │
                                                                 ▼
                                                           Object AuthZ
                                                                 │
                                                                 ▼
                                                            Execution
                                                                 │
                                                                 ▼
                                                            Audit Event

                                      Agent Output
                                           │
                                           ▼
                                      Output Scan
                                           │
                                           ▼
                                      Audit Event
```

---

# Security Boundaries

The application currently models independent security boundaries around:

1. Customer object authorization
2. RAG retrieval authorization
3. Retrieved-content trust
4. Persistent session isolation
5. Tool availability
6. High-impact action authorization
7. Source-customer authorization
8. Human approval
9. Direct prompt policy
10. Tool argument validation
11. Agent-output inspection
12. Agent request rate limiting
13. High-impact transfer rate limiting
14. Security event auditing

A control implemented at one boundary is not assumed to replace another.

---

# Current Security Findings

| ID | Finding | Status |
|---|---|---|
| SEC-001 | Cross-customer authorization bypass | ✅ Mitigated |
| SEC-002 | Cross-user RAG authorization bypass | ✅ Mitigated |
| SEC-003 | Indirect prompt injection through RAG | 🛡️ Controls implemented |
| SEC-004 | Cross-user session memory leakage | ✅ Mitigated |
| SEC-007 | High-impact transfer without approval | ✅ Mitigated |
| SEC-008 | Unauthorized transfer | ✅ Mitigated |
| SEC-009 | Direct prompt-security enforcement gap | 🛡️ Mitigated for configured patterns |
| SEC-010 | Excessive tool exposure | ✅ Mitigated |
| SEC-011 | Malformed tool arguments | ✅ Mitigated at tool boundary |
| SEC-012 | Resource abuse / excessive request frequency | ✅ Mitigated with local rate limits |
| SEC-013 | Insufficient security-event auditability | ✅ Structured audit trail implemented |

---

# Customer Authorization

Customer data access is protected by object-level authorization.

```text
Alice → CUST001 → ALLOW
Alice → CUST002 → DENY

Bob   → CUST001 → DENY
Bob   → CUST002 → ALLOW
```

Both successful and denied customer authorization decisions are represented as structured security events.

Example event type:

```text
AUTHZ_CUSTOMER
```

Possible outcomes:

```text
ALLOW
DENY
```

---

# RAG Security

The RAG pipeline combines retrieval authorization and content security.

```text
Query
  ↓
Retrieval ACL
  ↓
Authorized Documents
  ↓
Content Scanner
  ↓
Explicit UNTRUSTED Boundary
  ↓
LLM
```

Audit events include:

```text
RAG_SEARCH
RAG_RETRIEVAL
RAG_CONTENT_SCAN
```

The search event records metadata such as:

```text
query_length
```

rather than storing the raw user query.

This intentionally reduces sensitive-content exposure in security logs.

---

# Prompt Security

Direct user prompts are scanned before being sent to the model.

```text
User Prompt
     │
     ▼
Prompt Scanner
     │
     ▼
Policy Decision
  ┌──┴─────┐
  │        │
BLOCK    ALLOW
```

Configured high-confidence rules include attacks such as:

- Instruction override
- Role override
- Security bypass
- System-prompt extraction
- Human-approval bypass

Detected and blocked prompts generate structured audit events.

Example:

```text
PROMPT_SECURITY
```

with outcomes such as:

```text
DETECTED
BLOCK
```

The application stores characteristics such as rule name and prompt length rather than the full malicious prompt.

---

# Tool Access / Least Privilege

Tool availability is permission-scoped.

```text
customer:read
    ↓
get_customer


document:read
    ↓
search_documents


transfer:create
    ↓
create_transfer
```

The goal is to reduce the capabilities exposed to the model according to the authenticated caller.

Tool availability does not replace object-level authorization.

---

# Structured Tool Validation

Agent-facing arguments use constrained schemas.

## Customer IDs

```text
^CUST\d{3}$
```

Valid:

```text
CUST001
CUST999
```

Invalid:

```text
cust001
CUST01
CUST0001
CUSTABC
```

---

## Destination Accounts

Only simulated account identifiers are accepted.

```text
DEMO-ACCOUNT-<3 to 6 digits>
```

Examples:

```text
DEMO-ACCOUNT-999       ✅
DEMO-ACCOUNT-123456    ✅

CH9300000000000000000  ❌
DEMO-ACCOUNT-ABC       ❌
```

---

## Transfer Amounts

Agent-facing transfers are constrained to:

```text
CHF 1 – CHF 100,000
```

---

## RAG Queries

Document-search queries are constrained to:

```text
minimum: 2 characters
maximum: 500 characters
```

---

# High-Impact Transfer Security

The simulated transfer tool combines multiple controls.

```text
Agent requests transfer
        │
        ▼
Tool Permission
        │
        ▼
Human Approval
        │
        ▼
Source-Customer Authorization
        │
        ▼
Input Validation
        │
        ▼
Transfer Rate Limit
        │
        ▼
Simulated Execution
```

This ensures that:

```text
Human approval
```

does not replace:

```text
Authorization
```

and authorization does not replace:

```text
Validation
```

or:

```text
Abuse protection
```

---

# SEC-012 — Resource Abuse / Rate Limiting

## Status: ✅ Mitigated for the local lab

LLM and agentic applications may be abused by repeatedly triggering:

- Model requests
- RAG retrieval
- Tool execution
- High-impact operations

The project therefore implements two independent sliding-window rate limits.

---

## Agent Request Rate Limit

Current configuration:

```text
10 requests
per
60 seconds
per user
```

The limiter is keyed by username.

Therefore:

```text
Alice exhausting Alice's quota
```

must not cause:

```text
Bob's quota to be exhausted
```

---

## Transfer Rate Limit

The simulated high-impact transfer capability has a stricter limit:

```text
3 transfer requests
per
300 seconds
per user
```

This provides a separate control around repeated high-impact operations.

---

# Rate-Limit Flow

```text
Request
   │
   ▼
Sliding Window
   │
 ┌─┴─────────┐
 │           │
ALLOW       DENY
 │           │
 ▼           ▼
Continue   Audit
             │
             ▼
           Reject
```

Rate-limited agent requests do not reach model execution.

Rate-limited transfer requests do not create an additional transfer record.

---

# Rate-Limit Audit Events

Agent-level rate limiting produces:

```text
RATE_LIMIT
```

with:

```text
ALLOW
DENY
```

and useful metadata including:

```text
remaining
retry_after_seconds
```

Transfer rate limiting generates:

```text
TRANSFER_RATE_LIMIT
```

when the high-impact operation is denied.

---

# Rate-Limiter Limitations

The current limiter is intentionally appropriate for a local security lab.

It is:

```text
in-memory
per-process
```

Therefore state is reset if the application restarts.

It is not designed as a distributed production-grade rate-limiting system.

A production deployment would typically require a shared backend or gateway-level enforcement.

---

# SEC-013 — Security Auditability

## Status: ✅ Structured audit trail implemented

Security controls should not only make decisions.

Those decisions must also be observable.

The project therefore introduces structured security audit events.

---

# Audit Event Format

Audit records are stored as JSON Lines:

```text
security-audit.jsonl
```

Each event contains:

```json
{
  "event_id": "...",
  "timestamp": "...",
  "event_type": "...",
  "username": "...",
  "outcome": "...",
  "details": {}
}
```

Each event receives:

- Unique event ID
- UTC timestamp
- Event type
- Authenticated username
- Security outcome
- Structured event-specific details

---

# Current Audit Event Types

The system currently emits security events including:

```text
RATE_LIMIT
PROMPT_SECURITY
HUMAN_APPROVAL
OUTPUT_SECURITY

AUTHZ_CUSTOMER

RAG_SEARCH
RAG_RETRIEVAL
RAG_CONTENT_SCAN

TOOL_ACCESS

AUTHZ_TRANSFER
TRANSFER_RATE_LIMIT
TRANSFER_EXECUTION
```

---

# Example Authorization Event

```json
{
  "event_type": "AUTHZ_CUSTOMER",
  "username": "alice",
  "outcome": "DENY",
  "details": {
    "customer_id": "CUST002",
    "reason": "customer_not_authorized"
  }
}
```

---

# Example Prompt-Security Event

```json
{
  "event_type": "PROMPT_SECURITY",
  "username": "alice",
  "outcome": "BLOCK",
  "details": {
    "rule": "instruction_override"
  }
}
```

---

# Example Transfer Event

```json
{
  "event_type": "TRANSFER_EXECUTION",
  "username": "alice",
  "outcome": "SUCCESS",
  "details": {
    "source_customer_id": "CUST001",
    "amount_chf": 1000
  }
}
```

The simulated destination account is intentionally not required in the successful transfer audit event.

This demonstrates basic audit-data minimization.

---

# Audit Data Minimization

Audit logs themselves can become a sensitive-data source.

The logger documentation therefore explicitly warns against recording:

```text
Secrets
Full prompts
Customer records
Other sensitive content
```

Examples of deliberate minimization include:

```text
RAG query
    ↓
store query_length
rather than raw query
```

and:

```text
Prompt
    ↓
store rule + length
rather than full prompt
```

---

# Audit Trail Limitations

The current audit trail is designed for the local lab.

It is stored in a local JSONL file.

This provides:

```text
Structured
Searchable
Append-oriented
Human-readable
Machine-readable
```

security evidence.

It does **not** provide production-grade properties such as:

- Cryptographic log integrity
- Tamper-evident storage
- Centralized collection
- SIEM integration
- Retention policies
- Log rotation
- Remote immutable storage
- Alert correlation

These remain production considerations rather than claims of the current implementation.

---

# Human-in-the-Loop Auditing

High-impact transfer requests require operator approval.

Approval outcomes are now explicitly recorded.

```text
HUMAN_APPROVAL
```

Possible outcomes:

```text
APPROVED
REJECTED
```

Conceptually:

```text
Agent requests transfer
        │
        ▼
Human Approval
   ┌────┴─────┐
   │          │
APPROVE     REJECT
   │          │
   └────┬─────┘
        ▼
    Audit Event
```

---

# Output-Security Auditing

The project contains a controlled internal marker used to test output leakage.

If output security blocks a response:

```text
OUTPUT_SECURITY
```

is recorded with:

```text
outcome = BLOCK
```

and the matching security rule.

---

# Security Testing Strategy

The project deliberately separates deterministic application-security tests from probabilistic model-behavior tests.

## Deterministic Tests

pytest currently covers:

```text
Customer authorization                    ✅
RAG authorization                         ✅
RAG content security                      ✅
Session isolation                         ✅
Transfer authorization                    ✅
Human approval                            ✅
Prompt-security enforcement               ✅
Output canary enforcement                 ✅
Tool permissions                          ✅
Least-privilege tool exposure             ✅
Structured tool schemas                   ✅
Transfer validation                       ✅
Agent rate limiting                       ✅
Transfer rate limiting                    ✅
Per-user rate-limit isolation             ✅
Rate-limit window expiry                  ✅
Rate-limited side-effect prevention       ✅
Audit JSONL structure                     ✅
Audit event append behavior               ✅
Authorization audit events                ✅
RAG audit events                          ✅
Transfer audit events                     ✅
Audit data minimization                   ✅
```

Run:

```powershell
python -m pytest -v
```

---

# Deterministic vs Probabilistic Testing

```text
Application Security Property
           │
           ▼
         pytest


Model / LLM Behavior
           │
           ▼
   Promptfoo / Red Teaming
```

Future probabilistic tests will target:

- Jailbreaking
- Direct prompt-injection variations
- Indirect prompt injection
- System-prompt extraction
- Tool manipulation
- Approval manipulation
- Sensitive-data extraction
- Semantic and obfuscated attacks

---

# Current Attack Matrix

| ID | Threat | Control | Evidence |
|---|---|---|---|
| SEC-001 | Cross-customer access | Object authorization | pytest ✅ |
| SEC-002 | Cross-user RAG retrieval | Retrieval ACL | pytest ✅ |
| SEC-003 | Indirect prompt injection | Content scan + trust boundary | pytest ✅ |
| SEC-004 | Cross-user session leakage | User-bound sessions | pytest ✅ |
| SEC-007 | Autonomous high-impact transfer | HITL | pytest + CLI ✅ |
| SEC-008 | Unauthorized transfer | Action + object AuthZ | pytest ✅ |
| SEC-009 | Direct prompt injection | Prompt policy + output scan | pytest ✅ |
| SEC-010 | Excessive tool exposure | Permission-scoped tools | pytest ✅ |
| SEC-011 | Malformed tool arguments | Structured schemas | pytest ✅ |
| SEC-012 | Request / transfer resource abuse | Sliding-window rate limits | pytest ✅ |
| SEC-013 | Insufficient security observability | Structured audit trail | pytest ✅ |

---

# Git Security Evolution

Version tags represent hardened security checkpoints.

```text
v0.1-vulnerable-baseline
        │
        ▼
v0.2-authz-controls
        │
        ▼
v0.3-rag-authz-controls
        │
        ▼
v0.4-rag-injection-controls
        │
        ▼
v0.5-session-isolation-controls
        │
        ▼
v0.6-transfer-authz-hitl-controls
        │
        ▼
v0.7-prompt-security-controls
        │
        ▼
v0.8-tool-access-validation-controls
        │
        ▼
v0.9-audit-rate-limit-controls
```

---

# Development Roadmap

## Customer Authorization

- [x] Reproduce cross-customer access
- [x] Add tests
- [x] Enforce object authorization
- [x] Retest

## RAG Authorization

- [x] Reproduce cross-user retrieval
- [x] Add retrieval ACL
- [x] Add tests
- [x] Retest

## Indirect Prompt Injection

- [x] Introduce malicious retrieved content
- [x] Add content scanner
- [x] Add untrusted-content boundary
- [x] Add regression tests
- [x] Document residual risk

## Session Isolation

- [x] Introduce shared-session vulnerability
- [x] Reproduce cross-user leakage
- [x] Bind sessions to authenticated users
- [x] Add regression tests

## Tool Abuse / Excessive Agency

- [x] Add simulated high-impact transfer
- [x] Demonstrate execution without approval
- [x] Demonstrate unauthorized transfer
- [x] Add action authorization
- [x] Add object authorization
- [x] Add HITL
- [x] Test approve/reject paths

## Direct Prompt Security

- [x] Add controlled security canary
- [x] Create detection-only vulnerable baseline
- [x] Add blocking policy
- [x] Enforce configured rules pre-model
- [x] Add output canary protection
- [x] Add regression tests

## Tool Access / Least Privilege

- [x] Add explicit permissions
- [x] Dynamically expose tools
- [x] Test least-privilege behavior
- [x] Preserve internal authorization controls

## Structured Tool Validation

- [x] Validate customer IDs
- [x] Validate simulated accounts
- [x] Validate transfer amounts
- [x] Validate RAG queries
- [x] Test generated schemas
- [x] Verify invalid transfers create no side effect

## Rate Limiting / Resource Abuse

- [x] Add per-user agent rate limiter
- [x] Add transfer-specific rate limiter
- [x] Test quota exhaustion
- [x] Test per-user isolation
- [x] Test sliding-window expiry
- [x] Prevent rate-limited transfer side effects
- [x] Audit rate-limit decisions

## Security Logging / Audit Trail

- [x] Add structured JSONL security events
- [x] Add unique event IDs
- [x] Add UTC timestamps
- [x] Record authenticated user
- [x] Record security outcomes
- [x] Audit customer authorization
- [x] Audit RAG operations
- [x] Audit prompt-security decisions
- [x] Audit human approval
- [x] Audit transfer authorization
- [x] Audit transfer rate limiting
- [x] Audit successful transfer execution
- [x] Audit output-security blocking
- [x] Add audit data-minimization tests
- [x] Release `v0.9-audit-rate-limit-controls`

---

# Remaining Work

## Output Validation / Sensitive-Data Controls

- [ ] Expand beyond controlled prompt canary
- [ ] Identify sensitive output fields
- [ ] Test role-dependent disclosure
- [ ] Implement redaction where appropriate
- [ ] Minimize error-detail disclosure
- [ ] Test authorization-scoped final outputs

## Automated Security / Red-Team Testing

- [ ] Introduce Promptfoo
- [ ] Add direct prompt-injection attack corpus
- [ ] Add indirect injection cases
- [ ] Add jailbreak variants
- [ ] Add system-prompt extraction tests
- [ ] Add tool-manipulation tests
- [ ] Separate deterministic and probabilistic results

## Threat Model

- [ ] Architecture diagram
- [ ] Assets
- [ ] Entry points
- [ ] Trust boundaries
- [ ] STRIDE analysis
- [ ] OWASP LLM / GenAI mapping
- [ ] Threat → control mapping
- [ ] Residual-risk assessment

## Finding Documentation

Each final finding will document:

```text
Security requirement
Attack
Expected behavior
Observed vulnerable behavior
Root cause
Mitigation
Regression test
Post-control result
Residual risk
```

## Final GitHub Polish

- [ ] Final concise README
- [ ] Architecture diagram
- [ ] Formal threat model
- [ ] Attack matrix
- [ ] Control mapping
- [ ] Security-test results
- [ ] Sanitized log examples
- [ ] Setup instructions
- [ ] `.env.example`
- [ ] Dependency documentation
- [ ] Lessons learned

---

# Current Security-Control Stack

```text
USER
 │
 ▼
Rate Limiting
 │
 ▼
Prompt Security
 │
 ▼
LLM / Agent
 │
 ▼
Least-Privilege Tool Exposure
 │
 ▼
Structured Tool Validation
 │
 ▼
Authorization
 │
 ▼
Human Approval
 │
 ▼
Business Logic
 │
 ▼
Output Security
 │
 ▼
USER


Across the pipeline:

        SECURITY AUDIT TRAIL
```

---

# Final Objective

The completed lab demonstrates practical security engineering across:

```text
Agent
├── Prompt security
├── Least-privilege tool access
├── Tool authorization
├── Human approval
└── Structured validation

RAG
├── Retrieval authorization
├── Indirect prompt injection
├── Content trust
└── Poisoning

Memory
├── Session isolation
└── Cross-user leakage

Application
├── Rate limiting
├── Output security
├── Security logging
└── Auditability

Testing
├── Deterministic pytest controls
└── Probabilistic LLM red teaming

Threat Modelling
├── STRIDE
├── OWASP LLM / GenAI
└── Residual risk
```

The objective is not simply to show that an AI agent can be attacked.

It is to demonstrate:

> **where trust boundaries belong, which controls must remain deterministic, how high-impact agent actions can be constrained, how abuse can be limited, and how security-relevant decisions can be independently tested and audited.**