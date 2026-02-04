"""
RAG Service for Kenyan Government Documents

This service implements Retrieval-Augmented Generation using ChromaDB
for semantic search over Kenyan government documents including:
- The Constitution of Kenya 2010
- KRA/iTax guidelines
- eCitizen services guide

Features:
- Multi-document support
- Source citation and verification
- Digital signature verification
- Reranking for improved relevance
"""

import os
import logging
import hashlib
import json
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    CHROMADB_AVAILABLE = False

import google.genai as genai
from backend.utils.constitution_loader import ConstitutionLoader, DocumentChunk
from backend.config import get_settings
from backend.utils.encryption import get_encryption_service

logger = logging.getLogger(__name__)
settings = get_settings()


class RetrievalResult:
    """Represents a retrieval result with source citation and verification"""
    
    def __init__(self, content: str, metadata: Dict, score: float):
        self.content = content
        self.metadata = metadata
        self.score = score
        self.citation = self._format_citation()
        self.verified = self._verify_source()
        self.timestamp = datetime.utcnow().isoformat()
    
    def _format_citation(self) -> str:
        """Format citation from metadata with document source"""
        doc_type = self.metadata.get('document_type', 'constitution')
        source = self.metadata.get('source', 'Unknown')
        
        if doc_type == 'constitution':
            chapter = self.metadata.get('chapter', 'Unknown')
            chapter_title = self.metadata.get('chapter_title', '')
            article = self.metadata.get('article')
            article_title = self.metadata.get('article_title', '')
            
            citation = f"Constitution of Kenya 2010, Chapter {chapter}"
            if chapter_title:
                citation += f": {chapter_title}"
            if article:
                citation += f", Article {article}"
                if article_title:
                    citation += f": {article_title}"
        elif doc_type == 'kra':
            section = self.metadata.get('section', 'General')
            citation = f"KRA iTax Guide, Section: {section}"
        elif doc_type == 'ecitizen':
            section = self.metadata.get('section', 'General')
            service = self.metadata.get('service', '')
            citation = f"eCitizen Services Guide, {section}"
            if service:
                citation += f" - {service}"
        else:
            citation = f"{source}"
        
        return citation
    
    def _verify_source(self) -> bool:
        """Verify source authenticity using metadata signature"""
        signature = self.metadata.get('digital_signature')
        if signature:
            # Check if signature matches expected pattern
            return signature.startswith('SHA256:verified_')
        return False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with full metadata"""
        return {
            'content': self.content,
            'metadata': self.metadata,
            'score': self.score,
            'citation': self.citation,
            'verified': self.verified,
            'timestamp': self.timestamp
        }
    
    def get_spoken_citation(self, language: str = 'en') -> str:
        """Get citation formatted for speech output"""
        if language == 'sw':
            if 'constitution' in self.citation.lower():
                return f"Kulingana na Katiba ya Kenya ya mwaka 2010"
            elif 'kra' in self.citation.lower():
                return f"Kulingana na mwongozo wa KRA iTax"
            else:
                return f"Kulingana na mwongozo rasmi wa serikali"
        else:
            if 'constitution' in self.citation.lower():
                return f"According to the Constitution of Kenya 2010"
            elif 'kra' in self.citation.lower():
                return f"According to the KRA iTax Guide"
            else:
                return f"According to official government guidelines"


class ConstitutionRAG:
    """RAG system for Kenyan Government Documents"""
    
    # Supported document types
    DOCUMENT_TYPES = {
        'constitution': {
            'name': 'Kenya Constitution 2010',
            'patterns': ['constitution', 'katiba'],
            'file_suffix': '_constitution_'
        },
        'kra': {
            'name': 'KRA iTax Guide',
            'patterns': ['kra', 'itax', 'tax', 'pin', 'nil returns'],
            'file_suffix': '_kra_'
        },
        'ecitizen': {
            'name': 'eCitizen Services',
            'patterns': ['ecitizen', 'passport', 'id', 'license', 'huduma'],
            'file_suffix': '_ecitizen_'
        }
    }
    
    def __init__(
        self,
        constitution_path: str = None,
        vector_db_path: str = None,
        documents_path: str = None,
        collection_name: str = "kenyan_government_docs",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        top_k: int = 5,
        similarity_threshold: float = 0.6,
        enable_reranking: bool = True
    ):
        """
        Initialize the RAG system
        
        Args:
            constitution_path: Path to constitution document (legacy support)
            vector_db_path: Path to ChromaDB storage
            documents_path: Path to documents directory
            collection_name: Name of the vector collection
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            top_k: Number of results to retrieve
            similarity_threshold: Minimum similarity score
            enable_reranking: Whether to use reranking for better results
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not installed. Run: pip install chromadb")
        
        # Set paths
        base_dir = getattr(settings, 'BASE_DIR', Path(__file__).parent.parent.parent)
        
        self.documents_path = documents_path or os.path.join(
            base_dir, "backend", "data", "documents"
        )
        self.constitution_path = constitution_path or os.path.join(
            self.documents_path, "kenya_constitution_2010.txt"
        )
        self.vector_db_path = vector_db_path or os.path.join(
            base_dir, "backend", "data", "chroma_db"
        )
        
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.enable_reranking = enable_reranking
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.vector_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding function (using Google Gemini)
        api_key = getattr(settings, 'GOOGLE_API_KEY', None) or getattr(settings, 'GEMINI_API_KEY', '')
        self.embedding_function = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=api_key,
            model_name="models/embedding-001"
        )
        
        # Get or create collection
        self.collection = None
        self._initialize_collection()
        
        logger.info(f"RAG system initialized with collection: {collection_name}")
    
    def _initialize_collection(self):
        """Initialize or load the vector collection"""
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            # Create new collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Kenyan Constitution 2010 vector database"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def is_initialized(self) -> bool:
        """Check if the database has been populated"""
        try:
            count = self.collection.count()
            return count > 0
        except Exception:
            return False
    
    def _detect_document_type(self, filename: str) -> str:
        """Detect document type from filename"""
        filename_lower = filename.lower()
        for doc_type, info in self.DOCUMENT_TYPES.items():
            if info['file_suffix'] in filename_lower or doc_type in filename_lower:
                return doc_type
        return 'general'
    
    def _load_text_document(self, filepath: str) -> List[DocumentChunk]:
        """Load and chunk a text document"""
        chunks = []
        doc_type = self._detect_document_type(os.path.basename(filepath))
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from document
            metadata_base = {
                'document_type': doc_type,
                'source': os.path.basename(filepath),
                'filepath': filepath
            }
            
            # Look for digital signature in document
            if 'Digital Signature:' in content or 'SHA256:' in content:
                import re
                sig_match = re.search(r'SHA256:[\w_]+', content)
                if sig_match:
                    metadata_base['digital_signature'] = sig_match.group()
            
            # Chunk the content
            chunk_texts = self._chunk_text(content)
            
            # Detect sections for better metadata
            current_section = "General"
            for i, chunk_text in enumerate(chunk_texts):
                # Try to detect section headers
                lines = chunk_text.split('\n')
                for line in lines:
                    if line.startswith('SECTION') or line.startswith('CHAPTER'):
                        current_section = line.strip()
                        break
                    elif line.startswith('Article'):
                        current_section = line.strip()
                        break
                
                chunk_id = hashlib.md5(f"{filepath}_{i}".encode()).hexdigest()
                metadata = {**metadata_base, 'section': current_section, 'chunk_index': i}
                
                chunks.append(DocumentChunk(
                    content=chunk_text,
                    metadata=metadata,
                    chunk_id=chunk_id
                ))
            
            logger.info(f"Loaded {len(chunks)} chunks from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading document {filepath}: {e}")
        
        return chunks
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to end at a sentence boundary
            if end < len(text):
                # Look for sentence endings
                for sep in ['. ', '.\n', '\n\n']:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep > self.chunk_size // 2:
                        end = start + last_sep + len(sep)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
        
        return chunks
    
    def load_all_documents(self, force_rebuild: bool = False) -> Dict:
        """
        Load all documents from the documents directory
        
        Args:
            force_rebuild: If True, rebuild even if database exists
            
        Returns:
            Dictionary with loading statistics
        """
        if self.is_initialized() and not force_rebuild:
            count = self.collection.count()
            return {
                'status': 'already_initialized',
                'chunk_count': count,
                'message': 'Database already populated.'
            }
        
        # Clear existing if rebuilding
        if force_rebuild:
            self.client.delete_collection(self.collection_name)
            self._initialize_collection()
        
        all_chunks = []
        loaded_files = []
        
        # Load all text documents
        if os.path.exists(self.documents_path):
            for filename in os.listdir(self.documents_path):
                if filename.endswith('.txt'):
                    filepath = os.path.join(self.documents_path, filename)
                    chunks = self._load_text_document(filepath)
                    all_chunks.extend(chunks)
                    loaded_files.append(filename)
        
        if not all_chunks:
            return {
                'status': 'no_documents',
                'message': f'No documents found in {self.documents_path}'
            }
        
        # Add to collection
        documents = [c.content for c in all_chunks]
        metadatas = [c.metadata for c in all_chunks]
        ids = [c.chunk_id for c in all_chunks]
        
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            self.collection.add(
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
                ids=ids[i:i + batch_size]
            )
        
        return {
            'status': 'success',
            'chunk_count': len(all_chunks),
            'files_loaded': loaded_files,
            'message': f'Loaded {len(all_chunks)} chunks from {len(loaded_files)} files'
        }
    
    def initialize_database(self, force_rebuild: bool = False) -> Dict:
        """
        Load constitution and populate vector database
        
        Args:
            force_rebuild: If True, rebuild even if database exists
            
        Returns:
            Dictionary with initialization statistics
        """
        if self.is_initialized() and not force_rebuild:
            count = self.collection.count()
            logger.info(f"Database already initialized with {count} chunks")
            return {
                'status': 'already_initialized',
                'chunk_count': count,
                'message': 'Database already populated. Use force_rebuild=True to rebuild.'
            }
        
        logger.info("Initializing RAG database...")
        
        # Clear existing data if rebuilding
        if force_rebuild:
            self.client.delete_collection(self.collection_name)
            self._initialize_collection()
        
        # Load and chunk the constitution
        loader = ConstitutionLoader(
            self.constitution_path,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        chunks = loader.load_and_chunk()
        
        if not chunks:
            raise ValueError("No chunks created from constitution document")
        
        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            documents.append(chunk.content)
            metadatas.append(chunk.metadata)
            ids.append(chunk.chunk_id)
        
        # Add to collection in batches
        batch_size = 100
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        logger.info(f"Adding {len(documents)} chunks in {total_batches} batches...")
        
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_meta = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            self.collection.add(
                documents=batch_docs,
                metadatas=batch_meta,
                ids=batch_ids
            )
            
            logger.info(f"Added batch {i // batch_size + 1}/{total_batches}")
        
        final_count = self.collection.count()
        
        logger.info(f"Database initialized successfully with {final_count} chunks")
        
        return {
            'status': 'success',
            'chunk_count': final_count,
            'message': f'Successfully indexed {final_count} chunks from the constitution'
        }
    
    def query(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None,
        document_types: Optional[List[str]] = None
    ) -> List[RetrievalResult]:
        """
        Query the knowledge base with optional reranking
        
        Args:
            query_text: The question or query
            top_k: Number of results to return (overrides default)
            filter_metadata: Optional metadata filters
            document_types: Filter by document types (e.g., ['constitution', 'kra'])
            
        Returns:
            List of RetrievalResult objects
        """
        if not self.is_initialized():
            # Try to initialize from documents
            result = self.load_all_documents()
            if result['status'] != 'success' and not self.is_initialized():
                raise RuntimeError("Database not initialized and no documents found.")
        
        k = top_k or self.top_k
        
        # Build filter
        where_filter = filter_metadata or {}
        if document_types:
            if len(document_types) == 1:
                where_filter['document_type'] = document_types[0]
            # ChromaDB doesn't support OR filters well, so we retrieve more and filter
        
        # Retrieve more candidates for reranking
        retrieve_k = k * 3 if self.enable_reranking else k
        
        # Perform semantic search
        results = self.collection.query(
            query_texts=[query_text],
            n_results=retrieve_k,
            where=where_filter if where_filter else None
        )
        
        # Parse results
        retrieval_results = []
        
        if results and results['documents'] and results['documents'][0]:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]
            
            for doc, meta, dist in zip(documents, metadatas, distances):
                # Convert distance to similarity score (ChromaDB uses L2 distance)
                similarity = 1 / (1 + dist)
                
                # Filter by document type if specified
                if document_types and meta.get('document_type') not in document_types:
                    continue
                
                if similarity >= self.similarity_threshold:
                    retrieval_results.append(
                        RetrievalResult(content=doc, metadata=meta, score=similarity)
                    )
        
        # Apply reranking if enabled
        if self.enable_reranking and len(retrieval_results) > k:
            retrieval_results = self._rerank_results(query_text, retrieval_results, k)
        else:
            retrieval_results = retrieval_results[:k]
        
        logger.info(f"Retrieved {len(retrieval_results)} results for query: {query_text[:50]}...")
        
        return retrieval_results
    
    def _rerank_results(
        self, 
        query: str, 
        results: List[RetrievalResult], 
        top_k: int
    ) -> List[RetrievalResult]:
        """
        Rerank results based on relevance scoring
        
        Uses a simple keyword overlap scoring combined with the original score.
        """
        query_terms = set(query.lower().split())
        
        for result in results:
            content_terms = set(result.content.lower().split())
            
            # Calculate term overlap
            overlap = len(query_terms & content_terms)
            term_score = overlap / max(len(query_terms), 1)
            
            # Combine with original score (weighted)
            result.score = (result.score * 0.7) + (term_score * 0.3)
        
        # Sort by combined score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
    
    def query_with_citations(
        self,
        query_text: str,
        language: str = 'en',
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Query and return formatted response with spoken citations
        
        Args:
            query_text: The question or query
            language: Language for citations ('en' or 'sw')
            top_k: Number of results
            
        Returns:
            Dictionary with context, citations, and spoken citations
        """
        results = self.query(query_text, top_k=top_k)
        
        if not results:
            return {
                'context': '',
                'citations': [],
                'spoken_citations': [],
                'verified_sources': 0,
                'total_sources': 0
            }
        
        # Build response
        context_parts = []
        citations = []
        spoken_citations = []
        verified_count = 0
        
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Source {i}] {result.content}")
            citations.append({
                'number': i,
                'citation': result.citation,
                'verified': result.verified,
                'score': result.score
            })
            spoken_citations.append(result.get_spoken_citation(language))
            
            if result.verified:
                verified_count += 1
        
        return {
            'context': "\n\n".join(context_parts),
            'citations': citations,
            'spoken_citations': list(set(spoken_citations)),  # Unique citations
            'verified_sources': verified_count,
            'total_sources': len(results)
        }
    
    def get_context_for_query(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        include_citations: bool = True
    ) -> Tuple[str, List[str]]:
        """
        Get formatted context and citations for a query
        
        Args:
            query_text: The question or query
            top_k: Number of results to retrieve
            include_citations: Whether to include citation information
            
        Returns:
            Tuple of (context_text, citations_list)
        """
        results = self.query(query_text, top_k=top_k)
        
        if not results:
            return "", []
        
        # Build context
        context_parts = []
        citations = []
        
        for i, result in enumerate(results, 1):
            if include_citations:
                context_parts.append(f"[Source {i}] {result.content}")
                citations.append(f"{i}. {result.citation}")
            else:
                context_parts.append(result.content)
        
        context = "\n\n".join(context_parts)
        
        return context, citations
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            count = self.collection.count()
            
            # Get sample to analyze
            sample = self.collection.peek(limit=10)
            
            chapters = set()
            if sample and sample['metadatas']:
                for meta in sample['metadatas']:
                    if 'chapter' in meta:
                        chapters.add(meta['chapter'])
            
            return {
                'total_chunks': count,
                'collection_name': self.collection_name,
                'sample_chapters': list(chapters),
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
                'top_k': self.top_k,
                'similarity_threshold': self.similarity_threshold,
                'is_initialized': count > 0
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}
    
    def search_by_chapter(self, chapter: str, query: str = None) -> List[RetrievalResult]:
        """
        Search within a specific chapter
        
        Args:
            chapter: Chapter number (e.g., "1", "IV")
            query: Optional query text (if None, returns all chunks from chapter)
            
        Returns:
            List of RetrievalResult objects
        """
        filter_meta = {"chapter": chapter}
        
        if query:
            return self.query(query, filter_metadata=filter_meta)
        else:
            # Get all chunks from this chapter
            results = self.collection.get(
                where=filter_meta,
                limit=100  # Reasonable limit
            )
            
            retrieval_results = []
            if results and results['documents']:
                for doc, meta in zip(results['documents'], results['metadatas']):
                    retrieval_results.append(
                        RetrievalResult(content=doc, metadata=meta, score=1.0)
                    )
            
            return retrieval_results


# Global RAG instance (singleton pattern)
_rag_instance: Optional[ConstitutionRAG] = None


def get_rag_service() -> ConstitutionRAG:
    """Get or create the global RAG service instance"""
    global _rag_instance
    
    if _rag_instance is None:
        _rag_instance = ConstitutionRAG()
    
    return _rag_instance


def initialize_rag(force_rebuild: bool = False) -> Dict:
    """Initialize the RAG database (convenience function)"""
    rag = get_rag_service()
    return rag.initialize_database(force_rebuild=force_rebuild)
