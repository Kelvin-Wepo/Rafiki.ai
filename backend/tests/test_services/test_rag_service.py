"""Tests for RAG service."""

import pytest
from unittest.mock import MagicMock, patch
import uuid

from services.rag_service import ConstitutionRAG, RetrievalResult


@pytest.fixture
def rag_service():
    """Create RAG service instance."""
    # If chromadb or its helpers are missing, mock them comprehensively
    mock_client = MagicMock()
    mock_client.get_collection.side_effect = Exception("no collection")
    mock_client.create_collection.return_value = MagicMock()

    mock_chromadb = MagicMock()
    mock_chromadb.PersistentClient = MagicMock(return_value=mock_client)

    mock_embedding_funcs = MagicMock()
    mock_embedding_funcs.GoogleGenerativeAiEmbeddingFunction = MagicMock(return_value=MagicMock())

    with patch("services.rag_service.chromadb", new=mock_chromadb):
        with patch("services.rag_service.Settings", new=MagicMock(), create=True):
            with patch("services.rag_service.embedding_functions", new=mock_embedding_funcs, create=True):
                with patch("services.rag_service.genai.embed_content"):
                    service = ConstitutionRAG()
                    return service


@pytest.fixture
def mock_chromadb():
    """Mock ChromaDB client."""
    # Return a client factory mock
    mock_chromadb = MagicMock()
    mock_chromadb.Client = MagicMock()
    with patch("services.rag_service.chromadb", new=mock_chromadb):
        yield mock_chromadb


@pytest.fixture
def mock_embeddings():
    """Mock embeddings model."""
    with patch("services.rag_service.genai.embed_content") as mock:
        yield mock


class TestRetrievalResult:
    """Test retrieval result model."""

    def test_retrieval_result_citation_formatting(self):
        """Test citation formatting."""
        metadata = {
            "chapter": "4",
            "chapter_title": "The Bill of Rights",
            "article": 33,
            "article_title": "Human dignity"
        }
        
        result = RetrievalResult(
            content="All persons have inherent dignity",
            metadata=metadata,
            score=0.95
        )
        
        assert result.content == "All persons have inherent dignity"
        assert "Chapter 4" in result.citation
        assert "Article 33" in result.citation

    def test_retrieval_result_minimal_metadata(self):
        """Test citation with minimal metadata."""
        metadata = {
            "chapter": "2",
        }
        
        result = RetrievalResult(
            content="Some content",
            metadata=metadata,
            score=0.87
        )
        
        assert "Constitution of Kenya 2010" in result.citation
        assert "Chapter 2" in result.citation

    def test_retrieval_result_to_dict(self):
        """Test conversion to dictionary."""
        metadata = {"chapter": "3"}
        result = RetrievalResult("Test content", metadata, 0.92)
        
        result_dict = result.to_dict()
        
        assert result_dict["content"] == "Test content"
        assert result_dict["score"] == 0.92
        assert "citation" in result_dict


class TestConstitutionRAG:
    """Test RAG service."""

    def test_initialize_creates_collection(self, rag_service):
        """Test collection initialization."""
        assert rag_service is not None

    def test_is_initialized_false_initially(self, rag_service):
        """Test is_initialized before initialization."""
        result = rag_service.is_initialized()
        assert result is False

    def test_initialize_database_success(self, rag_service):
        """Test successful database initialization."""
        # Patch ConstitutionLoader to avoid filesystem dependency
        loader_mock = MagicMock()
        chunk1 = MagicMock(content="Chunk 1", metadata={"chapter": 1}, chunk_id="c1")
        chunk2 = MagicMock(content="Chunk 2", metadata={"chapter": 2}, chunk_id="c2")
        loader_mock.load_and_chunk.return_value = [chunk1, chunk2]

        # Simulate an empty collection (not initialized)
        rag_service.collection = MagicMock()
        rag_service.collection.count.return_value = 0

        with patch("services.rag_service.ConstitutionLoader", return_value=loader_mock):
            result = rag_service.initialize_database()

            assert result["status"] == "success"

    def test_initialize_database_force_rebuild(self, rag_service):
        """Test force rebuilding database."""
        loader_mock = MagicMock()
        chunk = MagicMock(content="Chunk 1", metadata={"chapter": 1}, chunk_id="c1")
        loader_mock.load_and_chunk.return_value = [chunk]

        rag_service.collection = MagicMock()
        rag_service.collection.count.return_value = 1

        with patch("services.rag_service.ConstitutionLoader", return_value=loader_mock):
            result = rag_service.initialize_database(force_rebuild=True)
            
            assert result["status"] == "success"

    def test_query_success(self, rag_service):
        """Test successful document query."""
        # Ensure collection appears initialized
        rag_service.collection = MagicMock()
        rag_service.collection.count.return_value = 1

        # Mock query results in ChromaDB format
        rag_service.collection.query.return_value = {
            'documents': [["Article 1 content", "Article 2 content"]],
            'metadatas': [[{"article": 1}, {"article": 2}]],
            'distances': [[0.1, 0.2]]
        }

        results = rag_service.query(
            "What are the rights?",
            top_k=2
        )

        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0].content == "Article 1 content"
        assert results[1].metadata["article"] == 2

    def test_query_with_chapter_filter(self, rag_service):
        """Test query with chapter filtering."""
        rag_service.collection = MagicMock()
        rag_service.collection.count.return_value = 1

        rag_service.collection.query.return_value = {
            'documents': [["Chapter 2 content"]],
            'metadatas': [[{"chapter": 2}]],
            'distances': [[0.08]]
        }

        results = rag_service.query(
            "Find about chapter 2",
            filter_metadata={"chapter": 2}
        )

        assert isinstance(results, list)
        assert results[0].metadata["chapter"] == 2

    def test_query_empty_string(self, rag_service):
        """Test query with empty string."""
        rag_service.collection = MagicMock()
        rag_service.collection.count.return_value = 1

        rag_service.collection.query.return_value = {
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }

        result = rag_service.query("")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_context_for_query(self, rag_service):
        """Test getting context for a query."""
        rag_service.collection = MagicMock()
        rag_service.collection.count.return_value = 1

        rag_service.collection.query.return_value = {
            'documents': [["Context 1", "Context 2"]],
            'metadatas': [[{}, {}]],
            'distances': [[0.12, 0.15]]
        }

        context, citations = rag_service.get_context_for_query("How many articles?")

        assert isinstance(context, str)
        assert isinstance(citations, list)
        assert "Context 1" in context

    def test_get_stats(self, rag_service):
        """Test getting service statistics."""
        rag_service.collection = MagicMock()
        rag_service.collection.count.return_value = 250
        rag_service.collection.peek.return_value = {
            'metadatas': [{"chapter": "1"}, {"chapter": "2"}]
        }

        result = rag_service.get_stats()

        assert result.get("total_chunks") == 250
        assert "sample_chapters" in result

    def test_search_by_chapter(self, rag_service):
        """Test searching by chapter."""
        rag_service.collection = MagicMock()
        rag_service.collection.get.return_value = {
            'documents': ["Chapter content"],
            'metadatas': [{"chapter": "3"}]
        }

        result = rag_service.search_by_chapter("3")

        assert isinstance(result, list)
        assert result[0].metadata["chapter"] == "3"

    def test_search_by_chapter_with_query(self, rag_service):
        """Test searching by chapter with additional query."""
        rag_service.collection = MagicMock()
        rag_service.collection.count.return_value = 1

        rag_service.collection.query.return_value = {
            'documents': [["Article about rights"]],
            'metadatas': [[{"chapter": "4"}]],
            'distances': [[0.05]]
        }

        result = rag_service.search_by_chapter("4", query="rights")

        assert isinstance(result, list)
        assert result[0].metadata["chapter"] == "4"

    def test_multiple_queries_consistency(self, rag_service):
        """Test that multiple queries return consistent results."""
        rag_service.collection = MagicMock()
        rag_service.collection.count.return_value = 1

        rag_service.collection.query.return_value = {
            'documents': [["Result 1"]],
            'metadatas': [[{}]],
            'distances': [[0.1]]
        }

        result1 = rag_service.query("test query 1")
        result2 = rag_service.query("test query 2")

        assert isinstance(result1, list)
        assert isinstance(result2, list)
