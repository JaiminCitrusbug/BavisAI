"""
Retriever Module for PDF RAG
Retrieves relevant chunks from Pinecone based on user queries.
"""
import os
import sys

# Windows compatibility fix for readline
if sys.platform == "win32":
    try:
        import readline
    except ImportError:
        try:
            import pyreadline3 as readline
        except ImportError:
            pass  # readline is optional, continue without it

from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Pinecone setup
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME_PDF", "bavis-pdf-vectors")


def get_embedding(text: str, model: str = None):
    """Generate embedding for query."""
    if model is None:
        model = EMBEDDING_MODEL
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding


def retrieve_similar_chunks(query: str, top_k: int = 5):
    """
    Retrieve top-k similar chunks for the given query using Pinecone.
    Ensures deterministic and consistent retrieval by normalizing query and sorting results.
    
    Args:
        query: User query string
        top_k: Number of chunks to retrieve
        
    Returns:
        List of chunk dictionaries with text, similarity, and metadata, sorted by similarity (descending)
    """
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not found in environment variables")
    
    # Normalize query for consistency (lowercase, strip whitespace)
    normalized_query = query.lower().strip()
    query_embedding = get_embedding(normalized_query)
    
    # Initialize Pinecone and connect to index
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(name=PINECONE_INDEX_NAME)
    
    # Query Pinecone for similar vectors
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    # Format results and ensure deterministic ordering
    chunks = []
    for match in results.matches:
        chunks.append({
            "text": match.metadata.get("text", ""),
            "similarity": float(match.score),  # Cosine similarity score
            "source": match.metadata.get("source", ""),
            "page": match.metadata.get("page", 0),
            "chunk_index": match.metadata.get("chunk_index", 0),
            "id": match.id  # Include ID for deterministic sorting
        })
    
    # Sort by similarity (descending), then by source, then by page, then by chunk_index for complete determinism
    chunks.sort(key=lambda x: (-x["similarity"], x["source"], x["page"], x["chunk_index"]))
    
    return chunks

