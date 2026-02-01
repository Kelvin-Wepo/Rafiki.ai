"""Tests for authentication routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from main import app
from models.user import PhoneAuthRequest, OTPVerifyRequest


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth_service():
    """Mock auth service."""
    with patch("routes.auth.get_auth_service") as mock:
        service = AsyncMock()
        mock.return_value = service
        yield service


class TestAuthRoutes:
    """Test authentication endpoints."""

    def test_initiate_login_success(self, client, mock_auth_service):
        """Test successful OTP request."""
        mock_auth_service.initiate_login.return_value = {
            "success": True,
            "message": "OTP sent",
            "otp_request_id": "req_123",
            "phone_hash": "hash_123"
        }
        
        response = client.post(
            "/auth/login",
            json={"phone_number": "+254712345678"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "otp_request_id" in data

    def test_initiate_login_invalid_phone(self, client, mock_auth_service):
        """Test login with invalid phone format."""
        mock_auth_service.initiate_login.return_value = {
            "success": False,
            "error": "Invalid phone format"
        }
        
        response = client.post(
            "/auth/login",
            json={"phone_number": "invalid"}
        )
        
        assert response.status_code == 400

    def test_initiate_login_rate_limited(self, client, mock_auth_service):
        """Test OTP request rate limiting."""
        mock_auth_service.initiate_login.return_value = {
            "success": False,
            "error": "Rate limit exceeded",
            "retry_after": 300
        }
        
        response = client.post(
            "/auth/login",
            json={"phone_number": "+254712345678"}
        )
        
        assert response.status_code == 429

    def test_verify_otp_success(self, client, mock_auth_service):
        """Test successful OTP verification."""
        mock_auth_service.verify_and_login.return_value = {
            "success": True,
            "message": "Login successful",
            "access_token": "eyJhbGc...",
            "user_id": "usr_123",
            "phone_number": "+254712345678"
        }
        
        response = client.post(
            "/auth/verify",
            json={
                "phone_number": "+254712345678",
                "otp": "123456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data

    def test_verify_otp_invalid(self, client, mock_auth_service):
        """Test OTP verification with invalid code."""
        mock_auth_service.verify_and_login.return_value = {
            "success": False,
            "error": "Invalid OTP"
        }
        
        response = client.post(
            "/auth/verify",
            json={
                "phone_number": "+254712345678",
                "otp": "000000"
            }
        )
        
        assert response.status_code == 401

    def test_verify_otp_expired(self, client, mock_auth_service):
        """Test OTP verification with expired code."""
        mock_auth_service.verify_and_login.return_value = {
            "success": False,
            "error": "OTP expired"
        }
        
        response = client.post(
            "/auth/verify",
            json={
                "phone_number": "+254712345678",
                "otp": "123456"
            }
        )
        
        assert response.status_code == 401

    def test_validate_token_valid(self, client, mock_auth_service):
        """Test token validation with valid token."""
        mock_auth_service.validate_token.return_value = {
            "user_id": "usr_123",
            "phone_number": "+254712345678",
            "valid": True
        }
        
        response = client.post(
            "/auth/validate",
            json={"token": "eyJhbGc..."}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_token_invalid(self, client, mock_auth_service):
        """Test token validation with invalid token."""
        mock_auth_service.validate_token.return_value = None
        
        response = client.post(
            "/auth/validate",
            json={"token": "invalid_token"}
        )
        
        assert response.status_code == 401

    def test_logout_success(self, client, mock_auth_service):
        """Test successful logout."""
        mock_auth_service.logout.return_value = {
            "success": True,
            "message": "Logged out successfully"
        }
        
        response = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer eyJhbGc..."}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_missing_authorization_header(self, client):
        """Test endpoint requiring auth without header."""
        response = client.post("/auth/logout")
        
        assert response.status_code == 401

    def test_create_conversation_authenticated(self, client, mock_auth_service):
        """Test creating conversation when authenticated."""
        mock_auth_service.validate_token.return_value = {
            "user_id": "usr_123"
        }
        mock_auth_service.create_conversation.return_value = {
            "conversation_id": "conv_456",
            "user_id": "usr_123",
            "created_at": datetime.now().isoformat()
        }
        
        response = client.post(
            "/auth/conversations",
            headers={"Authorization": "Bearer token123"},
            json={
                "title": "Test Conversation",
                "context": "Test context"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "conv_456"
