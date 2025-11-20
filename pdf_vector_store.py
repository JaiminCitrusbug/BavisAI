"""
Vector Store Module for PDF Embeddings
Stores PDF chunks as embeddings in Pinecone with metadata.
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

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec, CloudProvider, AwsRegion
from pdf_processor import PDFProcessor

load_dotenv()

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Pinecone setup
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME_PDF", "bavis-pdf-vectors")  # New index name for PDFs
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")


def create_embedding(text: str):
    """Generate an embedding vector for a given text."""
    if not text:
        text = " "  # avoid empty input to embeddings API
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding


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
    
    print(f"⚠️  Region '{region_string}' not found, defaulting to us-east-1")
    return AwsRegion.US_EAST_1


def store_pdf_embeddings(pdf_directory: str = "data", chunk_size: int = 1000, chunk_overlap: int = 200):
    """
    Process PDFs and store embeddings in Pinecone index.
    
    Args:
        pdf_directory: Directory containing PDF files
        chunk_size: Target chunk size for text splitting
        chunk_overlap: Overlap between chunks
    """
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not found in environment variables")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Get embedding dimension from OpenAI model
    print(f"Getting embedding dimension for model: {EMBEDDING_MODEL}")
    sample_embedding = create_embedding("sample")
    embedding_dimension = len(sample_embedding)
    print(f"✅ Embedding dimension: {embedding_dimension}")
    
    # Check if index exists, create if not
    existing_indexes = [index.name for index in pc.list_indexes()]
    
    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
        
        aws_region = get_aws_region(PINECONE_REGION)
        
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=embedding_dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=CloudProvider.AWS,
                region=aws_region
            )
        )
        print(f"✅ Index {PINECONE_INDEX_NAME} created successfully with dimension {embedding_dimension}!")
    else:
        print(f"✅ Index {PINECONE_INDEX_NAME} already exists")
        # Check index dimension
        index_stats = pc.describe_index(PINECONE_INDEX_NAME)
        index_dimension = index_stats.dimension
        
        if index_dimension != embedding_dimension:
            raise ValueError(
                f"❌ Dimension mismatch!\n"
                f"   Index '{PINECONE_INDEX_NAME}' has dimension: {index_dimension}\n"
                f"   Embedding model '{EMBEDDING_MODEL}' produces dimension: {embedding_dimension}\n\n"
                f"   Solutions:\n"
                f"   1. Use a different index name (set PINECONE_INDEX_NAME_PDF in .env)\n"
                f"   2. Delete the existing index and recreate it\n"
                f"   3. Use an embedding model that matches the index dimension\n"
            )
        else:
            print(f"✅ Index dimension ({index_dimension}) matches embedding dimension ({embedding_dimension})")
    
    # Connect to index
    index = pc.Index(name=PINECONE_INDEX_NAME)
    
    # Process PDFs
    print(f"\nProcessing PDFs from {pdf_directory}...")
    processor = PDFProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = processor.process_multiple_pdfs(pdf_directory)
    
    if not chunks:
        raise ValueError("No chunks created from PDFs")
    
    # Prepare vectors for batch upsert
    vectors_to_upsert = []
    
    print(f"\nGenerating embeddings for {len(chunks)} chunks...")
    for i, chunk in enumerate(chunks):
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(chunks)} chunks...")
        
        embedding = create_embedding(chunk['text'])
        
        # Pinecone metadata stores additional info
        metadata = {
            "text": chunk['text'],
            "source": chunk['source'],
            "page": chunk['page'],
            "chunk_index": chunk['chunk_index']
        }
        
        vectors_to_upsert.append({
            "id": chunk['id'],
            "values": embedding,
            "metadata": metadata
        })
    
    # Batch upsert to Pinecone (upsert in batches of 100)
    print(f"\nUploading {len(vectors_to_upsert)} vectors to Pinecone...")
    batch_size = 100
    for i in range(0, len(vectors_to_upsert), batch_size):
        batch = vectors_to_upsert[i:i + batch_size]
        index.upsert(vectors=batch)
        print(f"  Upserted batch {i//batch_size + 1}/{(len(vectors_to_upsert) + batch_size - 1)//batch_size}")
    
    print(f"\n✅ All {len(vectors_to_upsert)} embeddings stored successfully in Pinecone index '{PINECONE_INDEX_NAME}'!")


if __name__ == "__main__":
    # Process PDFs and store embeddings
    store_pdf_embeddings(pdf_directory="data", chunk_size=1000, chunk_overlap=200)

