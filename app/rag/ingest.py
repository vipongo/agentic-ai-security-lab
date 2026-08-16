from pathlib import Path

from app.rag.chroma_store import get_collection


BASE_DIR = Path(__file__).resolve().parents[2]

DOCUMENTS_DIR = BASE_DIR / "data" / "documents"


def ingest_documents():

    collection = get_collection()

    document_paths = list(
        DOCUMENTS_DIR.rglob("*.md")
    )

    if not document_paths:
        print("No documents found.")
        return

    for path in document_paths:

        relative_path = path.relative_to(DOCUMENTS_DIR)

        # First folder determines the owner:
        #
        # public/investment_policy.md -> public
        # alice/cust001_notes.md      -> alice
        # bob/cust002_notes.md        -> bob

        owner = relative_path.parts[0]

        if owner == "public":
            scope = "public"
        else:
            scope = "private"

        content = path.read_text(
            encoding="utf-8"
        )

        document_id = (
            str(relative_path)
            .replace("\\", "__")
            .replace("/", "__")
        )

        metadata = {
            "owner": owner,
            "scope": scope,
            "source": str(relative_path)
        }

        collection.upsert(
            ids=[document_id],
            documents=[content],
            metadatas=[metadata]
        )

        print(
            f"Ingested: {relative_path} "
            f"(owner={owner}, scope={scope})"
        )

def test_search():

    collection = get_collection()

    results = collection.query(
        query_texts=[
            "What should a balanced investor invest in?"
        ],
        n_results=2
    )

    print()
    print("Search results:")
    print()

    for document, metadata in zip(
        results["documents"][0],
        results["metadatas"][0]
    ):
        print("SOURCE:", metadata["source"])
        print(document)
        print("-" * 50)

if __name__ == "__main__":
    ingest_documents()