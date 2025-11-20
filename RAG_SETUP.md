# RAG System Setup Guide

## Overview
This RAG (Retrieval-Augmented Generation) system allows you to query PDF documents using natural language. The system uses:
- **PDF Processing**: Extracts and chunks text from PDFs using optimal chunking strategies
- **Vector Database**: Stores embeddings in Pinecone for fast similarity search
- **RAG Chat**: Generates answers strictly based on retrieved PDF content

## Prerequisites

1. **Python Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**: Create/update `.env` file with:
   ```
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX_NAME_PDF=bavis-pdf-vectors  # New index name for PDFs
   PINECONE_REGION=us-east-1  # Your Pinecone region
   EMBEDDING_MODEL=text-embedding-3-small  # Optional, defaults to this
   ```

## Setup Steps

### Step 1: Add PDF Files
Place your PDF files in the `data/` directory. The system will process all PDFs in this directory.

### Step 2: Process PDFs and Create Vector Database
Run the setup script to process PDFs and create embeddings:

```bash
python setup_pdf_vectors.py
```

Or manually:
```bash
python pdf_vector_store.py
```

This will:
- Extract text from all PDFs in the `data/` directory
- Create optimal chunks using recursive character splitting with semantic awareness
- Generate embeddings using OpenAI's embedding model
- Store embeddings in Pinecone index

### Step 3: Run the Streamlit App
```bash
streamlit run app.py
```

The app now has two tabs:
- **Guided Advisor**: Original system with static catalog
- **RAG Assistant**: New PDF-based RAG system

## Configuration

### Chunking Parameters
You can adjust chunking parameters in `pdf_vector_store.py` or via environment variables:
- `CHUNK_SIZE`: Target chunk size in characters (default: 1000)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 200)

### Retrieval Parameters
Adjust in `pdf_retriever.py`:
- `top_k`: Number of chunks to retrieve (default: 5)

## How It Works

1. **PDF Processing** (`pdf_processor.py`):
   - Extracts text from PDFs page by page
   - Uses recursive character text splitter with semantic boundaries
   - Maintains metadata (source file, page number, chunk index)

2. **Vector Storage** (`pdf_vector_store.py`):
   - Generates embeddings for each chunk
   - Stores in Pinecone with metadata

3. **Retrieval** (`pdf_retriever.py`):
   - Converts user query to embedding
   - Searches Pinecone for similar chunks
   - Returns top-k most relevant chunks

4. **RAG Chat** (`pdf_rag_chat.py`):
   - Uses retrieved chunks as context
   - Generates answers strictly based on retrieved content
   - Never invents information not in the knowledge base

## Features

- **Optimal Chunking**: Recursive character splitting with semantic awareness
- **Metadata Preservation**: Tracks source file and page numbers
- **Strict RAG**: Answers only from retrieved content, no hallucinations
- **Multi-PDF Support**: Processes all PDFs in directory
- **Separate Index**: Uses new Pinecone index to avoid conflicts

## Troubleshooting

1. **No chunks retrieved**: Check if PDFs were processed and embeddings stored
2. **Import errors**: Ensure all modules are in the same directory
3. **Pinecone errors**: Verify API key and index name in `.env`
4. **Dimension mismatch**: Ensure embedding model matches index dimension

## Notes

- The RAG system uses a separate Pinecone index (`PINECONE_INDEX_NAME_PDF`) from the original system
- All responses are strictly based on retrieved PDF content
- The system will clearly state when information is not available in the knowledge base

