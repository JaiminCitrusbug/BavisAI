"""
Vector Store Module for PDF embeddings in ChromaDB.
Stores PDF chunks as embeddings with page-aware metadata.
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

from pdf_processor import PDFProcessor
from vector_store_utils import (
    build_embedding_text,
    create_embeddings,
    get_chroma_collection_name,
    get_chroma_persist_directory,
)

load_dotenv()

try:
    import chromadb
except ImportError as exc:
    raise ImportError(
        "chromadb is required for Chroma vectorization. Install dependencies from requirements.txt."
    ) from exc

CHROMA_PERSIST_DIRECTORY = get_chroma_persist_directory()
CHROMA_COLLECTION_NAME = get_chroma_collection_name()


def store_pdf_embeddings_chroma(
    pdf_directory: str = "data",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    reset_collection: bool = True,
):
    """
    Process PDFs and store embeddings in a local Chroma collection.

    Args:
        pdf_directory: Directory containing PDF files
        chunk_size: Target chunk size for text splitting
        chunk_overlap: Overlap between chunks
        reset_collection: Whether to delete and recreate the collection before rebuilding
    """
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)

    if reset_collection:
        try:
            client.delete_collection(CHROMA_COLLECTION_NAME)
            print(f"Deleted existing Chroma collection '{CHROMA_COLLECTION_NAME}'")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"\nProcessing PDFs from {pdf_directory}...")
    processor = PDFProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = processor.process_multiple_pdfs(pdf_directory)

    if not chunks:
        raise ValueError("No chunks created from PDFs")

    print(f"\nGenerating embeddings for {len(chunks)} chunks...")
    embeddings = create_embeddings(build_embedding_text(chunk) for chunk in chunks)

    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "source": chunk["source"],
            "page": chunk["page"],
            "chunk_index": chunk["chunk_index"],
        }
        for chunk in chunks
    ]

    batch_size = 100
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    print(f"\nUploading {len(chunks)} vectors to ChromaDB...")
    for index_num in range(0, len(chunks), batch_size):
        end = index_num + batch_size
        collection.upsert(
            ids=ids[index_num:end],
            documents=documents[index_num:end],
            metadatas=metadatas[index_num:end],
            embeddings=embeddings[index_num:end],
        )
        batch_number = (index_num // batch_size) + 1
        print(f"  Upserted batch {batch_number}/{total_batches}")

    print(
        f"\nStored {len(chunks)} embeddings successfully in Chroma collection "
        f"'{CHROMA_COLLECTION_NAME}' at '{CHROMA_PERSIST_DIRECTORY}'"
    )


if __name__ == "__main__":
    store_pdf_embeddings_chroma(pdf_directory="data", chunk_size=1000, chunk_overlap=200)
