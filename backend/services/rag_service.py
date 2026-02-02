"""
RAG Service for Kenyan Constitution

This service implements Retrieval-Augmented Generation using ChromaDB
for semantic search over the Kenyan Constitution 2010.
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import hashlib
import json

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None

import google.genai as genai
from backend.utils.constitution_loader import ConstitutionLoader, DocumentChunk
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RetrievalResult:
    """Represents a retrieval result with source citation"""
    
    def __init__(self, content: str, metadata: Dict, score: float):
        self.content = content
        self.metadata = metadata
        self.score = score
        self.citation = self._format_citation()
    
    def _format_citation(self) -> str:
        """Format citation from metadata"""
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
        
        return citation
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'content': self.content,
            'metadata': self.metadata,
            'score': self.score,
            'citation': self.citation
        }


class ConstitutionRAG:
    """RAG system for the Kenyan Constitution"""
    
    def __init__(
        self,
        constitution_path: str = None,
        vector_db_path: str = None,
        collection_name: str = "kenyan_constitution",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize the RAG system
        
        Args:
            constitution_path: Path to constitution document
            vector_db_path: Path to ChromaDB storage
            collection_name: Name of the vector collection
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            top_k: Number of results to retrieve
            similarity_threshold: Minimum similarity score
        """
        if chromadb is None:
            raise ImportError("ChromaDB not installed. Run: pip install chromadb")
        
        # Set paths
        self.constitution_path = constitution_path or os.path.join(
            settings.BASE_DIR, "backend", "data", "kenyan_constitution_2010.pdf"
        )
        self.vector_db_path = vector_db_path or os.path.join(
            settings.BASE_DIR, "backend", "data", "chroma_db"
        )
        
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.vector_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding function (using Google Gemini)
        self.embedding_function = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=settings.GOOGLE_API_KEY,
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
        filter_metadata: Optional[Dict] = None
    ) -> List[RetrievalResult]:
        """
        Query the constitution knowledge base
        
        Args:
            query_text: The question or query
            top_k: Number of results to return (overrides default)
            filter_metadata: Optional metadata filters
            
        Returns:
            List of RetrievalResult objects
        """
        if not self.is_initialized():
            raise RuntimeError("Database not initialized. Call initialize_database() first.")
        
        k = top_k or self.top_k
        
        # Perform semantic search
        results = self.collection.query(
            query_texts=[query_text],
            n_results=k,
            where=filter_metadata
        )
        
        # Parse results
        retrieval_results = []
        
        if results and results['documents'] and results['documents'][0]:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]
            
            for doc, meta, dist in zip(documents, metadatas, distances):
                # Convert distance to similarity score (ChromaDB uses L2 distance)
                # Lower distance = higher similarity
                similarity = 1 / (1 + dist)
                
                if similarity >= self.similarity_threshold:
                    retrieval_results.append(
                        RetrievalResult(content=doc, metadata=meta, score=similarity)
                    )
        
        logger.info(f"Retrieved {len(retrieval_results)} results for query: {query_text[:50]}...")
        
        return retrieval_results
    
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
