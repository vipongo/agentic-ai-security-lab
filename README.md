# Agentic AI Security Lab

A hands-on security engineering project focused on identifying, exploiting, and mitigating security risks in LLM-based agentic applications.

The project implements a small enterprise-style AI agent with access to tools, a Retrieval-Augmented Generation (RAG) knowledge base, and sensitive mock data.

The application is deliberately developed through vulnerable and hardened iterations so that security issues can be:

1. Reproduced
2. Tested
3. Documented
4. Mitigated
5. Retested

The project currently demonstrates both a **successfully mitigated object-level authorization vulnerability** and an **intentionally vulnerable RAG authorization design**.

> **Important:** All users, customers, documents, accounts, and financial information in this repository are fictional test data.

---

# Project Goal

The final architecture represents a simplified enterprise AI assistant:

```text
User
 │
 ▼
AI Agent / LLM
 │
 ├──────────────┬────────────────┬────────────────┐
 ▼              ▼                ▼                ▼
Customer Tool   Calculator       RAG Search       High-impact Tools
 │                               │
 ▼                               ▼
Mock Data                     Vector DB
```

Security controls are progressively introduced around the agent:

```text
Authentication
      │
Authorization
      │
Agent / LLM
      │
Tool access controls
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

The development methodology is:

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

A core architectural principle of the project is that security-sensitive decisions must not rely solely on LLM instructions or prompt-based guardrails.

---

# Current Status

## RAG Vulnerable Baseline

The application currently contains:

* OpenAI-based AI agent
* Two mock application users
* Two mock banking customers
* Trusted application context
* Customer lookup tool
* Deterministic object-level authorization
* Calculator tool
* Multi-tool agent behavior
* Chroma vector database
* Internal document dataset
* RAG document search tool
* Document ownership metadata
* Customer authorization regression tests
* RAG authorization security tests

Two security findings have now been investigated:

| ID      | Finding                             | Status       |
| ------- | ----------------------------------- | ------------ |
| SEC-001 | Cross-customer authorization bypass | ✅ Mitigated  |
| SEC-002 | Cross-user RAG document retrieval   | ❌ Vulnerable |

Current development state:

```text
Customer lookup vulnerability
          │
          ▼
SEC-001 reproduced
          │
          ▼
Authorization control
          │
          ▼
SEC-001 tests PASS
          │
          ▼
Calculator added
          │
          ▼
RAG implemented
          │
          ▼
Cross-user retrieval reproduced
          │
          ▼
SEC-002 test XFAIL
          │
          ▼
CURRENT STATE
```

The next step is to enforce authorization **during RAG retrieval**.

---

# Current Architecture

```text
                         User
                          │
                          ▼
                    AI Agent / LLM
                          │
              ┌───────────┼────────────┐
              │           │            │
              ▼           ▼            ▼
       get_customer() Calculator  search_documents()
              │                         │
              ▼                         ▼
      lookup_customer()          Chroma Vector DB
              │                         │
              ▼                         │
       Authorization                    │
              │                         │
        ┌─────┴─────┐                   │
        │           │                   │
      ALLOW       DENY                  │
        │           │                   │
        ▼           ▼                   ▼
 customers.json  ACCESS DENIED    All documents
                                      │
                                      ▼
                              No retrieval ACL yet
                                      │
                                      ▼
                               ❌ SEC-002
```

The customer tool is now authorization-aware.

The RAG retrieval pipeline is intentionally not authorization-aware yet.

---

# Trusted Application Context

The authenticated application user is represented by `AppContext`:

```text
AppContext
 │
 ├── username
 ├── user_id
 ├── role
 └── authorized_customer_ids
```

This context represents trusted application-side information.

For example:

```text
Alice
└── Authorized customer: CUST001

Bob
└── Authorized customer: CUST002
```

The LLM does not determine these permissions.

---

# Mock Authorization Model

| User  | Role    | Authorized customer |
| ----- | ------- | ------------------- |
| Alice | Advisor | `CUST001`           |
| Bob   | Advisor | `CUST002`           |

Customer authorization matrix:

| User  | CUST001 | CUST002 |
| ----- | ------- | ------- |
| Alice | ✅ Allow | ❌ Deny  |
| Bob   | ❌ Deny  | ✅ Allow |

This authorization matrix is currently enforced for direct customer lookup.

---

# SEC-001 — Cross-Customer Authorization Bypass

## Status: ✅ Mitigated

### Original Vulnerability

The initial implementation allowed the agent to retrieve any customer that existed in the dataset.

For example:

```text
Authenticated user: Alice
Authorized customer: CUST001
Requested customer: CUST002

Result:
CUST002 returned
```

The customer lookup contained no object-level authorization control.

---

## SEC-001 Control

Authorization is now implemented in deterministic application logic:

```python
if customer_id not in context.authorized_customer_ids:
    return "ACCESS DENIED"
```

Result:

```text
Alice
 │
 │ request CUST002
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
 ├── Authenticated: Alice
 ├── Authorized: CUST001
 └── Requested: CUST002
          │
          ▼
     ACCESS DENIED
```

The security control is outside the LLM.

---

# SEC-001 Security Tests

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

These tests currently pass.

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

This creates the foundation for later testing of tool abuse, excessive agency, and least-privilege tool access.

---

# Retrieval-Augmented Generation

The application now contains a RAG pipeline backed by Chroma.

Conceptually:

```text
User question
      │
      ▼
AI Agent
      │
      ▼
search_documents()
      │
      ▼
Semantic query
      │
      ▼
Chroma Vector DB
      │
      ▼
Relevant documents
      │
      ▼
LLM context
      │
      ▼
Answer
```

Documents contain metadata including ownership information.

Conceptually:

```text
Document A
├── source: customer_CUST001.md
└── owner: alice

Document B
├── source: customer_CUST002.md
└── owner: bob
```

This metadata will eventually be used to enforce retrieval authorization.

It is deliberately **not enforced in the current baseline**.

---

# SEC-002 — Cross-User RAG Document Retrieval

## Status: ❌ Vulnerable

The current RAG implementation performs semantic retrieval across the complete Chroma collection.

Conceptually, the vulnerable query behaves like:

```text
Search:
    all documents

Authorization filter:
    NONE
```

The current implementation performs:

```python
results = collection.query(
    query_texts=[query],
    n_results=3
)
```

No authorization condition is applied.

---

## SEC-002 Attack

Alice is authenticated.

Her authorized customer is:

```text
CUST001
```

Alice asks the agent:

```text
Search the internal documents for information about CUST002.
```

The RAG pipeline can retrieve:

```text
SOURCE: customer_CUST002.md
OWNER: bob
```

The information may then enter the LLM context.

Attack flow:

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
 │ semantic similarity search
 │
 │ no authorization filter
 ▼
Bob-owned document
 │
 ▼
LLM context
 │
 ▼
❌ CROSS-USER DATA DISCLOSURE
```

---

# SEC-002 Root Cause

The vector database performs relevance filtering but not authorization filtering.

These are separate security properties:

```text
Semantic relevance
        ≠
Authorization
```

A document can be highly relevant to Alice's query while still being unauthorized for Alice.

The current vulnerable architecture effectively performs:

```text
Retrieve documents
WHERE semantic_similarity = high
```

The target architecture must instead enforce:

```text
Retrieve documents
WHERE semantic_similarity = high
AND
owner IN (authenticated_user, public)
```

---

# SEC-002 Security Requirement

Users should only retrieve:

```text
Public documents
+
documents they are authorized to access
```

Expected retrieval matrix:

| User  | Public | Alice documents | Bob documents |
| ----- | -----: | --------------: | ------------: |
| Alice |      ✅ |               ✅ |             ❌ |
| Bob   |      ✅ |               ❌ |             ✅ |

---

# SEC-002 Security Tests

A deterministic RAG authorization test now documents the vulnerability.

Example:

```python
@pytest.mark.xfail(
    strict=True,
    reason="SEC-002: RAG retrieval does not enforce document ownership"
)
def test_alice_cannot_retrieve_bobs_documents():

    alice = get_user_context("alice")

    result = search_documents_logic(
        context=alice,
        query="CUST002"
    )

    assert "owner: bob" not in result.lower()
```

The test currently produces:

```text
XFAIL
```

This is intentional.

It means:

```text
Security requirement
        │
        ▼
Alice must not retrieve Bob documents
        │
        ▼
Current implementation violates requirement
        │
        ▼
Known and reproducible vulnerability
```

Once retrieval authorization is implemented, the `xfail` marker will be removed and the same test will become a regression test.

---

# Why Authorization Must Happen During Retrieval

A future implementation should **not** retrieve unauthorized documents and remove them afterward.

For example, this is undesirable:

```text
Chroma
  │
  ▼
Bob's sensitive document retrieved
  │
  ▼
Application checks ownership
  │
  ▼
Document discarded
```

Unauthorized information has already crossed the retrieval boundary.

The target architecture is:

```text
Alice
 │
 ▼
search_documents()
 │
 ▼
Authorization-aware query
 │
 ├── public
 └── owner = alice
        │
        ▼
      Chroma
        │
        ▼
Only authorized documents
        │
        ▼
LLM context
```

The objective is to prevent unauthorized information from entering the LLM context at all.

---

# Why LLM Instructions Are Not Authorization Controls

An insecure approach would tell the agent:

```text
Never retrieve documents belonging to another user.
```

This is not considered a sufficient security control.

The project assumes that the LLM could potentially be manipulated through:

* Direct prompt injection
* Indirect prompt injection
* Malicious retrieved content
* Jailbreaking
* Tool-use manipulation

Therefore:

> **LLM instructions and guardrails are not authorization controls.**

Even if the LLM deliberately requests an unauthorized resource, deterministic application controls should prevent access.

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
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── customer.py
│   │   ├── calculator.py
│   │   └── document_search.py
│   │
│   └── rag/
│       ├── __init__.py
│       └── chroma_store.py
│
├── data/
│   ├── users.json
│   ├── customers.json
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
XFAIL
```

This is intentional.

The repository currently contains:

```text
SEC-001 → mitigated
SEC-002 → intentionally vulnerable
```

---

# Git Security Evolution

The repository preserves important security states through Git history and tags.

## `v0.1-vulnerable-baseline`

Initial agent implementation with missing customer object-level authorization.

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

Customer authorization is enforced in deterministic application logic.

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

## Current Untagged Development State

RAG has now been introduced.

```text
Alice
  ↓
Search CUST002
  ↓
Chroma
  ↓
Bob document returned

❌ VULNERABLE RAG
```

This state remains represented by Git history but does not receive a release tag.

---

## Planned `v0.3-secure-rag`

This tag will only be created after:

* Retrieval authorization is implemented
* Alice cannot retrieve Bob-owned documents
* Bob cannot retrieve Alice-owned documents
* Authorized private documents remain accessible
* Public documents remain accessible
* SEC-002 regression tests pass

---

## Planned Version Tags

```text
v0.1-vulnerable-baseline
v0.2-authz-controls
v0.3-secure-rag
v0.4-agent-guardrails
v1.0-final
```

Tags represent major security architecture states rather than every development milestone.

---

# Development Roadmap

## Phase 1 — Agent and Authorization Baseline

* [x] Create project structure
* [x] Create mock users
* [x] Create mock customer data
* [x] Implement application context
* [x] Implement basic AI agent
* [x] Implement customer lookup tool
* [x] Create vulnerable authorization baseline
* [x] Reproduce cross-customer authorization bypass
* [x] Add security test
* [x] Enforce object-level authorization
* [x] Add authorization matrix tests
* [x] Retest SEC-001

## Phase 2 — Additional Agent Tools

* [x] Add calculator tool
* [x] Demonstrate multi-tool agent behavior

## Phase 3 — RAG and Retrieval Authorization

* [x] Add document dataset
* [x] Add Chroma vector database
* [x] Implement document ingestion
* [x] Implement document search tool
* [x] Add document ownership metadata
* [x] Demonstrate cross-user retrieval
* [x] Add SEC-002 security test
* [ ] Implement retrieval authorization
* [ ] Add complete RAG authorization matrix tests
* [ ] Retest SEC-002
* [ ] Tag `v0.3-secure-rag`

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
* [ ] Implement least-privilege tool access
* [ ] Add tool allowlisting
* [ ] Add structured argument validation
* [ ] Add human approval for sensitive actions

## Phase 6 — Memory and Session Security

* [ ] Add conversation sessions
* [ ] Demonstrate cross-session leakage
* [ ] Implement per-user session isolation
* [ ] Test memory poisoning

## Phase 7 — Defensive Controls

* [ ] Input validation
* [ ] Output validation
* [ ] Rate limiting
* [ ] Audit logging
* [ ] Content filtering
* [ ] Least-privilege tool scopes

## Phase 8 — Automated AI Red Teaming

* [ ] Expand pytest security regression suite
* [ ] Add Promptfoo
* [ ] Automate adversarial prompts
* [ ] Measure attack success
* [ ] Compare before/after controls

## Phase 9 — Threat Model

* [ ] Architecture diagram
* [ ] Identify assets
* [ ] Identify trust boundaries
* [ ] STRIDE analysis
* [ ] LLM-specific threat analysis
* [ ] Map threats to security controls

---

# Security Engineering Methodology

Each finding follows the same process:

```text
1. Define security requirement
2. Create vulnerable implementation
3. Develop attack scenario
4. Reproduce vulnerability
5. Add automated security test
6. Determine root cause
7. Implement deterministic control
8. Repeat the attack
9. Verify regression tests
10. Document the result
```

Git history deliberately preserves vulnerable states so that changes in security behavior remain reproducible.

---

# Current Results

## SEC-001

```text
BEFORE

Alice → CUST002 → Data returned
                     ❌


CONTROL

Object-level authorization


AFTER

Alice → CUST002 → ACCESS DENIED
                     ✅
```

## SEC-002

```text
CURRENT

Alice
  ↓
Search for CUST002
  ↓
Semantic retrieval
  ↓
Bob-owned document
  ↓
LLM context

❌ VULNERABLE
```

Target:

```text
Alice
  ↓
Search for CUST002
  ↓
Retrieval authorization
  ↓
Bob-owned document excluded

✅ BLOCKED
```

---

# Next Milestone

The immediate next step is to mitigate **SEC-002**.

The RAG query will be changed from:

```text
Search all documents
```

to:

```text
Search only:
    public documents
    OR
    documents owned by the authenticated user
```

The same security tests that currently produce `XFAIL` will then be rerun.

Once:

```text
Alice → Bob documents = DENIED
Bob → Alice documents = DENIED
Alice → Alice documents = ALLOWED
Bob → Bob documents = ALLOWED
Public documents = ALLOWED
```

all pass, the project will reach:

```text
v0.3-secure-rag
```

The following milestone will then deliberately introduce **indirect prompt injection and RAG poisoning**.

---

# Final Objective

The final project will demonstrate an agentic application in which the LLM is treated as an **untrusted decision-making component rather than a security boundary**.

Established application-security concepts such as:

* Authentication
* Authorization
* Least privilege
* Input validation
* Trust boundaries
* Auditability
* Separation of duties
* Defense in depth

are applied to AI-specific components including:

* LLM agents
* Tool invocation
* RAG
* Vector databases
* Agent memory
* Human-in-the-loop workflows

The final repository will contain:

* Working source code
* Vulnerable historical baselines
* Exploit scenarios
* Automated security tests
* Defensive implementations
* Before/after security results
* Architecture documentation
* STRIDE threat model
* LLM-specific threat model
* Automated red-team methodology
* Lessons learned
