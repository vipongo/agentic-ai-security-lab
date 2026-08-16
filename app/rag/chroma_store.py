from pathlib import Path

import chromadb
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction


load_dotenv()


BASE_DIR = Path(__file__).resolve().parents[2]

CHROMA_DIR = BASE_DIR / "data" / "chroma"


embedding_function = OpenAIEmbeddingFunction(
    model_name="text-embedding-3-small"
)


def get_collection():

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_or_create_collection(
        name="bank_documents",
        embedding_function=embedding_function
    )

    return collection