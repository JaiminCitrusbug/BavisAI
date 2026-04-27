"""
Build the PDF vector database in ChromaDB.
Run this file directly to rebuild the local Chroma-backed manual index.
"""
import os

from dotenv import load_dotenv

from pdf_vector_store_chroma import store_pdf_embeddings_chroma

load_dotenv()


if __name__ == "__main__":
    pdf_directory = os.getenv("PDF_DIRECTORY", "data")
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
    reset_collection = os.getenv("RESET_CHROMA_COLLECTION", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }

    print("=" * 60)
    print("Chroma PDF Vector Setup")
    print("=" * 60)
    print(f"PDF directory: {pdf_directory}")
    print(f"Chunk size: {chunk_size}")
    print(f"Chunk overlap: {chunk_overlap}")
    print(f"Reset collection: {reset_collection}")
    print("=" * 60)

    store_pdf_embeddings_chroma(
        pdf_directory=pdf_directory,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        reset_collection=reset_collection,
    )

    print("\nChroma vector rebuild completed successfully.")
