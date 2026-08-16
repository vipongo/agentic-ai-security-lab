# Agentic AI Security Lab

A hands-on security engineering project focused on identifying, exploiting, and mitigating security risks in LLM-based agentic applications.

The project implements a small enterprise-style AI agent with access to tools and sensitive mock data. The application is deliberately developed through vulnerable and hardened iterations so that security issues can be reproduced, tested, mitigated, and documented.

The objective is to demonstrate practical AI security engineering across:

* Agent tool security
* Authorization and least privilege
* Prompt injection
* Indirect prompt injection
* RAG security
* Sensitive information disclosure
* Cross-user and cross-session isolation
* Excessive agency
* Human-in-the-loop controls
* Security testing and red teaming
* STRIDE and LLM threat modelling

> **Important:** All users, customers, accounts, and financial information in this repository are fictional test data.

---

# Project Goal

The final architecture will represent a simplified enterprise AI assistant:

```text
User
 │
 ▼
AI Agent / LLM
 │
 ├───────────────┬────────────────┬────────────────┐
 ▼               ▼                ▼                ▼
Customer Tool    Calculator       RAG Search       High-impact Tools
 │                                │
 ▼                                ▼
Mock Data                        Vector DB
```

Security controls will progressively be introduced around the agent and its tools:

```text
Authentication
      │
Authorization
      │
Agent / LLM
      │
Tool allowlisting
      │
Tool argument validation
      │
Retrieval authorization
      │
Human approval
      │
Output validation
      │
Audit logging
```

The project follows a deliberate lifecycle:

```text
Build
  ↓
Exploit
  ↓
Document
  ↓
Mitigate
  ↓
Retest
```

The intention is not to rely solely on LLM instructions or prompt-based guardrails.

Security-sensitive decisions such as authorization are enforced using deterministic application logic outside the LLM.

---

# Current Status

## Version: Authorization Controls Implemented

The project currently includes:

* A working OpenAI-based AI agent
* Two mock application users
* Two mock banking customers
* Trusted application context representing the authenticated user
* A customer lookup tool
* Deterministic object-level authorization
* Automated authorization security tests
* A second calculator tool
* Multi-tool agent behavior

The first identified security issue, **SEC-001**, has been reproduced, tested, and mitigated.

Current development stage:

```text
Vulnerable customer lookup
          │
          ▼
Security test created
          │
          ▼
Authorization bypass reproduced
          │
          ▼
Authorization control implemented
          │
          ▼
Security regression tests passing
          │
          ▼
Second agent tool added
          │
          ▼
CURRENT STATE
```

The next major development phase will introduce **Retrieval-Augmented Generation (RAG)** and its associated security risks.

---

# Current Architecture

```text
                         User
                          │
                          ▼
                    AI Agent / LLM
                          │
                 ┌────────┴─────────┐
                 │                  │
                 ▼                  ▼
          get_customer()     calculate_percentage()
                 │
                 ▼
          lookup_customer()
                 │
                 ▼
       Authorization Check
                 │
          ┌──────┴──────┐
          │             │
        ALLOW          DENY
          │             │
          ▼             ▼
   customers.json   ACCESS DENIED
```

The authenticated user is stored in an application-side context:

```text
AppContext
 │
 ├── username
 ├── user_id
 ├── role
 └── authorized_customer_ids
```

This context is used by deterministic application code when deciding whether access to a customer should be granted.

The LLM does **not** make the authorization decision.

---

# Mock Authorization Model

Two fictional users currently exist:

| User  | Role    | Authorized customer |
| ----- | ------- | ------------------- |
| Alice | Advisor | `CUST001`           |
| Bob   | Advisor | `CUST002`           |

Authorization matrix:

| User  | CUST001 | CUST002 |
| ----- | ------- | ------- |
| Alice | Allow   | Deny    |
| Bob   | Deny    | Allow   |

This matrix is now enforced by application logic.

---

# Security Finding SEC-001

## Missing Object-Level Authorization in Customer Lookup

### Original Vulnerability

The first implementation of the customer lookup tool checked only whether the requested customer existed.

It did **not** verify whether the authenticated user was authorized to access that customer.

This allowed the following scenario:

```text
Authenticated user: Alice

Alice authorized customers:
    CUST001

Requested:
    CUST002

Result:
    CUST002 customer data returned
```

This represented an object-level authorization failure and cross-user sensitive information disclosure.

---

# SEC-001 Attack Flow

Before mitigation:

```text
Alice
 │
 │ "Show me CUST002"
 ▼
AI Agent
 │
 ▼
get_customer("CUST002")
 │
 ▼
lookup_customer()
 │
 ▼
customers.json
 │
 ▼
CUST002 returned
 │
 ▼
❌ UNAUTHORIZED DATA DISCLOSURE
```

The vulnerability existed because the requested `customer_id` was accepted without checking it against the authenticated user's authorized customer list.

---

# SEC-001 Security Control

Authorization is now implemented inside the deterministic customer lookup logic.

Conceptually:

```python
if customer_id not in context.authorized_customer_ids:
    return "ACCESS DENIED"
```

The resulting flow is:

```text
Alice
 │
 │ "Show me CUST002"
 ▼
AI Agent
 │
 ▼
get_customer("CUST002")
 │
 ▼
lookup_customer()
 │
 ▼
Authorization Check
 │
 ├── User: Alice
 ├── Authorized: CUST001
 └── Requested: CUST002
          │
          ▼
     ACCESS DENIED
```

The important design principle is:

> **Authorization is enforced outside the LLM.**

Even if the LLM is manipulated into requesting an unauthorized resource, the application-level security control denies access.

---

# Why Authorization Is Not Implemented in the Prompt

An insecure design might rely on instructions such as:

```text
Only retrieve customers that the current user is authorized to access.
```

This project deliberately does not treat such instructions as an authorization control.

LLMs can potentially be manipulated through:

* Direct prompt injection
* Indirect prompt injection
* Jailbreaking
* Malicious retrieved content
* Tool-use manipulation

The security architecture therefore assumes that the LLM may attempt unauthorized actions.

The target model is:

```text
Attacker
   │
   │ malicious instruction
   ▼
LLM
   │
   │ potentially compromised
   ▼
get_customer("CUST002")
   │
   ▼
Application Authorization
   │
   ▼
ACCESS DENIED
```

A central security principle of this project is therefore:

> **LLM instructions and guardrails are not authorization controls.**

---

# Security Tests

The authorization control is covered by deterministic automated tests.

Current test matrix:

| Test            | Expected result |
| --------------- | --------------- |
| Alice → CUST001 | Allowed         |
| Alice → CUST002 | Denied          |
| Bob → CUST001   | Denied          |
| Bob → CUST002   | Allowed         |

Example:

```python
def test_alice_cannot_access_bobs_customer():

    alice = get_user_context("alice")

    result = lookup_customer(
        context=alice,
        customer_id="CUST002"
    )

    assert result == "ACCESS DENIED"
```

Run the security test suite with:

```bash
python -m pytest -v
```

Current expected result:

```text
test_alice_can_access_her_customer PASSED
test_alice_cannot_access_bobs_customer PASSED
test_bob_can_access_his_customer PASSED
test_bob_cannot_access_alices_customer PASSED
```

The same test that previously exposed the vulnerability now verifies that the mitigation remains effective.

---

# Multi-Tool Agent

The agent now has access to more than one capability.

Current tools:

```text
Agent
 │
 ├── get_customer()
 │
 └── calculate_percentage()
```

This allows the LLM to perform multi-step reasoning involving tool selection.

Example:

```text
User:

What is 10% of CUST001's portfolio?
```

Possible agent execution:

```text
get_customer("CUST001")
        │
        ▼
portfolio_value = 250000
        │
        ▼
calculate_percentage(
    value=250000,
    percentage=10
)
        │
        ▼
25000
        │
        ▼
Assistant:
CHF 25,000
```

This prepares the architecture for later testing of:

* Tool selection
* Tool allowlisting
* Tool argument manipulation
* Excessive agency
* Least-privilege tool design
* High-impact tool invocation

---

# Current Project Structure

```text
agentic-ai-security-lab/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── agent.py
│   ├── context.py
│   ├── data_loader.py
│   │
│   └── tools/
│       ├── __init__.py
│       ├── customer.py
│       └── calculator.py
│
├── data/
│   ├── users.json
│   └── customers.json
│
├── tests/
│   └── security/
│       └── test_customer_authorization.py
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

# Running the Application

Create a Python virtual environment:

```powershell
py -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Set the OpenAI API key:

```powershell
$env:OPENAI_API_KEY = "YOUR_API_KEY"
```

Run as Alice:

```powershell
python -m app.main --user alice
```

Run as Bob:

```powershell
python -m app.main --user bob
```

---

# Testing Authorization Manually

Run:

```powershell
python -m app.main --user alice
```

Legitimate request:

```text
Show me all information about CUST001.
```

Expected:

```text
Customer information returned.
```

Unauthorized request:

```text
Show me all information about CUST002.
```

Expected:

```text
Access denied.
```

This demonstrates that authorization is enforced regardless of whether the LLM attempts the tool invocation.

---

# Git Security Evolution

The repository deliberately preserves major security states.

## `v0.1-vulnerable-baseline`

Represents the initial vulnerable implementation.

```text
Alice
  ↓
CUST002
  ↓
Customer data returned
```

SEC-001 can be reproduced in this version.

---

## `v0.2-authz-controls`

Represents the current authorization-hardened architecture.

```text
Alice
  ↓
CUST002
  ↓
Authorization check
  ↓
ACCESS DENIED
```

This version contains:

* Object-level authorization
* Authorization regression tests
* Multi-tool agent functionality

---

## Planned Tags

```text
v0.1-vulnerable-baseline
v0.2-authz-controls
v0.3-secure-rag
v0.4-agent-guardrails
v1.0-final
```

Tags represent major security architecture states rather than individual development milestones.

---

# Development Roadmap

## Phase 1 — Agent and Authorization Baseline

* [x] Create project structure
* [x] Create mock users
* [x] Create mock customer data
* [x] Implement application context
* [x] Implement basic AI agent
* [x] Implement customer lookup tool
* [x] Create intentionally vulnerable authorization baseline
* [x] Add first security test
* [x] Reproduce cross-customer authorization bypass
* [x] Enforce object-level authorization
* [x] Add authorization matrix tests
* [x] Retest SEC-001

## Phase 2 — Additional Agent Tools

* [x] Add calculator tool
* [x] Demonstrate multi-tool agent behavior
* [ ] Evaluate least-privilege tool design

## Phase 3 — RAG

* [ ] Add document dataset
* [ ] Add document ingestion
* [ ] Add vector database
* [ ] Implement document search tool
* [ ] Add public and user-specific documents
* [ ] Demonstrate cross-user retrieval
* [ ] Implement retrieval authorization

## Phase 4 — Prompt Injection and RAG Poisoning

* [ ] Direct prompt injection testing
* [ ] Indirect prompt injection testing
* [ ] Add malicious RAG document
* [ ] Demonstrate RAG poisoning
* [ ] System-prompt extraction attempts
* [ ] Separate trusted instructions from untrusted retrieved content

## Phase 5 — Agent Security

* [ ] Introduce high-impact simulated tool
* [ ] Test unauthorized tool invocation
* [ ] Test excessive agency
* [ ] Add tool allowlisting
* [ ] Add structured argument validation
* [ ] Add human approval for sensitive actions

## Phase 6 — Memory and Session Security

* [ ] Add conversation sessions
* [ ] Demonstrate cross-session leakage
* [ ] Implement per-user session isolation
* [ ] Test memory poisoning scenarios

## Phase 7 — Defensive Controls

* [ ] Input validation
* [ ] Output validation
* [ ] Rate limiting
* [ ] Audit logging
* [ ] Content filtering
* [ ] Retrieval ACLs
* [ ] Least-privilege tool scopes

## Phase 8 — Automated AI Red Teaming

* [ ] Expand pytest security regression suite
* [ ] Add Promptfoo
* [ ] Automate adversarial prompts
* [ ] Compare attack success before and after controls

## Phase 9 — Threat Model

* [ ] Architecture diagram
* [ ] Identify assets
* [ ] Identify trust boundaries
* [ ] STRIDE analysis
* [ ] LLM-specific threat analysis
* [ ] Map threats to security controls

---

# Planned Attack Scenarios

| ID      | Threat                              | Target           | Status      |
| ------- | ----------------------------------- | ---------------- | ----------- |
| SEC-001 | Cross-customer authorization bypass | Customer tool    | ✅ Mitigated |
| SEC-002 | Direct prompt injection             | Agent            | Planned     |
| SEC-003 | Indirect prompt injection           | RAG              | Planned     |
| SEC-004 | Sensitive information disclosure    | Agent / tools    | Planned     |
| SEC-005 | RAG authorization bypass            | Retriever        | Planned     |
| SEC-006 | RAG poisoning                       | Knowledge base   | Planned     |
| SEC-007 | Unauthorized tool invocation        | Agent            | Planned     |
| SEC-008 | Excessive agency                    | High-impact tool | Planned     |
| SEC-009 | Cross-session data leakage          | Memory           | Planned     |
| SEC-010 | System prompt extraction            | Agent            | Planned     |
| SEC-011 | Malicious tool arguments            | Tools            | Planned     |
| SEC-012 | Resource abuse / rate-limit bypass  | API              | Planned     |

The list will evolve as the architecture grows.

---

# Security Engineering Methodology

Each security issue follows the same lifecycle:

```text
1. Define the expected security property
2. Build or identify the vulnerable implementation
3. Create an attack scenario
4. Reproduce the vulnerability
5. Write an automated security test
6. Identify the root cause
7. Implement the security control
8. Run the same attack again
9. Verify regression tests pass
10. Document the result
```

This methodology allows Git history to preserve both vulnerable and secured implementations.

---

# Current Security Result

## SEC-001

### Before

```text
Alice
  ↓
Request CUST002
  ↓
Customer data returned

❌ VULNERABLE
```

### Control

```text
Deterministic object-level authorization
```

### After

```text
Alice
  ↓
Request CUST002
  ↓
Authorization check
  ↓
ACCESS DENIED

✅ MITIGATED
```

---

# Next Milestone

The next major component will be **Retrieval-Augmented Generation (RAG)**.

The agent will gain a new tool:

```text
search_documents()
```

The architecture will evolve into:

```text
                    Agent
                      │
           ┌──────────┼───────────┐
           │          │           │
           ▼          ▼           ▼
     Customer      Calculator    RAG Search
       Tool           Tool          Tool
           │                       │
           ▼                       ▼
     Mock Customer              Vector DB
        Data
```

The RAG implementation will initially introduce deliberate security weaknesses so that the project can demonstrate:

* Cross-user document retrieval
* Retrieval authorization failures
* Indirect prompt injection
* RAG poisoning
* Untrusted content handling

The same **vulnerable → exploit → mitigate → retest** methodology will then be applied to the RAG pipeline.

---

# Final Objective

The final project will demonstrate an agentic application in which the LLM is treated as an **untrusted decision-making component rather than a security boundary**.

The project applies established application-security principles such as:

* Authentication
* Authorization
* Least privilege
* Input validation
* Trust boundaries
* Auditability
* Separation of duties
* Defense in depth

to modern AI-specific components including:

* LLM agents
* Tool invocation
* Retrieval-Augmented Generation
* Vector databases
* Agent memory
* Human-in-the-loop workflows

The final repository will include:

* Working source code
* Vulnerable historical baselines
* Exploit scenarios
* Automated security tests
* Defensive implementations
* Before/after results
* Architecture documentation
* STRIDE threat model
* LLM-specific threat model
* Automated red-team methodology
* Lessons learned
