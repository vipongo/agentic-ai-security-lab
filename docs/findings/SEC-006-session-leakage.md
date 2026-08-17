# SEC-006 — Cross-User Session Leakage

**Severity:** High  
**Status:** Remediated  
**Component:** Conversation memory / SQLiteSession  
**Category:** Information Disclosure

## Description

The initial persistent-memory implementation used the same session identifier for all authenticated users:

```python
session_id = "default"
```

This allowed Alice and Bob to share conversation history.

## Vulnerable Scenario

Alice:

```text
Give me the complete profile for CUST001.
```

The customer information becomes part of persistent conversation history.

Bob subsequently starts the application and asks:

```text
What customer profile did we discuss previously?
```

Because both users use:

```text
session_id="default"
```

Bob may receive Alice's previous context without invoking the protected customer tool.

## Security Impact

This bypasses tool authorization entirely.

The vulnerability path is:

```text
Alice authorized tool call
        ↓
sensitive output enters memory
        ↓
shared memory
        ↓
Bob reads previous context
```

No unauthorized tool call is required.

## Root Cause

Conversation ownership was not bound to authenticated identity.

## Remediation

Sessions are scoped to the authenticated user:

```python
session_id = f"user:{username}:default"
```

Result:

```text
Alice → user:alice:default
Bob   → user:bob:default
```

## Verification

Alice's conversation persists across Alice sessions.

Bob's conversation persists across Bob sessions.

Neither user receives the other's conversation history.

## Security Principle

Conversation state is security-sensitive persistent data and must be subject to the same isolation requirements as other customer data.

## Residual Risk

A production implementation should normally use both:

- authenticated user identifier;
- unique conversation identifier.

Example:

```text
user:<id>:conversation:<uuid>
```

Access to arbitrary session identifiers must never be controlled by untrusted client input alone.
