# SEC-008 — Missing Transfer Authorization

**Severity:** High  
**Status:** Remediated  
**Component:** Simulated transfer tool  
**Category:** Broken Function/Object Authorization

## Description

The vulnerable transfer implementation accepted any source customer identifier supplied by the model.

Although customer lookup already enforced customer authorization, transfer execution represented a separate access path and initially did not perform equivalent checks.

## Vulnerable Scenario

Alice is authorized for:

```text
CUST001
```

but requests:

```text
Transfer CHF 50000 from CUST002 to DEMO-ACCOUNT-999.
```

The vulnerable implementation executed the simulated transfer.

## Security Impact

A user could perform a high-impact operation against an object they were not permitted to control.

This demonstrates that read authorization on one tool does not automatically protect another tool acting on the same resource.

## Root Cause

Authorization was implemented independently for customer lookup but was missing from the transfer business logic.

## Remediation

Two authorization layers were introduced.

### Function-level permission

```python
"transfer:create" in context.permissions
```

### Object-level authorization

```python
source_customer_id in context.authorized_customer_ids
```

Additionally, runtime tool exposure now follows least privilege.

Users without:

```text
transfer:create
```

do not receive the transfer tool in the model's available tool set.

## Verification

Alice:

```text
CUST001
→ permitted, subject to approval
```

Alice:

```text
CUST002
→ DENY
```

Bob:

```text
CUST002
```

but without `transfer:create`:

```text
create_transfer hidden
```

## Security Principle

Every privileged action path must independently enforce authorization.

Authorization attached to one read API cannot be assumed to protect a separate write/action API.
