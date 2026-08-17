# Agentic AI Security Lab

A hands-on AI security engineering project focused on identifying, reproducing, testing, and mitigating security risks in LLM-based agentic applications.

The project implements a simplified enterprise-style banking assistant with access to:

- Structured customer data
- Multiple agent tools
- Retrieval-Augmented Generation (RAG)
- Public and user-specific documents
- Persistent multi-turn memory
- Simulated high-impact financial actions
- Human-in-the-loop approval
- Direct prompt-security controls
- Agent-output leakage controls
- Least-privilege tool exposure
- Structured tool-call validation

The system is deliberately developed through **vulnerable and hardened iterations**.

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

> **Important:** All users, customers, documents, accounts, conversations, and transfers used in this project are fictional. No real financial transaction is performed.

---

# Security Philosophy

A central design principle of this project is:

> **The LLM is not a security boundary.**

The model is treated as an untrusted decision-making component that may:

- Be manipulated through direct prompts
- Be manipulated through retrieved documents
- Request unauthorized resources
- Select inappropriate tools
- Generate malformed tool arguments
- Attempt high-impact operations
- Expose internal information
- Carry data across conversation state

Security-sensitive decisions are therefore enforced by deterministic application controls wherever possible.

```text
LLM request / decision
        │
        ▼
Application controls
        │
   ┌────┴────┐
   │         │
 ALLOW      DENY
```

The project also distinguishes several different security properties:

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
```

Each requires its own control.

---

# Current Release

## `v0.8-tool-access-validation-controls`

The current release adds:

- Permission-scoped tool exposure
- Least-privilege agent capabilities
- Structured customer-ID validation
- Structured transfer-account validation
- Transfer amount bounds
- RAG query-length constraints
- Tests verifying generated agent tool schemas
- Tests verifying disabled tools are not exposed to the agent
- Regression tests verifying invalid transfer inputs create no side effects

Previously implemented controls remain active:

- Customer object-level authorization
- RAG retrieval authorization
- Indirect prompt-injection defenses
- Session isolation
- Transfer authorization
- Human-in-the-loop approval
- Direct prompt-security filtering
- Controlled output-leakage detection

---

# Current Architecture

```text
                              User
                               │
                               ▼
                        Prompt Security
                               │
                               ▼
                         AI Agent / LLM
                               │
                         Tool Selection
                               │
                               ▼
                    Permission-Based Tool Set
                               │
             ┌─────────────────┼──────────────────┐
             │                 │                  │
             ▼                 ▼                  ▼
      get_customer()    search_documents()  create_transfer()
             │                 │                  │
             │                 │                  ▼
             │                 │             HITL Approval
             │                 │                  │
             ▼                 ▼                  ▼
       Object AuthZ      Retrieval AuthZ     Action AuthZ
                               │                  │
                               ▼                  ▼
                           RAG Scan         Object AuthZ
                               │                  │
                               ▼                  ▼
                          LLM Context        Business Logic
                                                    │
                                                    ▼
                                             Simulated Side
                                                 Effect
```

Tool calls also cross a structured validation boundary:

```text
LLM-generated arguments
          │
          ▼
    Tool JSON Schema
          │
      ┌───┴────┐
      │        │
    Valid    Invalid
      │        │
      ▼        ▼
 Continue    Reject
```

---

# Security Boundaries

The application currently models independent boundaries around:

1. Customer object authorization
2. RAG retrieval authorization
3. Retrieved-content trust
4. Persistent session isolation
5. High-impact action permission
6. Source-customer authorization
7. Human approval
8. Direct prompt policy
9. Agent-output inspection
10. Agent tool availability
11. Tool argument validation

A security control at one layer is not assumed to protect another.

---

# Mock Users

Two fictional relationship managers are used:

| User | Role | Authorized Customer |
|---|---|---|
| Alice | Advisor | `CUST001` |
| Bob | Advisor | `CUST002` |

User context contains:

```text
username
user_id
role
authorized_customer_ids
permissions
```

Permissions are used independently from customer ownership.

---

# Least-Privilege Tool Access

## SEC-010 — Excessive Tool Exposure

### Status: ✅ Mitigated

Giving every user every tool increases the agent's available attack surface.

The project now controls tool availability using explicit permissions.

Three permission checks currently exist:

```text
customer:read
document:read
transfer:create
```

Conceptually:

```text
Authenticated User
       │
       ▼
Application Permissions
       │
       ├── customer:read
       ├── document:read
       └── transfer:create
       │
       ▼
Agent Tool Set
```

A user without a required permission should not have that capability exposed to the model.

---

# Tool Access Controls

## Customer Access

```text
customer:read
      │
      ▼
get_customer enabled
```

Without the permission:

```text
get_customer
     ↓
not exposed
```

## Document Access

```text
document:read
      │
      ▼
search_documents enabled
```

## Transfer Access

```text
transfer:create
      │
      ▼
create_transfer enabled
```

This reduces the number of capabilities available to the LLM according to the authenticated caller.

---

# Why Tool Availability and Authorization Are Different

Tool hiding alone is not sufficient security.

For example:

```text
transfer:create
      │
      ▼
create_transfer exposed
```

does not mean:

```text
Alice may transfer from every customer
```

The transfer flow still requires:

```text
Tool Permission
      ↓
Human Approval
      ↓
Source-Customer Authorization
      ↓
Execution
```

This is defense in depth.

The high-impact transfer business logic also independently checks the `transfer:create` permission before creating a side effect.

---

# Least-Privilege Example

Consider a user with only:

```text
document:read
```

The expected agent capability set is:

```text
search_documents       ✅

get_customer           ❌
create_transfer        ❌
```

The security test suite verifies this behavior at the actual agent tool-set level, not only by calling the helper permission functions.

---

# Structured Tool Calls

## SEC-011 — Malformed Tool Arguments

### Status: ✅ Mitigated at the agent-facing tool boundary

LLMs generate tool arguments dynamically.

Without structured validation, values such as:

```text
customer_id = "John Smith"

amount_chf = -5000

destination_account = "anything"

query = ""
```

could reach application logic.

Agent-facing tools now use constrained argument types.

---

# Customer ID Schema

Customer IDs must match:

```text
CUST + exactly 3 digits
```

Examples:

```text
CUST001     ✅
CUST123     ✅
CUST999     ✅

cust001     ❌
CUST01      ❌
CUST0001    ❌
CUSTABC     ❌
```

Conceptual pattern:

```text
^CUST\d{3}$
```

---

# Destination Account Schema

Transfers in this project intentionally use simulated accounts only.

Valid format:

```text
DEMO-ACCOUNT-<3 to 6 digits>
```

Examples:

```text
DEMO-ACCOUNT-001        ✅
DEMO-ACCOUNT-999        ✅
DEMO-ACCOUNT-123456     ✅

DEMO-ACCOUNT-12         ❌
DEMO-ACCOUNT-ABC        ❌
CH9300000000000000000   ❌
```

This explicitly prevents the lab from treating real-looking banking identifiers as valid simulated transfer destinations.

---

# Transfer Amount Schema

Agent-facing transfer amounts must be whole CHF values between:

```text
CHF 1
```

and:

```text
CHF 100,000
```

Examples:

```text
1          ✅
1000       ✅
50000      ✅
100000     ✅

0          ❌
-1         ❌
100001     ❌
```

---

# Document Search Schema

RAG queries must contain:

```text
minimum length = 2
maximum length = 500
```

This rejects trivial or unexpectedly large values at the tool boundary.

Examples:

```text
"Q3"                                  ✅
"CUST001 investment preferences"      ✅

""                                    ❌
"A"                                   ❌
501-character query                   ❌
```

---

# Validation Boundary

The schemas protect the path:

```text
LLM
 ↓
Agent Tool
 ↓
Schema Validation
 ↓
Application Logic
```

This is an important trust boundary.

Python type annotations alone should not be interpreted as universal runtime validation for every internal function call.

For example:

```text
create_transfer()
```

uses the structured agent-facing schema, while:

```text
create_transfer_logic()
```

is internal business logic.

Direct application calls to inner functions must therefore either originate from trusted validated paths or perform their own critical checks.

---

# Transfer Defense in Depth

The transfer implementation currently includes additional deterministic checks inside the business logic.

```text
Transfer Request
      │
      ▼
transfer:create?
      │
      ▼
Authorized customer?
      │
      ▼
Amount > 0?
      │
      ▼
Valid DEMO-ACCOUNT format?
      │
      ▼
Create simulated transfer
```

Therefore invalid destination values are rejected even if the internal function is called directly.

A denied validation request produces:

```text
No transfer record
```

rather than merely returning an error after creating the side effect.

---

# Important Validation Design Note

The agent-facing transfer schema imposes:

```text
1 <= amount_chf <= 100000
```

The internal transfer function independently rejects:

```text
amount_chf <= 0
```

The upper CHF 100,000 limit is currently enforced at the **tool/schema boundary** rather than duplicated inside the business-logic function.

This distinction is intentional to make trust boundaries visible in the lab.

A future hardening iteration could choose to duplicate high-value invariants inside domain logic if those functions may be invoked from other application paths.

---

# SEC-001 — Customer Authorization

## Status: ✅ Mitigated

### Before

```text
Alice
  ↓
CUST002
  ↓
Customer returned ❌
```

### Control

Object-level authorization.

### After

```text
Alice → CUST001 → ALLOW
Alice → CUST002 → DENY

Bob   → CUST001 → DENY
Bob   → CUST002 → ALLOW
```

---

# SEC-002 — Cross-User RAG Retrieval

## Status: ✅ Mitigated

### Before

```text
Alice
  ↓
Semantic Search
  ↓
Bob-owned document
  ↓
LLM Context ❌
```

### Control

Authorization is applied before semantic retrieval.

```text
Alice
  ↓
public + alice documents only
  ↓
Chroma
```

---

# SEC-003 — Indirect Prompt Injection

## Status: 🛡️ Controls Implemented

Authorized documents may still contain malicious instructions.

Controls include:

```text
Retrieved Document
       │
       ▼
Content Scanner
       │
   ┌───┴────┐
   │        │
 BLOCK    PASS
            │
            ▼
       Mark UNTRUSTED
            │
            ▼
           LLM
```

Safe retrieved content is not promoted to trusted instructions.

Residual risk remains for novel or semantically obfuscated attacks.

---

# SEC-004 — Session Memory Leakage

## Status: ✅ Mitigated

### Before

```text
Alice ──┐
        ▼
      default
        ▲
Bob ────┘

❌
```

### After

```text
Alice → user:alice:default

Bob   → user:bob:default
```

Regression tests verify cross-user conversation isolation.

---

# SEC-007 — High-Impact Action Without Approval

## Status: ✅ Mitigated

### Before

```text
Agent
  ↓
create_transfer()
  ↓
SIMULATED_EXECUTED ❌
```

### After

```text
Agent
  ↓
Human Approval
  │
  ├── Reject → STOP
  │
  └── Approve
         ↓
      Authorization
         ↓
      Execution
```

---

# SEC-008 — Transfer Authorization

## Status: ✅ Mitigated

### Before

```text
Alice
  ↓
Transfer from CUST002
  ↓
EXECUTED ❌
```

### After

```text
Alice
  ↓
transfer:create
  ↓
CUST002 authorization
  ↓
DENY
  ↓
No side effect ✅
```

---

# SEC-009 — Direct Prompt Security

## Status: 🛡️ Mitigated for configured rules

The application detects several direct prompt attack patterns, including:

- Instruction override
- Role override
- Security bypass
- System-prompt extraction
- Human-approval bypass

High-confidence rules are blocked before the prompt reaches the model.

```text
User Prompt
     │
     ▼
Prompt Scanner
     │
     ▼
Policy
  ┌──┴─────┐
  │        │
BLOCK    ALLOW
  │        │
 STOP      ▼
          LLM
```

A controlled internal canary is also scanned in model output.

Prompt injection is not considered completely solved.

---

# Security Tests

The deterministic pytest suite currently covers:

```text
Customer object authorization                ✅
RAG authorization                            ✅
RAG content security                         ✅
Session isolation                            ✅
Transfer authorization                       ✅
Human approval controls                      ✅
Direct prompt enforcement                    ✅
Controlled output leakage                    ✅
Tool permission callbacks                    ✅
Least-privilege tool exposure                ✅
Customer-ID schema                           ✅
Destination-account schema                   ✅
Transfer amount schema                       ✅
RAG query schema                             ✅
Generated agent tool schemas                 ✅
Invalid transfer side effects                ✅
```

Run all tests:

```powershell
python -m pytest -v
```

Run tool-access tests:

```powershell
python -m pytest tests/security/test_tool_access.py -v
```

Run schema tests:

```powershell
python -m pytest tests/security/test_tool_schemas.py -v
```

---

# Current Attack Matrix

| ID | Threat | Control | Evidence |
|---|---|---|---|
| SEC-001 | Cross-customer lookup | Object authorization | pytest ✅ |
| SEC-002 | Cross-user RAG retrieval | Retrieval ACL | pytest ✅ |
| SEC-003 | Indirect RAG prompt injection | Scan + trust boundary | pytest ✅ |
| SEC-004 | Cross-session leakage | User-bound sessions | pytest ✅ |
| SEC-007 | Autonomous high-impact transfer | HITL | pytest + CLI ✅ |
| SEC-008 | Unauthorized transfer | Action + object AuthZ | pytest ✅ |
| SEC-009 | Direct prompt injection | Input policy + output scan | pytest ✅ |
| SEC-010 | Excessive tool exposure | Permission-scoped tool set | pytest ✅ |
| SEC-011 | Malformed tool arguments | Structured schemas | pytest ✅ |

---

# Git Security Evolution

Tags represent significant hardened security checkpoints.

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
```

---

# Development Roadmap

## Customer Authorization

- [x] Create vulnerable customer lookup
- [x] Reproduce cross-customer access
- [x] Add deterministic tests
- [x] Enforce authorization
- [x] Retest

---

## Multi-Tool Agent

- [x] Add multiple independent tools
- [x] Demonstrate multi-tool behavior

---

## RAG Authorization

- [x] Add Chroma RAG
- [x] Add document ownership
- [x] Reproduce unauthorized retrieval
- [x] Add tests
- [x] Enforce retrieval ACL
- [x] Retest

---

## Indirect Prompt Injection

- [x] Add malicious retrieved content
- [x] Reproduce risk
- [x] Add content scanner
- [x] Add explicit untrusted boundary
- [x] Add behavioral rules
- [x] Add regression tests
- [x] Document residual risk

---

## Session and Memory Isolation

- [x] Add persistent memory
- [x] Introduce shared-session vulnerability
- [x] Reproduce cross-user leakage
- [x] Implement per-user sessions
- [x] Add regression tests

---

## Tool Abuse / Excessive Agency

- [x] Add simulated transfer tool
- [x] Demonstrate excessive agency
- [x] Reproduce transfer authorization failure
- [x] Add action authorization
- [x] Add object authorization
- [x] Add HITL approval
- [x] Test approve/reject paths
- [x] Prevent unauthorized side effects

---

## Direct Prompt Injection / System-Prompt Extraction

- [x] Add controlled security canary
- [x] Create vulnerable detection-only baseline
- [x] Add direct prompt scanner
- [x] Add enforcement policy
- [x] Block configured high-confidence attacks
- [x] Add controlled output scanner
- [x] Add regression tests
- [x] Document residual risk

---

## Tool Access / Least Privilege

- [x] Add `customer:read`
- [x] Add `document:read`
- [x] Add `transfer:create`
- [x] Dynamically enable tools based on caller permissions
- [x] Verify disabled tools are not exposed to the agent
- [x] Test least-privilege combinations
- [x] Preserve business-logic authorization for high-impact transfer actions

---

## Structured Tool-Call and Input Validation

- [x] Add `CustomerId` schema
- [x] Add `DestinationAccount` schema
- [x] Add `TransferAmountCHF` schema
- [x] Add `DocumentSearchQuery` schema
- [x] Enforce customer-ID format
- [x] Enforce simulated-account format
- [x] Enforce CHF transfer range at tool boundary
- [x] Enforce RAG query length
- [x] Test generated agent schemas
- [x] Test invalid inputs
- [x] Verify rejected transfers produce no side effect
- [x] Release `v0.8-tool-access-validation-controls`

---

## Output Validation / Sensitive-Data Controls — NEXT

- [ ] Expand beyond the system-prompt canary
- [ ] Identify fields considered sensitive
- [ ] Test role-dependent disclosure
- [ ] Evaluate output redaction
- [ ] Minimize error-detail leakage
- [ ] Verify output remains inside caller authorization scope
- [ ] Add deterministic regression tests

---

## Rate Limiting / Resource Abuse

- [ ] Add per-user request limits
- [ ] Demonstrate repeated expensive RAG/LLM requests
- [ ] Reject abusive traffic
- [ ] Log rejected activity
- [ ] Add tests

---

## Security Logging and Audit Trail

- [ ] Replace development `print()` logs with structured events
- [ ] Record authenticated user
- [ ] Record session
- [ ] Record tool
- [ ] Record authorization decision
- [ ] Record validation failure
- [ ] Record approval result
- [ ] Record prompt-security decision
- [ ] Record RAG source
- [ ] Avoid unnecessary sensitive-data logging

---

## Automated Security / Red-Team Testing

### Deterministic pytest

Continue testing:

- Authorization
- Least privilege
- RAG security
- Session isolation
- HITL
- Prompt controls
- Tool schemas
- Output controls
- Rate limiting

### Probabilistic testing

Introduce Promptfoo for:

- Direct prompt injection
- Indirect prompt injection
- Jailbreaking
- System-prompt extraction
- Tool manipulation
- Approval manipulation
- Sensitive-data extraction
- Obfuscated and semantic variants

---

## Threat Model

- [ ] Architecture diagram
- [ ] Trust boundaries
- [ ] Assets
- [ ] Entry points
- [ ] STRIDE analysis
- [ ] OWASP LLM / GenAI mapping
- [ ] Threat → control mapping
- [ ] Residual-risk analysis

---

## Attack / Finding Documentation

Current findings:

```text
SEC-001 Customer authorization
SEC-002 RAG authorization
SEC-003 Indirect prompt injection
SEC-004 Session isolation
SEC-007 Missing HITL
SEC-008 Transfer authorization
SEC-009 Direct prompt security
SEC-010 Tool access / least privilege
SEC-011 Tool argument validation
```

Each finding documents:

```text
Security requirement
Attack
Expected behavior
Vulnerable behavior
Root cause
Mitigation
Regression test
Post-control result
Residual risk
```

---

# Security Engineering Methodology

Each control follows the same engineering lifecycle:

```text
1. Define security property
        ↓
2. Build / identify vulnerable state
        ↓
3. Reproduce the attack
        ↓
4. Add security test
        ↓
5. Determine root cause
        ↓
6. Implement control
        ↓
7. Repeat original attack
        ↓
8. Run regression suite
        ↓
9. Document residual risk
```

Git history preserves the evolution from vulnerable implementation to hardened state.

---

# Next Milestone

The next planned phase is:

## Output Validation / Sensitive-Data Controls

The project currently has one narrow output-security control:

```text
POLICY-CANARY-7F3A92
```

The next phase expands the question from:

```text
"Did the model leak its controlled system marker?"
```

to:

```text
"Could the final response expose information
the caller should not receive?"
```

Potential controls include:

```text
Tool Result
    │
    ▼
Authorization
    │
    ▼
LLM
    │
    ▼
Output Security
    │
 ┌──┴────┐
 │       │
SAFE   SENSITIVE
 │       │
 ▼       ▼
User   REDACT / BLOCK
```

This phase will focus on:

- Sensitive fields
- Role-based disclosure
- Authorization-scoped output
- Error-detail minimization
- Redaction where appropriate

---

# Final Objective

The completed project will demonstrate agentic-AI security across:

```text
Agent
├── Prompt security
├── Least-privilege tool access
├── Tool authorization
├── Human approval
└── Structured tool validation

RAG
├── Retrieval authorization
├── Indirect prompt injection
├── Content trust
└── Poisoning

Memory
├── Session isolation
└── Cross-user leakage

Application
├── Input validation
├── Output validation
├── Rate limiting
├── Logging
└── Auditability

Testing
├── Deterministic pytest controls
└── Probabilistic LLM red teaming

Threat Modelling
├── STRIDE
├── OWASP LLM / GenAI
└── Residual risk
```

The objective is not simply to build a functioning AI agent.

It is to demonstrate:

> **how authorization, least privilege, validation, approval, trust boundaries, and model-specific defenses combine to reduce the attack surface of an agentic AI application — and how each control can be tested independently.**