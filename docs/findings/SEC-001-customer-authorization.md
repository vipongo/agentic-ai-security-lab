# SEC-001 — Missing Customer Object Authorization

**Severity:** High  
**Status:** Remediated  
**Component:** Customer lookup tool  
**Category:** Broken Object Level Authorization / Information Disclosure

## Description

The initial customer lookup implementation allowed the agent to retrieve customer records based only on a customer identifier.

The tool did not verify whether the currently authenticated application user was authorized to access the requested customer.

Because the LLM controlled the customer identifier supplied to the tool, an authenticated user could potentially request another relationship manager's customer.

## Vulnerable Scenario

Authenticated user:

```text
alice
```

Authorized customer:

```text
CUST001
```

Unauthorized customer:

```text
CUST002
```

Attack:

```text
Retrieve the customer profile for CUST002.
```

Without application-level authorization, the model could invoke:

```text
get_customer(customer_id="CUST002")
```

and return another user's customer information.

## Security Impact

Successful exploitation could disclose:

- customer identity;
- portfolio information;
- risk profile;
- relationship-manager information;
- other structured banking data.

The vulnerability represents a cross-customer confidentiality breach.

## Root Cause

Authorization was implicitly delegated to agent behavior rather than being enforced by deterministic application code.

The security property incorrectly depended on the model choosing the correct customer identifier.

## Remediation

Object-level authorization was added to the deterministic customer lookup logic:

```python
if customer_id not in context.authorized_customer_ids:
    return "Customer not found or access denied."
```

The authorization decision uses trusted `AppContext` state rather than claims contained in the user's prompt.

## Verification

Alice:

```text
CUST001
→ ALLOW
```

Alice:

```text
CUST002
→ DENY
```

Bob:

```text
CUST002
→ ALLOW
```

Automated regression tests verify both authorized and unauthorized customer access.

## Security Principle

The LLM may select or request a resource, but it must never decide whether access to that resource is authorized.

## Residual Risk

The lab simulates authenticated identity through local application context. A production deployment would require integration with a real identity provider and trusted authorization source.
