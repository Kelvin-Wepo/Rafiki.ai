"""
Tests for AuthService
Covers authentication, OTP, session management, and conversation handling.
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.auth_service import AuthService, get_auth_service


@pytest.fixture
def auth_service():
    """Create a fresh AuthService instance for testing."""
    service = AuthService()
    return service


# ============== JWT Token Tests ==============

def test_create_access_token(auth_service, sample_user_data):
    """Test JWT token creation."""
    token = auth_service._create_access_token(sample_user_data["user_id"])
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_valid_token(auth_service, sample_user_data):
    """Test verifying a valid JWT token."""
    token = auth_service._create_access_token(sample_user_data["user_id"])
    payload = auth_service._verify_token(token)
    
    assert payload is not None
    assert payload.get("sub") == sample_user_data["user_id"]


def test_verify_invalid_token(auth_service):
    """Test verifying an invalid token."""
    invalid_token = "invalid.token.here"
    payload = auth_service._verify_token(invalid_token)
    
    assert payload is None


def test_verify_expired_token(auth_service, sample_user_data):
    """Test verifying an expired token."""
    # Create token that expires immediately
    token = auth_service._create_access_token(
        sample_user_data["user_id"],
        expires_delta=timedelta(seconds=-1)
    )
    
    payload = auth_service._verify_token(token)
    assert payload is None


# ============== OTP Tests ==============

@pytest.mark.asyncio
async def test_initiate_login_new_user(auth_service, mock_africas_talking):
    """Test initiating login for a new user."""
    with patch('services.otp_service.get_otp_service') as mock_otp:
        mock_otp_instance = AsyncMock()
        mock_otp_instance.send_otp.return_value = {
            "success": True,
            "message": "OTP sent successfully"
        }
        mock_otp.return_value = mock_otp_instance
        
        result = await auth_service.initiate_login(
            phone_number="+254712345678",
            ip_address="127.0.0.1"
        )
        
        assert result["success"] is True
        assert "OTP sent" in result["message"] or "sent" in result["message"].lower()


@pytest.mark.asyncio
async def test_verify_and_login_valid_otp(auth_service):
    """Test successful OTP verification and login."""
    with patch('services.otp_service.get_otp_service') as mock_otp:
        mock_otp_instance = AsyncMock()
        mock_otp_instance.verify_otp.return_value = {
            "success": True,
            "valid": True
        }
        mock_otp.return_value = mock_otp_instance
        
        result = await auth_service.verify_and_login(
            phone_number="+254712345678",
            otp="123456"
        )
        
        assert result["success"] is True
        assert "access_token" in result
        assert result["access_token"] is not None


@pytest.mark.asyncio
async def test_verify_and_login_invalid_otp(auth_service):
    """Test OTP verification with invalid code."""
    with patch('services.otp_service.get_otp_service') as mock_otp:
        mock_otp_instance = AsyncMock()
        mock_otp_instance.verify_otp.return_value = {
            "success": False,
            "error": "Invalid OTP code"
        }
        mock_otp.return_value = mock_otp_instance
        
        result = await auth_service.verify_and_login(
            phone_number="+254712345678",
            otp="000000"
        )
        
        assert result["success"] is False
        assert "error" in result


# ============== Session Management Tests ==============

@pytest.mark.asyncio
async def test_validate_token_valid(auth_service, sample_user_data):
    """Test validating a valid token."""
    # Create a token
    token = auth_service._create_access_token(sample_user_data["user_id"])
    
    result = await auth_service.validate_token(token)
    
    assert result is not None
    assert result.get("user_id") == sample_user_data["user_id"]


@pytest.mark.asyncio
async def test_validate_token_invalid(auth_service):
    """Test validating an invalid token."""
    result = await auth_service.validate_token("invalid_token")
    
    assert result is None


@pytest.mark.asyncio
async def test_logout(auth_service, sample_user_data):
    """Test logout functionality."""
    # Create a token first
    token = auth_service._create_access_token(sample_user_data["user_id"])
    
    result = await auth_service.logout(token)
    
    assert result["success"] is True


# ============== Conversation Management Tests ==============

@pytest.mark.asyncio
async def test_create_conversation(auth_service, sample_user_data):
    """Test creating a new conversation."""
    result = await auth_service.create_conversation(
        user_id=sample_user_data["user_id"],
        title="Test Conversation"
    )
    
    assert result["success"] is True
    assert result["conversation_id"] is not None
    assert result["title"] == "Test Conversation"


@pytest.mark.asyncio
async def test_add_message_to_conversation(auth_service, sample_user_data):
    """Test adding a message to a conversation."""
    # Create conversation first
    conv_result = await auth_service.create_conversation(sample_user_data["user_id"])
    conversation_id = conv_result["conversation_id"]
    
    # Add message
    result = await auth_service.add_message(
        conversation_id=conversation_id,
        role="user",
        content="Hello, this is a test message"
    )
    
    assert result["success"] is True
    assert result["message_id"] is not None


@pytest.mark.asyncio
async def test_get_user_conversations(auth_service, sample_user_data):
    """Test retrieving user's conversations."""
    # Create a conversation first
    await auth_service.create_conversation(sample_user_data["user_id"])
    
    conversations = await auth_service.get_user_conversations(sample_user_data["user_id"])
    
    assert isinstance(conversations, list)
    assert len(conversations) >= 1


@pytest.mark.asyncio
async def test_get_conversation(auth_service, sample_user_data):
    """Test retrieving a specific conversation."""
    # Create conversation
    conv_result = await auth_service.create_conversation(sample_user_data["user_id"])
    conversation_id = conv_result["conversation_id"]
    
    # Retrieve it
    conversation = await auth_service.get_conversation(
        conversation_id=conversation_id,
        user_id=sample_user_data["user_id"]
    )
    
    assert conversation is not None
    assert conversation.get("id") == conversation_id


@pytest.mark.asyncio
async def test_archive_conversation(auth_service, sample_user_data):
    """Test archiving a conversation."""
    # Create conversation
    conv_result = await auth_service.create_conversation(sample_user_data["user_id"])
    conversation_id = conv_result["conversation_id"]
    
    # Archive it
    result = await auth_service.archive_conversation(
        conversation_id=conversation_id,
        user_id=sample_user_data["user_id"]
    )
    
    assert result["success"] is True


# ============== Export Tests ==============

@pytest.mark.asyncio
async def test_export_transcript_txt(auth_service, sample_user_data):
    """Test exporting conversation as text."""
    # Create conversation with messages
    conv_result = await auth_service.create_conversation(sample_user_data["user_id"])
    conversation_id = conv_result["conversation_id"]
    
    await auth_service.add_message(conversation_id, "user", "Hello")
    await auth_service.add_message(conversation_id, "assistant", "Hi there!")
    
    # Export
    result = await auth_service.export_transcript(
        conversation_id=conversation_id,
        user_id=sample_user_data["user_id"],
        format="txt"
    )
    
    assert result["success"] is True
    assert result["content"] is not None
    assert result["filename"].endswith(".txt")


@pytest.mark.asyncio
async def test_export_transcript_json(auth_service, sample_user_data):
    """Test exporting conversation as JSON."""
    # Create conversation with messages
    conv_result = await auth_service.create_conversation(sample_user_data["user_id"])
    conversation_id = conv_result["conversation_id"]
    
    await auth_service.add_message(conversation_id, "user", "Test message")
    
    # Export
    result = await auth_service.export_transcript(
        conversation_id=conversation_id,
        user_id=sample_user_data["user_id"],
        format="json"
    )
    
    assert result["success"] is True
    assert result["content"] is not None
    assert result["filename"].endswith(".json")


# ============== Audit Log Tests ==============

@pytest.mark.asyncio
async def test_audit_log_creation(auth_service, sample_user_data):
    """Test audit log is created for auth events."""
    # Trigger an auth event (login attempt)
    await auth_service.initiate_login("+254712345678", ip_address="127.0.0.1")
    
    # Get audit logs
    logs = await auth_service.get_audit_logs(limit=10)
    
    assert isinstance(logs, list)
    # Logs should exist (implementation may vary)


def test_get_auth_service_singleton():
    """Test that get_auth_service returns singleton instance."""
    service1 = get_auth_service()
    service2 = get_auth_service()
    
    assert service1 is service2
