from agents import RunContextWrapper
from agents.decorators import tool

from app.context import AppContext
from app.rag.chroma_store import get_collection
from app.security.content_security import scan_untrusted_content
from app.security.tool_access import document_read_enabled
from app.security.tool_schemas import DocumentSearchQuery
from app.security.audit import audit_event
from app.security.request_policy import check_resource_scope


def document_access_filter(
    context: AppContext
) -> dict:
    """
    Build the retrieval authorization filter.

    Users may retrieve:
    - public documents
    - documents they own
    """

    return {
        "$or": [
            {"owner": "public"},
            {"owner": context.username}
        ]
    }


def search_documents_logic(
    context: AppContext,
    query: DocumentSearchQuery
) -> str:
    """
    Search authorized internal documents.

    Use this tool for:
    - investment preferences
    - relationship-manager notes
    - customer names
    - policies
    - market outlooks
    - other unstructured information

    The query may contain either customer names or customer IDs.
    """

    collection = get_collection()

    # SECURITY CONTROL:
    # Restrict the candidate document set BEFORE semantic retrieval.
    resource_decision = (
    check_resource_scope(
        context,
        query,
    )
)

    if not resource_decision.allowed:

        audit_event(
            event_type="RAG_QUERY_AUTHZ",
            username=context.username,
            outcome="DENY",
            reason=resource_decision.reason,
        )

        return "Request not permitted."
        
    acl_filter = document_access_filter(context)

    audit_event(
        event_type="RAG_SEARCH",
        username=context.username,
        outcome="START",
        query_length=len(query),
    )

    results = collection.query(
        query_texts=[query],
        where=acl_filter,
        n_results=5
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    if not documents:
        return "No relevant authorized documents found."

    output = []

    for document, metadata in zip(
        documents,
        metadatas
    ):
        source = metadata["source"]
        owner = metadata["owner"]

        audit_event(
            event_type="RAG_RETRIEVAL",
            username=context.username,
            outcome="ALLOW",
            source=source,
            owner=owner,
        )

        # SECURITY CONTROL:
        # Inspect retrieved content before returning it to the LLM.
        scan_result = scan_untrusted_content(
            document
        )

        if not scan_result.safe:
            audit_event(
                event_type="RAG_CONTENT_SCAN",
                username=context.username,
                outcome="BLOCK",
                source=source,
                rule=scan_result.matched_rule,
            )
            continue

        # Safe documents are still explicitly marked as untrusted data.
        output.append(
            f"""
<UNTRUSTED_RETRIEVED_CONTENT
source="{source}"
owner="{owner}">

{document}

</UNTRUSTED_RETRIEVED_CONTENT>
"""
        )

    if not output:
        return "No safe authorized documents were found."

    return "\n---\n".join(output)


@tool(
    is_enabled=document_read_enabled
)
def search_documents(
    context: RunContextWrapper[AppContext],
    query: DocumentSearchQuery
) -> str:
    """
    Search internal banking documents that the authenticated
    user is authorized to access.
    """

    return search_documents_logic(
        context=context.context,
        query=query
    )