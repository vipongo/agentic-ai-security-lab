# Agentic AI Security Lab

A hands-on security engineering project focused on identifying, exploiting, and mitigating security risks in LLM-based agentic applications.

The project implements a simplified enterprise-style AI agent with access to tools, sensitive mock customer data, and a Retrieval-Augmented Generation (RAG) knowledge base.

The application is deliberately developed through vulnerable and hardened iterations so that security weaknesses can be:

1. Identified
2. Reproduced
3. Tested
4. Mitigated
5. Retested

> **Important:** All users, customers, documents, accounts, and financial information in this repository are fictional test data.

---

# Project Goal

The target architecture represents a simplified enterprise AI assistant:

```text
User
 │
 ▼
AI Agent / LLM
 │
 ├────────────────┬─────────────────┐
 ▼                ▼                 ▼
Customer Tool     Calculator        RAG Search
 │                                  │
 ▼                                  ▼
Mock Customer Data               Chroma DB
```

Security controls are progressively added around these components.

The development methodology is:

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
```

A core principle of the project is:

> **The LLM is not treated as a security boundary.**

Security-sensitive decisions such as authorization are enforced through deterministic application logic rather than relying solely on system prompts or LLM behavior.

---

# Current Release

## `v0.3-rag-authz-controls`

This release introduces authorization-aware RAG retrieval and mitigates the second major security finding in the project.

Current capabilities include:

* OpenAI-based AI agent
* Multiple agent tools
* Mock authenticated users
* Mock banking customers
* Trusted application context
* Customer object-level authorization
* Calculator functionality
* Chroma vector database
* Document ingestion
* RAG document retrieval
* Document ownership metadata
* Authorization-aware retrieval
* Automated customer authorization tests
* Automated RAG authorization tests

Two security vulnerabilities have now been reproduced and mitigated:

| ID      | Finding                             | Status      |
| ------- | ----------------------------------- | ----------- |
| SEC-001 | Cross-customer authorization bypass | ✅ Mitigated |
| SEC-002 | Cross-user RAG document retrieval   | ✅ Mitigated |

---

# Current Architecture

```text
                             User
                              │
                              ▼
                        AI Agent / LLM
                              │
                 ┌────────────┼────────────┐
                 │            │            │
                 ▼            ▼            ▼
          get_customer()   Calculator   search_documents()
                 │                          │
                 ▼                          ▼
         lookup_customer()         search_documents_logic()
                 │                          │
                 ▼                          ▼
       Authorization Check           ACL Filter
                 │                          │
          ┌──────┴──────┐                   ▼
          │             │              Chroma Query
        ALLOW          DENY                  │
          │             │                   ▼
          ▼             ▼           Authorized Documents
   customers.json   ACCESS DENIED            │
                                             ▼
                                         LLM Context
```

Both customer lookup and RAG retrieval now enforce authorization before protected information is returned to the agent.

---

# Trusted Application Context

Each request runs with trusted application-side context describing the authenticated user.

Conceptually:

```text
AppContext
 │
 ├── username
 ├── user_id
 ├── role
 └── authorized_customer_ids
```

Example:

```text
Alice
└── Authorized customer: CUST001

Bob
└── Authorized customer: CUST002
```

This information is controlled by the application.

The LLM does not decide which customers or documents a user is authorized to access.

---

# Mock Authorization Model

Two fictional users are currently configured:

| User  | Role    | Authorized customer |
| ----- | ------- | ------------------- |
| Alice | Advisor | `CUST001`           |
| Bob   | Advisor | `CUST002`           |

Customer authorization matrix:

| User  | CUST001 | CUST002 |
| ----- | ------- | ------- |
| Alice | ✅ Allow | ❌ Deny  |
| Bob   | ❌ Deny  | ✅ Allow |

The same model is applied to private RAG documents.

Documents can also be marked as public and therefore accessible to both users.

---

# SEC-001 — Cross-Customer Authorization Bypass

## Status: ✅ Mitigated

### Vulnerable Baseline

The first version of the customer lookup functionality validated only that the requested customer existed.

It did not validate whether the authenticated user was authorized to access that customer.

Example:

```text
Authenticated user: Alice
Authorized customer: CUST001

Request:
CUST002

Result:
CUST002 returned

❌ Unauthorized information disclosure
```

---

## Root Cause

The original implementation effectively performed:

```text
Does customer exist?
        │
        ├── YES → return customer
        └── NO  → not found
```

It did not perform:

```text
Does customer exist?
        │
        ▼
Is authenticated user authorized?
        │
        ├── YES → return customer
        └── NO  → deny
```

---

## Mitigation

Authorization is enforced in deterministic customer lookup logic.

Conceptually:

```python
if customer_id not in context.authorized_customer_ids:
    return "ACCESS DENIED"
```

The resulting flow is:

```text
Alice
 │
 │ request CUST002
 ▼
Agent
 │
 ▼
get_customer("CUST002")
 │
 ▼
lookup_customer()
 │
 ▼
Authorization
 │
 ├── User: Alice
 ├── Allowed: CUST001
 └── Requested: CUST002
          │
          ▼
     ACCESS DENIED
```

---

# SEC-001 Tests

The following authorization matrix is automatically tested:

| Test            | Expected |
| --------------- | -------- |
| Alice → CUST001 | Allow    |
| Alice → CUST002 | Deny     |
| Bob → CUST001   | Deny     |
| Bob → CUST002   | Allow    |

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

The tests now pass and act as regression protection for SEC-001.

---

# Multi-Tool Agent

The agent currently exposes three capabilities:

```text
Agent
 │
 ├── get_customer()
 ├── calculate_percentage()
 └── search_documents()
```

This allows the model to decide which capability is required for a request.

For example:

```text
User:
What is 10% of CUST001's portfolio?
```

The agent can perform:

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
```

Future milestones will use this multi-tool architecture to investigate tool abuse, excessive agency, least privilege, and human approval.

---

# Retrieval-Augmented Generation

The application now includes a RAG pipeline backed by Chroma.

```text
User Question
      │
      ▼
AI Agent
      │
      ▼
search_documents()
      │
      ▼
search_documents_logic()
      │
      ▼
Chroma Vector Search
      │
      ▼
Relevant Documents
      │
      ▼
LLM Context
      │
      ▼
Answer
```

Documents include metadata describing their ownership.

For example:

```text
customer_CUST001.md
├── owner: alice
└── customer_id: CUST001

customer_CUST002.md
├── owner: bob
└── customer_id: CUST002
```

Public documents can use:

```text
owner: public
```

This metadata forms part of the retrieval authorization model.

---

# SEC-002 — Cross-User RAG Document Retrieval

## Status: ✅ Mitigated

### Vulnerable Baseline

The initial RAG implementation performed semantic similarity search across the entire vector collection.

Conceptually:

```text
Search documents
WHERE semantic_similarity = high
```

No authorization condition was applied.

This meant that Alice could explicitly search for information related to:

```text
CUST002
```

and retrieve a Bob-owned document.

---

# SEC-002 Attack Flow

The vulnerable architecture allowed:

```text
Alice
 │
 │ "Find information about CUST002"
 ▼
Agent
 │
 ▼
search_documents()
 │
 ▼
Chroma
 │
 │ semantic search
 │
 │ no authorization filter
 ▼
Bob-owned document
 │
 ▼
LLM context
 │
 ▼
❌ CROSS-USER INFORMATION DISCLOSURE
```

The issue occurred even though Alice's trusted application context correctly identified only:

```text
CUST001
```

as authorized.

---

# SEC-002 Root Cause

The vector database was filtering documents according to:

```text
relevance
```

but not:

```text
authorization
```

These are independent properties.

A highly relevant document is not necessarily an authorized document.

```text
Semantic relevance
        ≠
Authorization
```

The original retrieval behaved conceptually as:

```text
Retrieve
WHERE similarity = high
```

The secure retrieval must behave as:

```text
Retrieve
WHERE similarity = high
AND
document is authorized
```

---

# SEC-002 Mitigation

Authorization is now applied directly to the Chroma query.

The retrieval layer constructs an authorization filter based on the authenticated application context.

Conceptually:

```text
Authenticated user: Alice

Allowed document owners:

alice
OR
public
```

The Chroma query therefore restricts the candidate documents before semantic retrieval returns results.

```text
Alice
 │
 ▼
search_documents()
 │
 ▼
Build ACL Filter
 │
 ├── owner = alice
 └── owner = public
       │
       ▼
    Chroma
       │
       ▼
Semantic search over
authorized documents only
       │
       ▼
LLM Context
```

This prevents Bob-owned private documents from entering Alice's retrieval results.

---

# Why Authorization Happens During Retrieval

An important design decision is that unauthorized documents should not first be retrieved and then filtered afterward.

This design would be undesirable:

```text
Chroma
  │
  ▼
Bob's document
  │
  ▼
Application filter
  │
  ▼
Discard
```

Instead, authorization restricts the vector query itself:

```text
Authenticated User
        │
        ▼
Authorization Filter
        │
        ▼
Vector Search
        │
        ▼
Authorized Results Only
```

The objective is to prevent unauthorized content from crossing the retrieval boundary in the first place.

---

# SEC-002 Tests

The RAG authorization model now verifies both allowed and forbidden access.

Expected behavior:

| User  | Public documents | Alice documents | Bob documents |
| ----- | ---------------- | --------------- | ------------- |
| Alice | ✅ Allow          | ✅ Allow         | ❌ Deny        |
| Bob   | ✅ Allow          | ❌ Deny          | ✅ Allow       |

An example negative security test is:

```python
def test_alice_cannot_retrieve_bobs_documents():

    alice = get_user_context("alice")

    result = search_documents_logic(
        context=alice,
        query="CUST002"
    )

    assert "owner: bob" not in result.lower()
```

In the vulnerable baseline, this test was marked as an expected failure.

After retrieval authorization was introduced, the expected-failure marker was removed.

The same security requirement now acts as a regression test for the mitigation.

---

# Security Principle: Do Not Trust the LLM for Authorization

A possible approach would be to put this into the agent's system instructions:

```text
Never retrieve documents belonging to another user.
```

This project deliberately does not consider that an access-control mechanism.

An LLM may potentially be influenced through:

* Prompt injection
* Indirect prompt injection
* Jailbreaking
* Malicious RAG content
* Tool-use manipulation

The security architecture therefore assumes:

```text
LLM may make an unsafe decision
              │
              ▼
Application security control
              │
              ▼
Unsafe action prevented
```

Rather than assuming:

```text
LLM follows instructions
              │
              ▼
System is secure
```

A core principle of the lab is therefore:

> **Prompt instructions and guardrails are not substitutes for authorization controls.**

---

# Project Structure

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
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── customer.py
│   │   ├── calculator.py
│   │   └── retrieval.py
│   │
│   └── rag/
│       ├── __init__.py
│       └── chroma_store.py
│
├── data/
│   ├── users.json
│   ├── customers.json
│   │
│   └── documents/
│
├── tests/
│   └── security/
│       ├── test_customer_authorization.py
│       └── test_rag_authorization.py
│
├── .gitignore
├── requirements.txt
└── README.md
```

Authorization logic currently remains close to the resources it protects rather than being separated into a dedicated security package.

As the project grows, security-related functionality may be refactored where doing so provides a clear architectural benefit.

---

# Running the Application

Create a virtual environment:

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

# Running Security Tests

Run:

```powershell
python -m pytest -v
```

Current expected state:

```text
Customer authorization tests:
PASS

RAG authorization tests:
PASS
```

Current mitigated findings:

```text
SEC-001  ✅
SEC-002  ✅
```

---

# Git Security Evolution

The repository preserves important security states through Git history and release tags.

## `v0.1-vulnerable-baseline`

The initial agent could retrieve customer objects without enforcing object-level authorization.

```text
Alice
  ↓
CUST002
  ↓
Customer data returned

❌ VULNERABLE
```

---

## `v0.2-authz-controls`

Object-level customer authorization was added.

```text
Alice
  ↓
CUST002
  ↓
Authorization
  ↓
ACCESS DENIED

✅ MITIGATED
```

---

## `v0.3-rag-authz-controls`

RAG retrieval authorization has now been implemented.

Before:

```text
Alice
  ↓
Search CUST002
  ↓
Chroma
  ↓
Bob document returned

❌ VULNERABLE
```

After:

```text
Alice
  ↓
Search CUST002
  ↓
Authorization-aware retrieval
  ↓
Bob document excluded

✅ MITIGATED
```

---

# Release Tags

```text
v0.1-vulnerable-baseline
v0.2-authz-controls
v0.3-rag-authz-controls
```

Planned future tags:

```text
v0.4-agent-guardrails
v1.0-final
```

Tags represent significant security architecture states rather than every development milestone.

---

# Development Roadmap

## Phase 1 — Agent and Customer Authorization

* [x] Create project structure
* [x] Add mock users
* [x] Add mock customers
* [x] Implement application context
* [x] Implement AI agent
* [x] Add customer lookup tool
* [x] Demonstrate customer authorization bypass
* [x] Add SEC-001 security test
* [x] Implement object-level authorization
* [x] Retest SEC-001

## Phase 2 — Multi-Tool Agent

* [x] Add calculator tool
* [x] Demonstrate multi-tool agent behavior

## Phase 3 — RAG and Retrieval Authorization

* [x] Add internal document dataset
* [x] Add Chroma vector database
* [x] Implement document ingestion
* [x] Implement document search tool
* [x] Add document ownership metadata
* [x] Demonstrate cross-user retrieval
* [x] Add SEC-002 security test
* [x] Implement authorization-aware retrieval
* [x] Retest SEC-002
* [x] Release `v0.3-rag-authz-controls`

## Phase 4 — Prompt Injection and RAG Poisoning

* [x] Test direct prompt injection
* [x] Add malicious RAG document
* [x] Demonstrate indirect prompt injection
* [x] Demonstrate RAG poisoning
* [ ] Test system-prompt extraction
* [ ] Introduce trusted/untrusted content boundaries
* [ ] Retest attacks after controls

## Phase 5 — Agent Security

* [ ] Introduce high-impact simulated tool
* [ ] Demonstrate unauthorized tool invocation
* [ ] Demonstrate excessive agency
* [ ] Implement least-privilege tool access
* [ ] Implement tool allowlisting
* [ ] Add structured tool argument validation
* [ ] Require human approval for sensitive actions

## Phase 6 — Memory and Session Security

* [ ] Add persistent conversation sessions
* [ ] Demonstrate cross-session information leakage
* [ ] Implement per-user session isolation
* [ ] Test memory poisoning

## Phase 7 — Additional Defensive Controls

* [ ] Input validation
* [ ] Output validation
* [ ] Rate limiting
* [ ] Audit logging
* [ ] Content filtering
* [ ] Review least-privilege tool scopes

## Phase 8 — Automated AI Red Teaming

* [ ] Expand pytest security regression tests
* [ ] Add Promptfoo
* [ ] Automate adversarial prompt generation
* [ ] Measure attack success
* [ ] Compare pre-control and post-control results

## Phase 9 — Threat Model

* [ ] Document architecture
* [ ] Identify assets
* [ ] Identify trust boundaries
* [ ] Perform STRIDE analysis
* [ ] Perform LLM-specific threat analysis
* [ ] Map threats to mitigations

---

# Security Engineering Methodology

Each finding follows the same process:

```text
1. Define the expected security property
2. Build or identify the vulnerable implementation
3. Develop an attack scenario
4. Reproduce the vulnerability
5. Add an automated security test
6. Determine the root cause
7. Implement a deterministic control
8. Repeat the attack
9. Verify regression tests
10. Document the result
```

This approach deliberately preserves vulnerable states through Git history before introducing their mitigations.

---

# Current Security Results

## SEC-001 — Customer Authorization

### Before

```text
Alice → CUST002 → Customer data

❌
```

### Control

```text
Object-level authorization
```

### After

```text
Alice → CUST002 → ACCESS DENIED

✅
```

---

## SEC-002 — RAG Authorization

### Before

```text
Alice
  ↓
CUST002 search
  ↓
Bob-owned document
  ↓
LLM context

❌
```

### Control

```text
Authorization-aware vector retrieval
```

### After

```text
Alice
  ↓
CUST002 search
  ↓
ACL-filtered vector search
  ↓
Bob document excluded

✅
```

---

# Next Milestone

With customer and retrieval authorization now enforced, the next phase focuses on an entirely different RAG security problem:

> **A document can be authorized to retrieve while still being malicious.**

The next attack path will therefore investigate:

```text
Authorized document
       │
       ▼
Malicious instructions embedded in content
       │
       ▼
RAG retrieval
       │
       ▼
LLM interprets document as instructions
       │
       ▼
Unauthorized agent behavior
```

This will introduce:

* Indirect prompt injection
* RAG poisoning
* Trusted vs. untrusted content boundaries

The project will therefore demonstrate the distinction between:

```text
Can this user retrieve this document?
```

and:

```text
Should the LLM trust instructions contained in this document?
```

These are separate security problems requiring separate controls.

---

# Final Objective

The final project will demonstrate an agentic system in which the LLM is treated as an **untrusted decision-making component rather than a security boundary**.

Established application-security principles including:

* Authentication
* Authorization
* Least privilege
* Input validation
* Trust boundaries
* Auditability
* Separation of duties
* Defense in depth

will be applied to AI-specific components including:

* LLM agents
* Tool invocation
* Retrieval-Augmented Generation
* Vector databases
* Agent memory
* Human-in-the-loop workflows

The final repository will include:

* Working source code
* Vulnerable historical baselines
* Security findings
* Reproducible attacks
* Automated regression tests
* Defensive implementations
* Before/after results
* Architecture documentation
* STRIDE threat model
* LLM-specific threat model
* Automated red-team testing
* Lessons learned
