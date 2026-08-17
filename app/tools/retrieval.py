from agents import RunContextWrapper
from agents.decorators import tool

from app.context import AppContext
from app.rag.chroma_store import get_collection
from app.security.content_security import scan_untrusted_content
from app.security.tool_access import document_read_enabled
from app.security.tool_schemas import DocumentSearchQuery


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

    print(
        f"[RAG] User={context.username} "
        f"Query={query}"
    )

    collection = get_collection()

    # SECURITY CONTROL:
    # Restrict the candidate document set BEFORE semantic retrieval.
    acl_filter = document_access_filter(context)

    print(
        f"[RAG][AUTHZ] Applying ACL "
        f"user={context.username} "
        f"filter={acl_filter}"
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

        print(
            f"[RAG] Retrieved "
            f"source={source} "
            f"owner={owner}"
        )

        # SECURITY CONTROL:
        # Inspect retrieved content before returning it to the LLM.
        scan_result = scan_untrusted_content(
            document
        )

        if not scan_result.safe:
            print(
                f"[SECURITY] BLOCKED suspicious RAG content "
                f"source={source} "
                f"rule={scan_result.matched_rule}"
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