"""
Vector Store Module for PDF embeddings in Pinecone.
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
from pinecone import AwsRegion, CloudProvider, Pinecone, ServerlessSpec

from pdf_processor import PDFProcessor
from vector_store_utils import (
    EMBEDDING_MODEL,
    build_embedding_text,
    create_embedding,
    create_embeddings,
    get_pinecone_index_name,
    get_pinecone_region,
)

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = get_pinecone_index_name()
PINECONE_REGION = get_pinecone_region()


def get_aws_region(region_string: str):
    """Get AwsRegion enum value from string, with fallback."""
    region_map = {
        "us-east-1": AwsRegion.US_EAST_1,
        "us-west-2": AwsRegion.US_WEST_2,
        "eu-west-1": AwsRegion.EU_WEST_1,
    }

    if region_string in region_map:
        return region_map[region_string]

    try:
        enum_name = region_string.replace("-", "_").upper()
        if hasattr(AwsRegion, enum_name):
            return getattr(AwsRegion, enum_name)
    except Exception:
        pass

    print(f"Warning: region '{region_string}' not found, defaulting to us-east-1")
    return AwsRegion.US_EAST_1


def ensure_index(pc: Pinecone, embedding_dimension: int):
    existing_indexes = [index.name for index in pc.list_indexes()]

    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=embedding_dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=CloudProvider.AWS,
                region=get_aws_region(PINECONE_REGION),
            ),
        )
        print(
            f"Index {PINECONE_INDEX_NAME} created successfully with dimension {embedding_dimension}"
        )
        return

    print(f"Index {PINECONE_INDEX_NAME} already exists")
    index_stats = pc.describe_index(PINECONE_INDEX_NAME)
    index_dimension = index_stats.dimension

    if index_dimension != embedding_dimension:
        raise ValueError(
            f"Dimension mismatch for '{PINECONE_INDEX_NAME}': "
            f"index dimension is {index_dimension}, embedding model '{EMBEDDING_MODEL}' "
            f"produces {embedding_dimension}. Use a new index name or recreate the index."
        )

    print(f"Index dimension ({index_dimension}) matches embedding dimension ({embedding_dimension})")


def store_pdf_embeddings(
    pdf_directory: str = "data",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    clear_existing: bool = True,
):
    """
    Process PDFs and store embeddings in a Pinecone index.

    Args:
        pdf_directory: Directory containing PDF files
        chunk_size: Target chunk size for text splitting
        chunk_overlap: Overlap between chunks
        clear_existing: Whether to clear existing vectors before rebuilding
    """
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not found in environment variables")

    pc = Pinecone(api_key=PINECONE_API_KEY)

    print(f"Getting embedding dimension for model: {EMBEDDING_MODEL}")
    embedding_dimension = len(create_embedding("sample"))
    print(f"Embedding dimension: {embedding_dimension}")

    ensure_index(pc, embedding_dimension)
    index = pc.Index(name=PINECONE_INDEX_NAME)

    if clear_existing:
        try:
            index.delete(delete_all=True)
            print(f"Cleared existing vectors from '{PINECONE_INDEX_NAME}'")
        except Exception as exc:
            print(f"Warning: could not clear existing vectors: {exc}")

    print(f"\nProcessing PDFs from {pdf_directory}...")
    processor = PDFProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = processor.process_multiple_pdfs(pdf_directory)

    if not chunks:
        raise ValueError("No chunks created from PDFs")

    print(f"\nGenerating embeddings for {len(chunks)} chunks...")
    embedding_inputs = [build_embedding_text(chunk) for chunk in chunks]
    embeddings = create_embeddings(embedding_inputs)

    vectors_to_upsert = []
    for chunk, embedding in zip(chunks, embeddings):
        metadata = {
            "text": chunk["text"],
            "source": chunk["source"],
            "page": chunk["page"],
            "chunk_index": chunk["chunk_index"],
        }
        vectors_to_upsert.append(
            {
                "id": chunk["id"],
                "values": embedding,
                "metadata": metadata,
            }
        )

    print(f"\nUploading {len(vectors_to_upsert)} vectors to Pinecone...")
    batch_size = 100
    total_batches = (len(vectors_to_upsert) + batch_size - 1) // batch_size
    for index_num in range(0, len(vectors_to_upsert), batch_size):
        batch = vectors_to_upsert[index_num:index_num + batch_size]
        index.upsert(vectors=batch)
        batch_number = (index_num // batch_size) + 1
        print(f"  Upserted batch {batch_number}/{total_batches}")

    print(
        f"\nStored {len(vectors_to_upsert)} embeddings successfully in Pinecone index "
        f"'{PINECONE_INDEX_NAME}'"
    )


if __name__ == "__main__":
    store_pdf_embeddings(pdf_directory="data", chunk_size=1000, chunk_overlap=200)
