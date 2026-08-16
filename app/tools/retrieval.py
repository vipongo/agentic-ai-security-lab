from agents import RunContextWrapper
from agents.decorators import tool

from app.context import AppContext
from app.rag.chroma_store import get_collection


def search_documents_logic(
    context: AppContext,
    query: str
) -> str:
    """
    Core document retrieval logic.

    Intentionally vulnerable baseline:
    retrieval authorization is not enforced yet.
    """

    collection = get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    if not documents:
        return "No relevant documents found."

    output = []

    for document, metadata in zip(
        documents,
        metadatas
    ):
        output.append(
            f"""
SOURCE: {metadata["source"]}
OWNER: {metadata["owner"]}

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
    Search internal banking documents for information relevant
    to the user's query.
    """

    return search_documents_logic(
        context=context.context,
        query=query
    )