# Agentic AI Security Lab

A hands-on security engineering project for building, attacking, hardening, and reassessing an LLM-based agentic application.

The project implements a simulated internal banking assistant using an agent, Retrieval-Augmented Generation (RAG), persistent memory, external tools, and high-impact actions.

The application was intentionally developed through vulnerable and hardened iterations:

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
Measure residual risk
```

> **Test Data Notice:** All identities, customer records, account information, documents, financial data, and transfers in this repository are fictional and exist solely for security testing. The application does not connect to real banking infrastructure.

---

## Key Results

The project demonstrates security controls across:

- Object-level authorization
- RAG authorization
- Direct and indirect prompt injection
- Session isolation
- Least-privilege tool access
- Structured tool schemas
- High-impact action authorization
- Human-in-the-loop approval
- Rate limiting
- Security audit logging
- Automated adversarial testing
- Threat modelling

Automated Promptfoo red teaming showed:

| Assessment | Attack Success Rate |
|---|---:|
| Initial red-team assessment | **40.35%** |
| Post-remediation assessment | **9.52%** |

```text
40.35%
   │
   │ security remediation
   ▼
 9.52%
```

This represents a **30.83 percentage-point reduction** in observed attack success against the configured adversarial suite.

The complete before/after reports are available under:

```text
/docs/report-promptfoo/
```

The formal threat model is available at:

```text
/docs/threat-model.md
```

---

# Core Security Principle

> **The LLM is not a security boundary.**

The application assumes that the model may:

- Follow malicious user instructions
- Follow malicious retrieved instructions
- Request unauthorized resources
- Select inappropriate tools
- Generate malformed tool arguments
- Attempt high-impact actions
- Expose internal information
- Be influenced by poisoned conversation state

Security-critical decisions therefore remain in deterministic application logic.

```text
             USER
               │
               ▼
        Request Security
               │
               ▼
          LLM / Agent
               │
               ▼
     Least-Privilege Tools
               │
               ▼
      Structured Validation
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

     ─────────────────────
       Security Audit Trail
```

---

# Current Release

## `v0.11-threat-model`

The current release combines the implemented controls with a formal threat model covering:

- System architecture
- Trust boundaries
- Security assets
- Threat actors
- STRIDE analysis
- OWASP Top 10 for LLM Applications mapping
- OWASP Agentic Applications mapping
- Security-finding traceability
- Security invariants
- Residual risks
- Qualitative risk ratings

See:

```text
/docs/threat-model.md
```

---

# Architecture

The application models:

```text
Relationship Manager
        │
        ▼
CLI Application
        │
        ├── Trusted AppContext
        │
        ├── Prompt Security
        │
        ▼
     AI Agent
        │
        ├── get_customer()
        ├── search_documents()
        ├── calculate_percentage()
        └── create_transfer()
        │
        ├── Customer Data
        ├── Chroma RAG
        ├── SQLite Sessions
        ├── Human Approval
        ├── Simulated Transfers
        └── Security Audit Log
```

The detailed Mermaid architecture is maintained in the threat model.

---

# Trust Boundaries

The threat model identifies six primary trust boundaries.

## TB-01 — User → Application

Natural-language identity, role, permission, or approval claims are untrusted.

```text
"I am an administrator"
```

does not modify authenticated application context.

---

## TB-02 — Application → LLM

The LLM is non-deterministic and cannot prove:

```text
identity
authorization
permission
approval
```

These decisions remain application-side.

---

## TB-03 — LLM → Tools

Tool calls originate from model decisions and are untrusted until validated.

Controls include:

- Conditional tool exposure
- Structured schemas
- Input validation
- Permission checks
- Object authorization
- HITL approval

---

## TB-04 — RAG Content → Agent

Retrieved documents are untrusted.

They cannot:

```text
grant permissions
change authorization
approve actions
change security policy
```

---

## TB-05 — Application → Persistent State

Protected state includes:

- Customer data
- Authorization information
- Conversation sessions
- Chroma vector data
- Audit logs
- Simulated transfers

---

## TB-06 — Agent → Human Approval

High-impact model-requested actions cross an explicit human approval boundary.

Human approval does not replace deterministic authorization.

---

# Security Findings

The formal threat model is the canonical source for finding IDs.

| ID | Finding | Primary Control | Status |
|---|---|---|---|
| SEC-001 | Missing customer authorization | Object-level authorization | Remediated |
| SEC-002 | Missing RAG authorization | Metadata retrieval ACL | Remediated |
| SEC-003 | Indirect prompt injection / RAG poisoning | Trust separation + filtering + external AuthZ | Mitigated |
| SEC-004 | Direct prompt injection | External identity/AuthZ + prompt detection | Mitigated |
| SEC-005 | System prompt extraction | No secrets in prompt + detection/output scan | Residual risk |
| SEC-006 | Cross-user session leakage | Per-user session IDs | Remediated |
| SEC-007 | Excessive agency | Human approval | Remediated |
| SEC-008 | Missing transfer authorization | Permission + object AuthZ | Remediated |
| SEC-009 | Purpose limitation | Policy restriction | Open / residual |

Detailed attack descriptions, controls, and residual risks are documented in:

```text
/docs/threat-model.md
```

---

# SEC-001 — Customer Authorization

The vulnerable implementation allowed:

```text
Alice
  ↓
CUST002
  ↓
Bob's customer data
```

The hardened implementation evaluates object authorization using trusted application context.

```text
Alice → CUST001 → ALLOW
Alice → CUST002 → DENY

Bob   → CUST001 → DENY
Bob   → CUST002 → ALLOW
```

---

# SEC-002 — RAG Authorization

Semantic relevance is not authorization.

```text
Relevant
   ≠
Authorized
```

Metadata authorization is applied before semantic retrieval so another user's private documents cannot enter the candidate context.

---

# SEC-003 — Indirect Prompt Injection

Retrieved documents are treated as untrusted data.

```text
RAG Document
     │
     ▼
Authorization
     │
     ▼
Content Security
     │
 ┌───┴────┐
 │        │
BLOCK   UNTRUSTED
          │
          ▼
         LLM
```

Content-based detection remains bypassable, so authorization and tool-security controls remain independent.

---

# SEC-004 — Direct Prompt Injection

Examples include:

```text
Ignore all previous instructions...

You are now an administrator...

Disable authorization...
```

The application separates:

```text
Detection
    ↓
Policy Decision
    ↓
Enforcement
```

Prompt filtering is defense in depth and cannot grant or revoke authorization.

---

# SEC-005 — System Prompt Extraction

A controlled canary is used to test disclosure:

```text
POLICY-CANARY-7F3A92
```

Controls include:

- No real secrets in system instructions
- Prompt-extraction detection
- Output canary detection
- Promptfoo extraction attacks

The finding remains **residual risk** because the model may still infer or paraphrase non-secret behavioral instructions.

---

# SEC-006 — Session Isolation

The vulnerable implementation used shared persistent memory.

```text
Alice ──┐
        ▼
      default
        ▲
Bob ────┘
```

The hardened implementation scopes sessions to authenticated identity:

```text
Alice → user:alice:default

Bob → user:bob:default
```

Conversation memory cannot grant authorization.

---

# SEC-007 — Excessive Agency

The initial transfer capability could execute immediately after model selection.

The hardened flow requires:

```text
Agent Requests Action
        │
        ▼
Human Approval
        │
        ▼
Authorization
        │
        ▼
Validation
        │
        ▼
Rate Limit
        │
        ▼
Simulated Execution
```

---

# SEC-008 — Transfer Authorization

Alice must not be able to transfer funds from Bob's customer.

```text
Alice
  ↓
CUST002
  ↓
DENY
```

Controls include:

```text
transfer:create permission
        +
source-customer authorization
        +
structured validation
```

---

# SEC-009 — Purpose Limitation

Automated red-team testing identified a residual problem beyond traditional authorization:

> A user may be authorized to access banking information but attempt to reuse that information for an unrelated purpose.

This demonstrates:

```text
Authorized access
      ≠
Authorized purpose
```

Purpose limitation remains an open/residual security problem in the current lab.

---

# Least-Privilege Tool Access

Tool exposure is permission-based.

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

A user should expose the agent only to tools required by that user's permissions.

Tool hiding does not replace authorization inside sensitive business operations.

---

# Structured Tool Validation

Agent-facing tools use constrained schemas.

### Customer ID

```text
CUST001        ✅
CUST999        ✅

CUST01         ❌
CUSTABC        ❌
```

### Destination Account

```text
DEMO-ACCOUNT-999       ✅
DEMO-ACCOUNT-123456    ✅

DEMO-ACCOUNT-ABC       ❌
```

### Transfer Amount

```text
CHF 1 – CHF 100,000
```

### RAG Query

```text
2 – 500 characters
```

---

# Rate Limiting

Two local sliding-window controls are implemented.

### Agent Requests

```text
10 requests / 60 seconds / user
```

### Transfer Requests

```text
3 requests / 300 seconds / user
```

Rate limiting occurs before expensive or high-impact processing.

The implementation is intentionally local/in-memory and is not presented as production-grade distributed rate limiting.

---

# Security Audit Trail

Security-relevant application decisions produce structured JSONL events.

Examples include:

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

Audit records contain:

```text
event ID
UTC timestamp
username
event type
outcome
structured details
```

Sensitive raw content is intentionally minimized.

The lab does not claim cryptographic log integrity or tamper-resistant storage.

---

# Automated Red Teaming

## Promptfoo

Promptfoo provides the probabilistic security-testing layer.

```text
pytest
   ↓
Deterministic security invariants


Promptfoo
   ↓
Adversarial LLM behavior
```

The custom provider runs against the real hardened agent and keeps active:

- Application identity
- Authorization
- Request policy
- Prompt security
- Output controls
- RAG controls
- Tool controls
- Session handling

High-impact HITL actions are automatically rejected during automated testing.

---

# Red-Team Coverage

The automated suite includes attacks involving:

- BOLA
- BFLA
- RBAC
- Excessive agency
- Goal hijacking
- PII/API database leakage
- Prompt extraction
- Memory poisoning
- RAG poisoning
- Tool discovery
- Jailbreak strategies

---

# Promptfoo Results

| Assessment | Attack Success Rate |
|---|---:|
| Initial assessment | **40.35%** |
| Post-remediation assessment | **9.52%** |

```text
Initial Red Team
      │
      ▼
40.35%
      │
      ▼
Analyze successful attacks
      │
      ▼
Security remediation
      │
      ▼
Repeat red team
      │
      ▼
9.52%
```

Complete reports:

```text
/docs/report-promptfoo/
```

These scores represent measured attack success against the configured test suite, not a security guarantee.

---

# Threat Model

Phase 21 introduces the formal threat model:

```text
/docs/threat-model.md
```

It contains:

- Architecture diagram
- Trust boundaries
- Asset inventory
- Threat actors
- STRIDE analysis
- OWASP LLM mapping
- OWASP Agentic mapping
- Security finding traceability
- Security invariants
- Residual risks
- Qualitative risk ratings

---

# STRIDE Coverage

The model evaluates threats across:

```text
S — Spoofing
T — Tampering
R — Repudiation
I — Information Disclosure
D — Denial of Service
E — Elevation of Privilege
```

Examples include:

```text
Spoofing
→ Prompt claims another identity

Tampering
→ RAG poisoning / memory poisoning

Repudiation
→ User denies requesting transfer

Information Disclosure
→ Cross-customer/RAG/session leakage

Denial of Service
→ Excessive LLM or transfer requests

Elevation of Privilege
→ Prompt-based admin claims / unauthorized tools
```

---

# OWASP Mapping

The threat model maps the project against both:

```text
OWASP Top 10 for LLM Applications — 2025
```

and:

```text
OWASP Top 10 for Agentic Applications — 2026
```

Relevant areas include:

- Prompt Injection
- Sensitive Information Disclosure
- Data and Model Poisoning
- Improper Output Handling
- Excessive Agency
- System Prompt Leakage
- Vector and Embedding Weaknesses
- Unbounded Consumption
- Agent Goal Hijack
- Tool Misuse
- Identity & Privilege Abuse
- Memory & Context Poisoning
- Human-Agent Trust Exploitation

The project does not claim complete coverage of all categories.

---

# Security Invariants

The threat model formalizes the following invariants.

### Identity

Natural-language input cannot modify authenticated identity.

### Authorization

The LLM never determines whether a user is authorized.

### Retrieval

Unauthorized documents must not enter model context.

### Untrusted Content

Retrieved content cannot grant permissions or approve actions.

### Memory

Conversation state cannot grant authorization.

### Tools

Users expose only tools permitted by their application permissions.

### Sensitive Actions

High-impact operations require authorization and human approval.

### Validation

Tool arguments must pass structured validation.

### Auditing

Security-relevant decisions should generate structured audit events.

### Resource Usage

Users must not have unlimited access to expensive or high-impact operations.

---

# Residual Risks

The threat model explicitly records limitations rather than claiming perfect security.

Current residual risks include:

- Pattern-based prompt defenses can be bypassed
- System instructions may be paraphrased
- Local data is not cryptographically protected against tampering
- Audit logs are not tamper resistant
- Rate limits are process-local
- AI/dependency supply-chain risk is not comprehensively assessed
- Human approvers can be socially engineered
- Model-provider trust and data governance are not fully modeled
- Single-agent architecture does not cover inter-agent attacks
- Transfer execution is simulated
- Purpose limitation remains unresolved

---

# External Model Provider Boundary

Prompts, retrieved context, and tool-related interactions cross from the local application to an external model provider.

The lab therefore uses fictional data exclusively.

A production financial deployment would additionally require:

- Data classification
- Provider risk assessment
- Contractual controls
- Retention policies
- Technical data-protection controls

---

# Testing Strategy

The project deliberately uses two complementary testing approaches.

## Deterministic

```text
pytest
```

Tests properties such as:

- Authorization
- Session isolation
- Tool access
- Validation
- HITL
- Rate limiting
- Audit events
- Side-effect prevention

## Probabilistic

```text
Promptfoo
```

Tests behaviors such as:

- Prompt injection
- Jailbreaking
- Authorization manipulation
- RAG poisoning
- Memory poisoning
- Prompt extraction
- Tool misuse
- Excessive agency

---

# Security Engineering Methodology

Every major security finding follows:

```text
1. Define security property
        ↓
2. Create or identify vulnerable state
        ↓
3. Reproduce attack
        ↓
4. Write regression test
        ↓
5. Identify root cause
        ↓
6. Implement control
        ↓
7. Repeat attack
        ↓
8. Run regression suite
        ↓
9. Measure residual risk
        ↓
10. Document finding
```

Git history preserves vulnerable and hardened checkpoints.

---

# Release History

| Release | Security Milestone |
|---|---|
| `v0.1-vulnerable-baseline` | Initial vulnerable application |
| `v0.2-authz-controls` | Customer object authorization |
| `v0.3-rag-authz-controls` | RAG retrieval authorization |
| `v0.4-rag-injection-controls` | Indirect prompt-injection controls |
| `v0.5-session-isolation-controls` | Per-user conversation isolation |
| `v0.6-transfer-authz-hitl-controls` | Transfer authorization + HITL |
| `v0.7-prompt-security-controls` | Direct prompt/output security |
| `v0.8-tool-access-validation-controls` | Least privilege + tool schemas |
| `v0.9-audit-rate-limit-controls` | Auditability + abuse protection |
| `v0.10-automated-redteam-controls` | Promptfoo red teaming + remediation |
| `v0.11-threat-model` | Formal threat model and risk traceability |

---

# Project Documentation

```text
README.md
│
└── Project overview and security results


/docs/threat-model.md
│
└── Architecture, STRIDE, OWASP mappings,
    findings and residual risk


/docs/report-promptfoo/
│
├── Initial red-team report — 40.35%
└── Post-remediation report — 9.52%
```

---

# Development Status

## Completed

- [x] Customer authorization
- [x] RAG authorization
- [x] Indirect prompt-injection controls
- [x] Session isolation
- [x] Excessive-agency testing
- [x] Transfer authorization
- [x] Human-in-the-loop approval
- [x] Direct prompt security
- [x] System-prompt disclosure testing
- [x] Least-privilege tool access
- [x] Structured tool schemas
- [x] Rate limiting
- [x] Structured audit trail
- [x] Deterministic pytest security suite
- [x] Promptfoo integration
- [x] Initial automated red-team assessment
- [x] Security remediation
- [x] Post-remediation assessment
- [x] Formal threat model
- [x] STRIDE analysis
- [x] OWASP LLM mapping
- [x] OWASP Agentic mapping
- [x] Risk and residual-risk documentation
- [x] Release `v0.11-threat-model`

---

# Remaining Work

## Formal Finding Documentation

Create dedicated documentation for each finding:

```text
SEC-001
SEC-002
SEC-003
SEC-004
SEC-005
SEC-006
SEC-007
SEC-008
SEC-009
```

Each should capture:

```text
Security requirement
Attack
Vulnerable behavior
Security impact
Root cause
Mitigation
Regression test
Post-remediation result
Residual risk
```

## Final GitHub Polish

- [ ] Final architecture screenshots/diagrams
- [ ] Dedicated finding documentation
- [ ] Review Promptfoo reports for environment-specific metadata
- [ ] Setup instructions
- [ ] `.env.example`
- [ ] Dependency documentation
- [ ] Selected test-result examples
- [ ] Lessons learned
- [ ] Final repository cleanup

---

# Final Objective

The project demonstrates practical agentic-AI security engineering across:

```text
Agent
├── Prompt security
├── Least privilege
├── Tool authorization
├── Human approval
├── Structured validation
└── Excessive-agency controls

RAG
├── Retrieval authorization
├── Prompt injection
├── Poisoning
└── Trust separation

Memory
├── Session isolation
└── Context poisoning

Application
├── Authorization
├── Rate limiting
├── Output security
├── Audit logging
└── Side-effect protection

Testing
├── Deterministic pytest regression tests
└── Promptfoo adversarial red teaming

Threat Modelling
├── STRIDE
├── OWASP LLM
├── OWASP Agentic
├── Security invariants
└── Residual-risk analysis
```

The objective is to demonstrate:

> **how an agentic AI system can be systematically attacked, hardened, tested, red-teamed, threat-modeled, and reassessed while keeping deterministic security decisions outside the LLM.**