"""
PDF Processing Module with Optimal Chunking Strategy
Implements semantic-aware chunking with recursive character splitting for multi-PDF RAG systems.
"""
import os
import re
from typing import List, Dict, Any
from pathlib import Path
import pypdf
from dotenv import load_dotenv

load_dotenv()


class PDFProcessor:
    """Process PDFs and create optimal chunks for vector storage."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize PDF processor.
        
        Args:
            chunk_size: Target size for text chunks (characters)
            chunk_overlap: Overlap between chunks to maintain context
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF with page-level metadata.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of dictionaries with 'text', 'page', and 'source' keys
        """
        pages = []
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                pdf_name = Path(pdf_path).name
                
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    text = page.extract_text()
                    if text.strip():  # Only add non-empty pages
                        pages.append({
                            'text': text,
                            'page': page_num,
                            'source': pdf_name
                        })
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            raise
        
        return pages
    
    def split_text_recursive(self, text: str, separators: List[str] = None) -> List[str]:
        """
        Recursively split text using separators in order of preference.
        This maintains semantic boundaries while ensuring chunks are appropriately sized.
        
        Args:
            text: Text to split
            separators: List of separators to try (in order of preference)
            
        Returns:
            List of text chunks
        """
        if separators is None:
            # Order matters: try more specific separators first
            separators = [
                "\n\n\n",  # Multiple paragraph breaks
                "\n\n",    # Paragraph breaks
                "\n",      # Line breaks
                ". ",      # Sentence endings
                " ",       # Word boundaries
                ""         # Character level (last resort)
            ]
        
        # Base case: if text is small enough, return as single chunk
        if len(text) <= self.chunk_size:
            return [text]
        
        # Try each separator
        for sep in separators:
            if sep == "":
                # Character-level splitting (last resort)
                chunks = []
                for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                    chunks.append(text[i:i + self.chunk_size])
                return chunks
            
            splits = text.split(sep)
            
            # If splitting produces chunks that are reasonably sized
            if len(splits) > 1:
                chunks = []
                current_chunk = ""
                
                for split in splits:
                    # If adding this split would exceed chunk size, save current and start new
                    if len(current_chunk) + len(split) + len(sep) > self.chunk_size and current_chunk:
                        chunks.append(current_chunk.strip())
                        # Start new chunk with overlap
                        overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                        current_chunk = overlap_text + sep + split
                    else:
                        current_chunk += (sep + split) if current_chunk else split
                
                # Add remaining chunk
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                
                # If we got reasonable chunks, return them
                if chunks and all(len(chunk) <= self.chunk_size * 1.5 for chunk in chunks):
                    return chunks
        
        # Fallback: character-level split
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunks.append(text[i:i + self.chunk_size])
        return chunks
    
    def clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing excessive whitespace and normalizing.
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere
        text = re.sub(r'\x00', '', text)  # Remove null bytes
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        return text.strip()
    
    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Process a PDF file and return chunks with metadata.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        # Extract pages
        pages = self.extract_text_from_pdf(pdf_path)
        
        chunks = []
        chunk_id = 0
        
        for page_data in pages:
            text = self.clean_text(page_data['text'])
            
            # Split page text into chunks
            text_chunks = self.split_text_recursive(text)
            
            for chunk_text in text_chunks:
                if chunk_text.strip():  # Only add non-empty chunks
                    chunks.append({
                        'id': f"{Path(pdf_path).stem}_page{page_data['page']}_chunk{chunk_id}",
                        'text': chunk_text,
                        'page': page_data['page'],
                        'source': page_data['source'],
                        'chunk_index': chunk_id
                    })
                    chunk_id += 1
        
        return chunks
    
    def process_multiple_pdfs(self, pdf_directory: str) -> List[Dict[str, Any]]:
        """
        Process all PDFs in a directory.
        
        Args:
            pdf_directory: Directory containing PDF files
            
        Returns:
            List of all chunks from all PDFs
        """
        pdf_dir = Path(pdf_directory)
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            raise ValueError(f"No PDF files found in {pdf_directory}")
        
        all_chunks = []
        
        for pdf_file in pdf_files:
            print(f"Processing {pdf_file.name}...")
            chunks = self.process_pdf(str(pdf_file))
            all_chunks.extend(chunks)
            print(f"  Created {len(chunks)} chunks from {pdf_file.name}")
        
        print(f"\nTotal chunks created: {len(all_chunks)}")
        return all_chunks


if __name__ == "__main__":
    # Example usage
    processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
    
    # Process single PDF
    # chunks = processor.process_pdf("data/data-sheet-product-catalog.pdf")
    
    # Process directory of PDFs
    chunks = processor.process_multiple_pdfs("data")
    
    # Print sample chunk
    if chunks:
        print("\nSample chunk:")
        print(f"ID: {chunks[0]['id']}")
        print(f"Source: {chunks[0]['source']}")
        print(f"Page: {chunks[0]['page']}")
        print(f"Text preview: {chunks[0]['text'][:200]}...")

