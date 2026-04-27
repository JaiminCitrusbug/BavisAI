"""
Build the PDF vector database in Pinecone.
Run this file directly to rebuild the Pinecone-backed manual index.
"""
import os

from dotenv import load_dotenv

from pdf_vector_store import store_pdf_embeddings

load_dotenv()


if __name__ == "__main__":
    pdf_directory = os.getenv("PDF_DIRECTORY", "data")
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
    clear_existing = os.getenv("CLEAR_EXISTING_VECTORS", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }

    print("=" * 60)
    print("Pinecone PDF Vector Setup")
    print("=" * 60)
    print(f"PDF directory: {pdf_directory}")
    print(f"Chunk size: {chunk_size}")
    print(f"Chunk overlap: {chunk_overlap}")
    print(f"Clear existing vectors: {clear_existing}")
    print("=" * 60)

    store_pdf_embeddings(
        pdf_directory=pdf_directory,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        clear_existing=clear_existing,
    )

    print("\nPinecone vector rebuild completed successfully.")
