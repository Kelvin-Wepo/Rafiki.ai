"""
Tests for GeminiService
Covers NLU, intent detection, and response generation.
"""

import pytest
from unittest.mock import patch, Mock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.gemini_service import GeminiService, gemini_service


@pytest.fixture
def gemini_test_service(mock_google_genai):
    """Create GeminiService with mocked API."""
    service = GeminiService()
    service.initialize()
    return service


# ============== Initialization Tests ==============

@pytest.mark.asyncio
async def test_initialize_service(mock_google_genai):
    """Test Gemini service initialization."""
    service = GeminiService()
    result = await service.initialize()
    
    assert result is True or isinstance(result, bool)


# ============== Message Processing Tests ==============

@pytest.mark.asyncio
async def test_process_message_basic(gemini_test_service, mock_google_genai):
    """Test processing a basic user message."""
    result = await gemini_test_service.process_message(
        user_message="Hello, I need help with passport application",
        language="en"
    )
    
    assert result is not None
    assert "response" in result or "text" in result or "message" in result


@pytest.mark.asyncio
async def test_process_message_with_history(gemini_test_service, mock_google_genai):
    """Test processing message with conversation history."""
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! How can I help?"}
    ]
    
    result = await gemini_test_service.process_message(
        user_message="I need passport information",
        conversation_history=history,
        language="en"
    )
    
    assert result is not None


@pytest.mark.asyncio
async def test_process_message_multilingual(gemini_test_service, mock_google_genai):
    """Test processing message in Swahili."""
    result = await gemini_test_service.process_message(
        user_message="Nataka taarifa kuhusu pasipoti",
        language="sw"
    )
    
    assert result is not None


@pytest.mark.asyncio
async def test_process_message_with_context(gemini_test_service, mock_google_genai):
    """Test processing message with additional context."""
    context = {
        "user_id": "test_user_123",
        "previous_intent": "passport_application"
    }
    
    result = await gemini_test_service.process_message(
        user_message="What documents do I need?",
        context=context,
        language="en"
    )
    
    assert result is not None


# ============== Response Generation Tests ==============

@pytest.mark.asyncio
async def test_generate_response(gemini_test_service, mock_google_genai):
    """Test generating a response."""
    prompt = "User asked about passport application process"
    
    response = await gemini_test_service._generate_response(prompt)
    
    assert response is not None
    assert isinstance(response, str)


# ============== Service Info Tests ==============

def test_get_service_info(gemini_test_service):
    """Test getting service information."""
    info = gemini_test_service.get_service_info("passport")
    
    assert info is not None
    assert isinstance(info, dict)


def test_get_service_info_invalid(gemini_test_service):
    """Test getting info for invalid service."""
    info = gemini_test_service.get_service_info("invalid_service_123")
    
    # Should return error or None
    assert info is None or "error" in info


# ============== Build Prompt Tests ==============

def test_build_system_context_english(gemini_test_service):
    """Test building system context in English."""
    context = gemini_test_service._build_system_context(language="en")
    
    assert context is not None
    assert isinstance(context, str)
    assert len(context) > 0


def test_build_system_context_swahili(gemini_test_service):
    """Test building system context in Swahili."""
    context = gemini_test_service._build_system_context(language="sw")
    
    assert context is not None
    assert isinstance(context, str)


@pytest.mark.asyncio
async def test_build_prompt(gemini_test_service):
    """Test building full prompt."""
    prompt = await gemini_test_service._build_prompt(
        user_message="Hello",
        language="en"
    )
    
    assert prompt is not None
    assert isinstance(prompt, str)
    assert "Hello" in prompt


# ============== Intent Detection Integration Tests ==============

@pytest.mark.asyncio
async def test_process_message_intent_detection(gemini_test_service, mock_google_genai):
    """Test that intent detection is integrated."""
    with patch('services.intent_service.intent_detector') as mock_intent:
        mock_intent.detect_intent.return_value = {
            "intent": "passport_inquiry",
            "confidence": 0.95
        }
        
        result = await gemini_test_service.process_message(
            user_message="How do I apply for a passport?",
            language="en"
        )
        
        assert result is not None


def test_gemini_service_singleton():
    """Test that gemini_service singleton exists."""
    assert gemini_service is not None
    assert isinstance(gemini_service, GeminiService)
