"""
Constitution Document Loader for RAG System

This module handles loading, parsing, and chunking the Kenyan Constitution 2010
for use in the RAG (Retrieval-Augmented Generation) system.
"""

import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

from bs4 import BeautifulSoup


@dataclass
class DocumentChunk:
    """Represents a chunk of the constitution with metadata"""
    content: str
    metadata: Dict[str, any]
    chunk_id: str
    
    def __post_init__(self):
        """Validate and clean content"""
        self.content = self.content.strip()


class ConstitutionLoader:
    """Loads and processes the Kenyan Constitution document"""
    
    def __init__(self, document_path: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the constitution loader
        
        Args:
            document_path: Path to the constitution PDF or text file
            chunk_size: Target size for text chunks (in characters)
            chunk_overlap: Overlap between chunks for context preservation
        """
        self.document_path = Path(document_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        if not self.document_path.exists():
            raise FileNotFoundError(f"Constitution document not found: {document_path}")
    
    def load_pdf(self) -> str:
        """Load text from PDF file"""
        try:
            reader = PdfReader(str(self.document_path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise RuntimeError(f"Failed to load PDF: {e}")
    
    def load_text(self) -> str:
        """Load text from plain text file"""
        with open(self.document_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def load_document(self) -> str:
        """Load document based on file extension"""
        ext = self.document_path.suffix.lower()
        
        if ext == '.pdf':
            return self.load_pdf()
        elif ext in ['.txt', '.md']:
            return self.load_text()
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers
        text = re.sub(r'Page \d+', '', text)
        text = re.sub(r'\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def extract_structure(self, text: str) -> List[Dict]:
        """
        Extract structural elements (chapters, articles, sections)
        
        Returns list of structured sections with metadata
        """
        sections = []
        
        # Pattern to match chapters
        chapter_pattern = r'CHAPTER\s+([IVXLCDM]+|[0-9]+)[:\s\-]+([^\n]+)'
        
        # Pattern to match articles
        article_pattern = r'(?:^|\n)(\d+)\.\s+([^\n]+)'
        
        # Split by chapters
        chapter_matches = list(re.finditer(chapter_pattern, text, re.IGNORECASE))
        
        for i, chapter_match in enumerate(chapter_matches):
            chapter_num = chapter_match.group(1)
            chapter_title = chapter_match.group(2).strip()
            
            # Get text from this chapter to the next
            start_pos = chapter_match.end()
            end_pos = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(text)
            chapter_text = text[start_pos:end_pos]
            
            # Extract articles within this chapter
            article_matches = list(re.finditer(article_pattern, chapter_text))
            
            if article_matches:
                for j, article_match in enumerate(article_matches):
                    article_num = article_match.group(1)
                    article_title = article_match.group(2).strip()
                    
                    # Get article content
                    article_start = article_match.end()
                    article_end = article_matches[j + 1].start() if j + 1 < len(article_matches) else len(chapter_text)
                    article_content = chapter_text[article_start:article_end].strip()
                    
                    sections.append({
                        'chapter': chapter_num,
                        'chapter_title': chapter_title,
                        'article': article_num,
                        'article_title': article_title,
                        'content': article_content,
                        'type': 'article'
                    })
            else:
                # No articles found, treat entire chapter as one section
                sections.append({
                    'chapter': chapter_num,
                    'chapter_title': chapter_title,
                    'article': None,
                    'article_title': None,
                    'content': chapter_text.strip(),
                    'type': 'chapter'
                })
        
        return sections
    
    def create_chunks(self, text: str, metadata: Optional[Dict] = None) -> List[DocumentChunk]:
        """
        Create overlapping chunks from text
        
        Args:
            text: Text to chunk
            metadata: Base metadata to attach to all chunks
            
        Returns:
            List of DocumentChunk objects
        """
        if metadata is None:
            metadata = {}
        
        chunks = []
        text_length = len(text)
        start = 0
        chunk_index = 0
        
        while start < text_length:
            # Calculate end position
            end = start + self.chunk_size
            
            # If not at the end, try to break at sentence boundary
            if end < text_length:
                # Look for sentence ending within the last 20% of chunk
                search_start = end - int(self.chunk_size * 0.2)
                sentence_end = max(
                    text.rfind('. ', search_start, end),
                    text.rfind('! ', search_start, end),
                    text.rfind('? ', search_start, end)
                )
                
                if sentence_end > search_start:
                    end = sentence_end + 1
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_metadata = {
                    **metadata,
                    'chunk_index': chunk_index,
                    'start_char': start,
                    'end_char': end
                }
                
                chunk_id = f"{metadata.get('chapter', 'unk')}_{metadata.get('article', 'unk')}_{chunk_index}"
                
                chunks.append(DocumentChunk(
                    content=chunk_text,
                    metadata=chunk_metadata,
                    chunk_id=chunk_id
                ))
                
                chunk_index += 1
            
            # Move to next chunk with overlap
            start = end - self.chunk_overlap
            
            # Ensure we make progress
            if start <= chunks[-1].metadata['start_char'] if chunks else False:
                start = end
        
        return chunks
    
    def load_and_chunk(self) -> List[DocumentChunk]:
        """
        Main method to load document and create chunks
        
        Returns:
            List of DocumentChunk objects ready for embedding
        """
        print(f"Loading document from {self.document_path}...")
        raw_text = self.load_document()
        
        print("Cleaning text...")
        cleaned_text = self.clean_text(raw_text)
        
        print("Extracting structure...")
        sections = self.extract_structure(cleaned_text)
        
        print(f"Found {len(sections)} structural sections")
        
        all_chunks = []
        
        # Create chunks for each section
        for section in sections:
            section_metadata = {
                'chapter': section['chapter'],
                'chapter_title': section['chapter_title'],
                'article': section.get('article'),
                'article_title': section.get('article_title'),
                'type': section['type'],
                'source': 'Constitution of Kenya 2010'
            }
            
            chunks = self.create_chunks(section['content'], section_metadata)
            all_chunks.extend(chunks)
        
        print(f"Created {len(all_chunks)} chunks total")
        
        return all_chunks
    
    def save_chunks_to_text(self, chunks: List[DocumentChunk], output_path: str):
        """Save chunks to a text file for inspection"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(f"\n{'='*80}\n")
                f.write(f"Chunk ID: {chunk.chunk_id}\n")
                f.write(f"Metadata: {chunk.metadata}\n")
                f.write(f"{'-'*80}\n")
                f.write(f"{chunk.content}\n")


def main():
    """Test the constitution loader"""
    import sys
    
    # Get document path from command line or use default
    doc_path = sys.argv[1] if len(sys.argv) > 1 else "backend/data/kenyan_constitution_2010.pdf"
    
    loader = ConstitutionLoader(doc_path, chunk_size=1000, chunk_overlap=200)
    chunks = loader.load_and_chunk()
    
    print(f"\n{'='*80}")
    print(f"Successfully loaded and chunked the constitution!")
    print(f"Total chunks: {len(chunks)}")
    print(f"\nSample chunk:")
    print(f"{'='*80}")
    if chunks:
        sample = chunks[0]
        print(f"ID: {sample.chunk_id}")
        print(f"Metadata: {sample.metadata}")
        print(f"Content preview: {sample.content[:200]}...")
    
    # Save to text file for inspection
    output_path = doc_path.replace('.pdf', '_chunks.txt').replace('.txt', '_chunks.txt')
    loader.save_chunks_to_text(chunks, output_path)
    print(f"\nChunks saved to: {output_path}")


if __name__ == "__main__":
    main()
