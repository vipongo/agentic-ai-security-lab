from agents import RunContextWrapper
from agents.decorators import tool

from app.context import AppContext
from app.rag.chroma_store import get_collection


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
    query: str
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
        print(
            f"[RAG] Retrieved "
            f"source={metadata['source']} "
            f"owner={metadata['owner']}"
        )

        output.append(
            f"""
SOURCE: {metadata["source"]}

{document}
"""
        )

    return "\n---\n".join(output)


@tool
def search_documents(
    context: RunContextWrapper[AppContext],
    query: str
) -> str:
    """
    Search internal banking documents that the authenticated
    user is authorized to access.
    """

    return search_documents_logic(
        context=context.context,
        query=query
    )