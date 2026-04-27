"""
Retriever Module for PDF RAG.
Retrieves relevant chunks from Pinecone or Chroma based on user queries.
"""
import os
import sys

if sys.platform == "win32":
    try:
        import readline
    except ImportError:
        try:
            import pyreadline3 as readline
        except ImportError:
            pass

from dotenv import load_dotenv

from vector_store_utils import (
    create_embedding,
    get_chroma_collection_name,
    get_chroma_persist_directory,
    get_pinecone_index_name,
    get_vector_provider,
)

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = get_pinecone_index_name()
CHROMA_PERSIST_DIRECTORY = get_chroma_persist_directory()
CHROMA_COLLECTION_NAME = get_chroma_collection_name()


def retrieve_from_pinecone(query_embedding, top_k: int):
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not found in environment variables")

    from pinecone import Pinecone

    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(name=PINECONE_INDEX_NAME)

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
    )

    chunks = []
    for match in results.matches:
        chunks.append(
            {
                "text": match.metadata.get("text", ""),
                "similarity": float(match.score),
                "source": match.metadata.get("source", ""),
                "page": match.metadata.get("page", 0),
                "chunk_index": match.metadata.get("chunk_index", 0),
                "id": match.id,
            }
        )

    return chunks


def retrieve_from_chroma(query_embedding, top_k: int):
    try:
        import chromadb
    except ImportError as exc:
        raise ImportError(
            "chromadb is required for Chroma retrieval. Install dependencies from requirements.txt."
        ) from exc

    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
    collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    chunks = []
    for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        similarity = 1.0 - float(distance) if distance is not None else 0.0
        chunks.append(
            {
                "text": document or "",
                "similarity": similarity,
                "source": metadata.get("source", ""),
                "page": metadata.get("page", 0),
                "chunk_index": metadata.get("chunk_index", 0),
                "id": chunk_id,
            }
        )

    return chunks


def retrieve_similar_chunks(query: str, top_k: int = 5):
    """
    Retrieve top-k similar chunks for the given query.
    Results are normalized and sorted deterministically.
    """
    normalized_query = query.lower().strip()
    query_embedding = create_embedding(normalized_query.replace("\n", " "))
    provider = get_vector_provider()

    if provider == "chroma":
        chunks = retrieve_from_chroma(query_embedding, top_k)
    else:
        chunks = retrieve_from_pinecone(query_embedding, top_k)

    chunks.sort(
        key=lambda item: (
            -item["similarity"],
            item["source"],
            item["page"],
            item["chunk_index"],
            item["id"],
        )
    )
    return chunks
