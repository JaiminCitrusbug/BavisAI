import os
from typing import Iterable, List

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
DEFAULT_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "50"))


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Restore the key in your environment or .env before running vectorization or chat."
        )
    return OpenAI(api_key=api_key)


def create_embedding(text: str) -> List[float]:
    """Generate a single embedding vector for the supplied text."""
    payload = text or " "
    response = get_openai_client().embeddings.create(model=EMBEDDING_MODEL, input=payload)
    return response.data[0].embedding


def create_embeddings(texts: Iterable[str], batch_size: int = DEFAULT_BATCH_SIZE) -> List[List[float]]:
    """Generate embeddings in batches to reduce API round-trips."""
    text_list = [(text or " ") for text in texts]
    embeddings: List[List[float]] = []
    client = get_openai_client()

    for start in range(0, len(text_list), batch_size):
        batch = text_list[start:start + batch_size]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        embeddings.extend(item.embedding for item in response.data)

    return embeddings


def build_embedding_text(chunk: dict) -> str:
    """Blend document metadata into the embedding text for stronger retrieval."""
    source = chunk.get("source", "Unknown PDF")
    page = chunk.get("page", "Unknown")
    text = chunk.get("text", "")
    return f"Manual: {source}\nPage: {page}\nContent:\n{text}"


def get_vector_provider() -> str:
    """Return the configured vector provider."""
    provider = os.getenv("VECTOR_DB_PROVIDER", "pinecone").strip().lower()
    if provider in {"chroma", "chromadb"}:
        return "chroma"
    return "pinecone"


def get_pinecone_index_name() -> str:
    return (
        os.getenv("PINECONE_INDEX_NAME_PDF")
        or os.getenv("PINECONE_INDEX")
        or "bavis-pdf-vectors"
    )


def get_pinecone_region() -> str:
    raw_region = os.getenv("PINECONE_REGION") or os.getenv("PINECONE_ENV") or "us-east-1"
    if raw_region.count("-") >= 3 and raw_region.endswith("-aws"):
        return raw_region.rsplit("-", 1)[0]
    return raw_region


def get_chroma_persist_directory() -> str:
    return os.getenv("CHROMA_PERSIST_DIRECTORY", "chroma_db")


def get_chroma_collection_name() -> str:
    return os.getenv("CHROMA_COLLECTION_NAME", "bavis-pdf-vectors")
