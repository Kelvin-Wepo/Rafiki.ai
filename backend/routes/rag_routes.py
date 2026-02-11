"""
RAG API Routes

Endpoints for querying the Kenyan Constitution knowledge base
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import logging

from services.rag_service import get_rag_service, initialize_rag

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["RAG"])


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for RAG queries"""
    query: str = Field(..., description="The question or query text")
    top_k: Optional[int] = Field(5, description="Number of results to retrieve", ge=1, le=20)
    include_citations: bool = Field(True, description="Include source citations")
    chapter_filter: Optional[str] = Field(None, description="Filter by specific chapter")


class RetrievalResultResponse(BaseModel):
    """Response model for a single retrieval result"""
    content: str
    citation: str
    score: float
    metadata: Dict


class QueryResponse(BaseModel):
    """Response model for RAG queries"""
    query: str
    context: str
    citations: List[str]
    results: List[RetrievalResultResponse]
    result_count: int


class InitializeRequest(BaseModel):
    """Request model for database initialization"""
    force_rebuild: bool = Field(False, description="Force rebuild even if database exists")


class InitializeResponse(BaseModel):
    """Response model for initialization"""
    status: str
    chunk_count: int
    message: str


class StatsResponse(BaseModel):
    """Response model for database statistics"""
    total_chunks: int
    collection_name: str
    sample_chapters: List[str]
    chunk_size: int
    chunk_overlap: int
    top_k: int
    similarity_threshold: float
    is_initialized: bool


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    is_initialized: bool
    message: str


# Endpoints
@router.post("/query", response_model=QueryResponse)
async def query_constitution(request: QueryRequest):
    """
    Query the Kenyan Constitution knowledge base
    
    Returns relevant constitutional text with citations
    """
    try:
        rag = get_rag_service()
        
        if not rag.is_initialized():
            raise HTTPException(
                status_code=503,
                detail="RAG database not initialized. Please initialize first."
            )
        
        # Get results
        filter_meta = {"chapter": request.chapter_filter} if request.chapter_filter else None
        results = rag.query(
            query_text=request.query,
            top_k=request.top_k,
            filter_metadata=filter_meta
        )
        
        # Get formatted context and citations
        context, citations = rag.get_context_for_query(
            query_text=request.query,
            top_k=request.top_k,
            include_citations=request.include_citations
        )
        
        # Format response
        result_responses = [
            RetrievalResultResponse(
                content=r.content,
                citation=r.citation,
                score=r.score,
                metadata=r.metadata
            )
            for r in results
        ]
        
        return QueryResponse(
            query=request.query,
            context=context,
            citations=citations,
            results=result_responses,
            result_count=len(results)
        )
    
    except Exception as e:
        logger.error(f"Error querying RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize", response_model=InitializeResponse)
async def initialize_database(request: InitializeRequest, background_tasks: BackgroundTasks):
    """
    Initialize or rebuild the RAG database
    
    This loads the constitution document and creates vector embeddings.
    Can be run in the background for large documents.
    """
    try:
        # Run initialization
        result = initialize_rag(force_rebuild=request.force_rebuild)
        
        return InitializeResponse(**result)
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Constitution document not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error initializing RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_database_stats():
    """
    Get statistics about the RAG database
    
    Returns information about the indexed documents
    """
    try:
        rag = get_rag_service()
        stats = rag.get_stats()
        
        if 'error' in stats:
            raise HTTPException(status_code=500, detail=stats['error'])
        
        return StatsResponse(**stats)
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check if the RAG service is healthy and initialized
    """
    try:
        rag = get_rag_service()
        is_init = rag.is_initialized()
        
        return HealthResponse(
            status="healthy" if is_init else "not_initialized",
            is_initialized=is_init,
            message="RAG service is operational" if is_init else "Database not initialized"
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            is_initialized=False,
            message=str(e)
        )


@router.get("/chapters")
async def list_chapters():
    """
    List all available chapters in the constitution
    
    Returns a list of chapter numbers and titles
    """
    try:
        rag = get_rag_service()
        
        if not rag.is_initialized():
            raise HTTPException(
                status_code=503,
                detail="RAG database not initialized"
            )
        
        # Get all documents and extract unique chapters
        sample = rag.collection.get(limit=1000)
        
        chapters = {}
        if sample and sample['metadatas']:
            for meta in sample['metadatas']:
                chapter_num = meta.get('chapter')
                chapter_title = meta.get('chapter_title')
                if chapter_num and chapter_num not in chapters:
                    chapters[chapter_num] = chapter_title
        
        # Format response
        chapter_list = [
            {"chapter": num, "title": title}
            for num, title in sorted(chapters.items())
        ]
        
        return {
            "chapters": chapter_list,
            "total_chapters": len(chapter_list)
        }
    
    except Exception as e:
        logger.error(f"Error listing chapters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/chapter/{chapter}")
async def search_chapter(chapter: str, query: Optional[str] = None, limit: int = 10):
    """
    Search within a specific chapter
    
    Args:
        chapter: Chapter number (e.g., "1", "IV")
        query: Optional search query
        limit: Maximum number of results
    """
    try:
        rag = get_rag_service()
        
        if not rag.is_initialized():
            raise HTTPException(
                status_code=503,
                detail="RAG database not initialized"
            )
        
        results = rag.search_by_chapter(chapter, query)
        
        # Limit results
        results = results[:limit]
        
        return {
            "chapter": chapter,
            "query": query,
            "results": [r.to_dict() for r in results],
            "result_count": len(results)
        }
    
    except Exception as e:
        logger.error(f"Error searching chapter: {e}")
        raise HTTPException(status_code=500, detail=str(e))
