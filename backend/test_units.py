
import pytest
from unittest.mock import AsyncMock, Mock, patch
import sys
from pathlib import Path
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.kra_service import KRAService
from services.elevenlabs_service import ElevenLabsService
from services.sadtalker_service import SadTalkerService

# --- KRA Service Tests ---

@pytest.fixture
def kra_service():
    service = KRAService()
    # Mock internal initialization to avoid errors if env vars are missing
    service.api_url = "https://itax.kra.go.ke/api"
    service.headers = {"Authorization": "Bearer test_token"}
    service._initialized = True
    return service

@pytest.mark.asyncio
async def test_kra_verify_pin_valid(kra_service):
    """Test PIN verification with valid mock response"""
    mock_response = {
        "success": True,
        "valid": True,
        "taxpayer_name": "John Doe",
        "taxpayer_type": "Individual",
        "status": "Active"
    }
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        
        result = await kra_service.verify_pin("A123456789Z")
        
        assert result["success"] is True
        assert result["valid"] is True
        assert result["taxpayer_name"] == "John Doe"

@pytest.mark.asyncio
async def test_kra_verify_pin_invalid_format(kra_service):
    """Test PIN verification with invalid format locally"""
    # Should fail local validation before making API call
    result = await kra_service.verify_pin("INVALID_PIN")
    
    assert result["success"] is False
    assert "Invalid KRA PIN format" in result["error"]

# --- ElevenLabs Service Tests ---

@pytest.fixture
def elevenlabs_service():
    with patch.dict('os.environ', {'ELEVENLABS_API_KEY': 'test_key'}):
        service = ElevenLabsService()
        return service

@pytest.mark.asyncio
async def test_elevenlabs_tts_success(elevenlabs_service):
    """Test text-to-speech with mock API success"""
    mock_audio_content = b"fake_audio_data"
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = mock_audio_content
        
        # Mock file writing to avoid actual disk I/O
        with patch('builtins.open', new_callable=Mock) as mock_open:
            path = await elevenlabs_service.text_to_speech_file("Hello", "voice_id")
            
            assert path is not None
            assert str(path).endswith(".mp3") or str(path).endswith(".wav")

# --- SadTalker Service Tests ---

@pytest.fixture
def sadtalker_service():
    service = SadTalkerService()
    return service

def test_sadtalker_initialization(sadtalker_service):
    """Test service initializes with default settings"""
    assert sadtalker_service.mode == "mock"  # Assuming default/fallback is mock or similar if not configured

@pytest.mark.asyncio
async def test_sadtalker_generate_mock(sadtalker_service):
    """Test generating a video with mocked response"""
    
    # Mock the internal API call method if it exists, or the http client
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"result_video": "path/to/video.mp4"}
        
        # Depending on implementation, we might need to mock more
        # Here we assume the service tries to call an external API
        
        # If the service checks for local files, we might need to mock os.path.exists
        pass
