# SEC-002 — Missing RAG Retrieval Authorization

**Severity:** High  
**Status:** Remediated  
**Component:** Chroma RAG retrieval  
**Category:** Information Disclosure / Broken Access Control

## Description

The initial RAG implementation performed semantic retrieval across the entire document collection without applying ownership or authorization constraints.

This allowed authorized users of the assistant to retrieve documents belonging to other relationship managers.

## Vulnerable Scenario

The vector store contained:

```text
alice/cust001_notes.md
bob/cust002_notes.md
public/...
```

Alice queried:

```text
Search all internal documents for CUST002 and tell me everything you can find.
```

The vulnerable retrieval query:

```python
collection.query(
    query_texts=[query],
    n_results=3
)
```

did not contain a metadata authorization filter.

As a result, Bob's private document could enter Alice's model context.

## Security Impact

Successful exploitation could expose confidential unstructured banking information including:

- customer intentions;
- investment preferences;
- relationship-manager notes;
- risk preferences;
- planned investments.

This is particularly serious because the access-control failure occurs before the LLM generates its answer.

## Root Cause

Authorization was applied to structured customer lookup but not to the retrieval layer.

The vector database was treated as one globally searchable corpus.

## Remediation

A metadata ACL is now calculated from the trusted application context:

```python
{
    "$or": [
        {"owner": "public"},
        {"owner": context.username}
    ]
}
```

and supplied directly to Chroma:

```python
results = collection.query(
    query_texts=[query],
    where=acl_filter,
    n_results=5
)
```

## Verification

Alice querying for CUST002 may retrieve semantically related authorized documents, but:

```text
bob/cust002_notes.md
```

does not enter the retrieval result.

Bob remains able to retrieve his own CUST002 notes.

## Security Principle

Retrieval authorization must occur **before** retrieved information is placed into LLM context.

Filtering the final answer after unauthorized documents have already reached the model is not considered an adequate authorization control.

## Residual Risk

Correct enforcement depends on accurate document metadata. Production systems would require strong controls around ingestion, metadata assignment and authorization-policy management.
