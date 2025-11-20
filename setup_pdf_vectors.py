"""
Setup script to process PDFs and create vector embeddings in Pinecone.
Run this script once to initialize the PDF vector database.
"""
import os
from dotenv import load_dotenv
from pdf_vector_store import store_pdf_embeddings

load_dotenv()

if __name__ == "__main__":
    print("=" * 60)
    print("PDF Vector Database Setup")
    print("=" * 60)
    print("\nThis script will:")
    print("1. Process all PDFs in the 'data' directory")
    print("2. Create text chunks with optimal chunking strategy")
    print("3. Generate embeddings using OpenAI")
    print("4. Store embeddings in Pinecone index")
    print("\nMake sure you have:")
    print("- PDF files in the 'data' directory")
    print("- OPENAI_API_KEY set in .env file")
    print("- PINECONE_API_KEY set in .env file")
    print("- PINECONE_INDEX_NAME_PDF set in .env (default: 'bavis-pdf-vectors')")
    print("\n" + "=" * 60)
    
    response = input("\nDo you want to proceed? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        try:
            pdf_directory = os.getenv("PDF_DIRECTORY", "data")
            chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
            chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
            
            print(f"\nProcessing PDFs from: {pdf_directory}")
            print(f"Chunk size: {chunk_size}, Overlap: {chunk_overlap}\n")
            
            store_pdf_embeddings(
                pdf_directory=pdf_directory,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            print("\n" + "=" * 60)
            print("✅ Setup completed successfully!")
            print("=" * 60)
            print("\nYou can now use the RAG Assistant tab in the Streamlit app.")
            
        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            print("\nPlease check:")
            print("1. PDF files exist in the data directory")
            print("2. Environment variables are set correctly")
            print("3. Pinecone index name is available")
    else:
        print("\nSetup cancelled.")

