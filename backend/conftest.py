"""
Pytest configuration and shared fixtures for Rafiki.ai backend tests.
Provides common test utilities, mocks, and database setup.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from ..database import Base, get_db

# Mock optional heavy dependencies to avoid import-time failures during test collection
# (e.g., PyPDF2 / pypdf used by ConstitutionLoader). Insert simple Mock modules so
# imports succeed and tests can patch the loader behavior as needed.
for _module in ("pypdf", "PyPDF2"):
    if _module not in sys.modules:
        sys.modules[_module] = Mock()
        setattr(sys.modules[_module], "PdfReader", Mock())

from main import app
from ..config import get_settings


# ============== Database Fixtures ==============

@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    Create a fresh in-memory SQLite database for each test.
    Automatically rolls back after each test.
    """
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI TestClient with test database.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ============== Mock Service Fixtures ==============

@pytest.fixture
def mock_africas_talking():
    """Mock Africa's Talking SMS service."""
    with patch('africastalking.initialize') as mock_init:
        mock_sms = Mock()
        mock_sms.send.return_value = {
            'SMSMessageData': {
                'Recipients': [{
                    'statusCode': 101,
                    'status': 'Success',
                    'messageId': 'test-message-id'
                }]
            }
        }
        mock_init.return_value = Mock(SMS=mock_sms)
        yield mock_sms


@pytest.fixture
def mock_elevenlabs():
    """Mock ElevenLabs API."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_audio_data"
        mock_response.json.return_value = {"audio": "base64_encoded"}
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        yield mock_client


@pytest.fixture
def mock_google_genai():
    """Mock Google Gemini API."""
    with patch('google.genai.configure') as mock_config, \
         patch('google.genai.GenerativeModel') as mock_model:
        
        mock_response = Mock()
        mock_response.text = "This is a test response from Gemini."
        
        mock_instance = Mock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        yield mock_model


@pytest.fixture
def mock_kra_api():
    """Mock KRA iTax API."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "valid": True,
            "taxpayer_name": "John Doe",
            "taxpayer_type": "Individual",
            "status": "Active"
        }
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        yield mock_client


@pytest.fixture
def mock_dialogflow():
    """Mock Google Dialogflow API."""
    with patch('google.cloud.dialogflow_v2.SessionsClient') as mock_client:
        mock_response = Mock()
        mock_response.query_result.intent.display_name = "test_intent"
        mock_response.query_result.fulfillment_text = "Test response"
        mock_response.query_result.parameters = {}
        
        mock_instance = Mock()
        mock_instance.detect_intent.return_value = mock_response
        mock_client.return_value = mock_instance
        
        yield mock_client


# ============== Test Data Fixtures ==============

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "phone_number": "+254712345678",
        "phone_hash": "hashed_phone_123",
        "user_id": "user_test_123",
        "created_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_otp_data():
    """Sample OTP data for testing."""
    return {
        "phone_number": "+254712345678",
        "otp_code": "123456",
        "expires_at": datetime.utcnow() + timedelta(minutes=5),
    }


@pytest.fixture
def sample_jwt_token():
    """Sample JWT token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX3Rlc3RfMTIzIiwiZXhwIjoxNzM4Mzk1NjAwfQ.test"


@pytest.fixture
def sample_booking_data():
    """Sample booking data for testing."""
    from datetime import date
    return {
        "service_type": "passport",
        "user_name": "John Doe",
        "phone_number": "+254712345678",
        # Use the correct TimeSlot enum value as string
        "time_slot": "08:00-12:00",
        "appointment_date": date.today() + timedelta(days=7),
        "additional_notes": "First time applicant"
    }


@pytest.fixture
def sample_kra_pin():
    """Sample KRA PIN for testing."""
    return "A123456789Z"


# ============== Utility Fixtures ==============

@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    with patch('datetime.datetime') as mock_dt:
        mock_dt.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        mock_dt.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
        yield mock_dt


@pytest.fixture
def mock_file_operations():
    """Mock file I/O operations."""
    with patch('builtins.open', create=True) as mock_open, \
         patch('os.makedirs') as mock_makedirs, \
         patch('os.path.exists') as mock_exists:
        
        mock_exists.return_value = True
        yield {
            'open': mock_open,
            'makedirs': mock_makedirs,
            'exists': mock_exists
        }


# ============== Event Loop Fixture ==============

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============== Authorization Headers ==============

@pytest.fixture
def auth_headers(sample_jwt_token):
    """Authorization headers with JWT token."""
    return {"Authorization": f"Bearer {sample_jwt_token}"}
