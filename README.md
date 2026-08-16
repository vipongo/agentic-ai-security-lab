# Agentic AI Security Lab

A hands-on security engineering project focused on identifying, exploiting, and mitigating security risks in LLM-based agentic applications.

The project implements a small enterprise-style AI agent with access to tools and sensitive mock data. The application is first built with deliberate security weaknesses, then attacked, tested, and progressively hardened.

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

## Project Goal

The final architecture will represent a simplified enterprise AI assistant:

```text
User
 │
 ▼
AI Agent / LLM
 │
 ├───────────────┬────────────────┐
 ▼               ▼                ▼
Customer Tool    RAG Search       Other Tools
 │               │
 ▼               ▼
Mock Data        Vector DB
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

Security-sensitive decisions such as authorization must be enforced by deterministic application logic outside the LLM.

---

# Current Status

## Version: Vulnerable Baseline

The current implementation contains:

* A basic OpenAI-based AI agent
* Two mock application users
* Two mock banking customers
* Application context representing the authenticated user
* A `get_customer` agent tool
* Deterministic customer lookup logic
* An initial automated security test
* An intentionally missing object-level authorization control

The current version is **deliberately vulnerable**.

---

# Current Architecture

```text
                User
                 │
                 │
                 ▼
            AI Agent / LLM
                 │
                 │ tool call
                 ▼
           get_customer()
                 │
                 ▼
         lookup_customer()
                 │
                 ▼
          customers.json
```

The authenticated application user is held separately in an `AppContext`:

```text
AppContext
 │
 ├── username
 ├── user_id
 ├── role
 └── authorized_customer_ids
```

At the current stage, this authorization information exists but is **not yet enforced by the customer lookup logic**.

This is intentional so that the vulnerability can first be reproduced and tested.

---

# Mock Authorization Model

Two users currently exist.

| User  | Role    | Authorized customer |
| ----- | ------- | ------------------- |
| Alice | Advisor | `CUST001`           |
| Bob   | Advisor | `CUST002`           |

Expected authorization matrix:

| User  | CUST001 | CUST002 |
| ----- | ------- | ------- |
| Alice | Allow   | Deny    |
| Bob   | Deny    | Allow   |

The vulnerable implementation currently does not enforce this matrix.

---

# Security Finding SEC-001

## Missing Object-Level Authorization in Customer Lookup

### Description

The `get_customer` agent tool allows the LLM to request a customer by customer ID.

The underlying lookup implementation currently verifies only whether the customer exists.

It does **not** verify whether the authenticated application user is authorized to access that customer.

### Example

Alice is authenticated with:

```text
authorized_customer_ids = ["CUST001"]
```

Alice should therefore be able to retrieve:

```text
CUST001
```

but should not be able to retrieve:

```text
CUST002
```

The current vulnerable implementation allows:

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
CUST002 data returned
```

### Security Impact

This represents an object-level authorization failure that could result in cross-user sensitive information disclosure.

In a real application, an attacker could potentially convince an LLM agent to access objects belonging to another user even though the attacker does not possess the required authorization.

---

# Security Test

An automated security test has been added for SEC-001.

The security requirement is:

```text
Alice + CUST002
       ↓
ACCESS DENIED
```

However, the vulnerable implementation currently returns customer data instead.

The test is therefore intentionally marked with `pytest.mark.xfail`.

Running:

```bash
python -m pytest -v
```

currently produces an expected failure:

```text
test_alice_cannot_access_bobs_customer XFAIL
```

This documents that the vulnerability is:

1. Known
2. Reproducible
3. Covered by a security regression test

---

# Running the Current Application

Create and activate a Python virtual environment.

Windows PowerShell:

```powershell
py -m venv .venv
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

Run the application as Alice:

```powershell
python -m app.main --user alice
```

Or as Bob:

```powershell
python -m app.main --user bob
```

---

# Reproducing SEC-001

Run the application as Alice:

```powershell
python -m app.main --user alice
```

First request Alice's authorized customer:

```text
Show me all information about CUST001.
```

This request is legitimate.

Then request Bob's customer:

```text
Show me all information about CUST002.
```

In the current vulnerable baseline, this request is also fulfilled.

That behavior demonstrates SEC-001.

---

# Running Security Tests

Run:

```powershell
python -m pytest -v
```

The current baseline intentionally contains an expected failing authorization test.

Future secure versions will remove the `xfail` marker once authorization enforcement is implemented.

---

# Development Roadmap

## Phase 1 — Agent and Tool Baseline

* [x] Create project structure
* [x] Create mock users
* [x] Create mock customer data
* [x] Implement application context
* [x] Implement basic AI agent
* [x] Implement customer lookup tool
* [x] Create intentionally vulnerable authorization baseline
* [x] Add first security test
* [ ] Enforce object-level authorization
* [ ] Retest SEC-001

## Phase 2 — Additional Agent Tools

* [ ] Add calculator tool
* [ ] Demonstrate multi-tool agent behavior
* [ ] Introduce least-privilege tool design

## Phase 3 — RAG

* [ ] Add document ingestion
* [ ] Add vector database
* [ ] Implement document search tool
* [ ] Add user-specific documents
* [ ] Demonstrate cross-user retrieval
* [ ] Implement retrieval authorization

## Phase 4 — Prompt Injection and RAG Poisoning

* [ ] Direct prompt injection testing
* [ ] Indirect prompt injection testing
* [ ] Malicious RAG document
* [ ] RAG poisoning scenario
* [ ] System-prompt extraction attempts
* [ ] Separate trusted instructions from untrusted retrieved content

## Phase 5 — Agent Security

* [ ] Introduce high-impact simulated tool
* [ ] Test excessive agency
* [ ] Add tool allowlisting
* [ ] Add structured argument validation
* [ ] Add deterministic authorization
* [ ] Add human approval for sensitive actions

## Phase 6 — Memory and Session Security

* [ ] Add conversation sessions
* [ ] Test cross-session leakage
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

* [ ] Add pytest security regression suite
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

| ID      | Threat                              | Target           |
| ------- | ----------------------------------- | ---------------- |
| SEC-001 | Cross-customer authorization bypass | Customer tool    |
| SEC-002 | Direct prompt injection             | Agent            |
| SEC-003 | Indirect prompt injection           | RAG              |
| SEC-004 | Sensitive information disclosure    | Agent / tools    |
| SEC-005 | RAG authorization bypass            | Retriever        |
| SEC-006 | RAG poisoning                       | Knowledge base   |
| SEC-007 | Unauthorized tool invocation        | Agent            |
| SEC-008 | Excessive agency                    | High-impact tool |
| SEC-009 | Cross-session data leakage          | Memory           |
| SEC-010 | System prompt extraction            | Agent            |
| SEC-011 | Malicious tool arguments            | Tools            |
| SEC-012 | Resource abuse / rate-limit bypass  | API              |

The list will evolve as the architecture becomes more complex.

---

# Security Engineering Approach

Each identified security issue will follow the same methodology:

```text
1. Define the expected security property
2. Build or identify the vulnerable implementation
3. Create an attack scenario
4. Reproduce the vulnerability
5. Write an automated security test
6. Identify the root cause
7. Implement the security control
8. Run the same attack again
9. Verify the regression test passes
10. Document the result
```

This allows Git history to preserve both the vulnerable and secured implementations.

---

# Final Objective

The final project will demonstrate an agentic application in which the LLM is treated as an **untrusted decision-making component rather than a security boundary**.

The goal is to show how conventional application-security principles such as:

* Authentication
* Authorization
* Least privilege
* Input validation
* Trust boundaries
* Auditability
* Separation of duties
* Defense in depth

apply to modern LLM agents, RAG systems, memory, and tool invocation.

The project will ultimately include:

* Working source code
* Vulnerable baselines
* Exploit scenarios
* Automated security tests
* Defensive implementations
* Before/after results
* Architecture documentation
* STRIDE threat model
* LLM-specific threat model
* Red-team methodology
* Lessons learned
