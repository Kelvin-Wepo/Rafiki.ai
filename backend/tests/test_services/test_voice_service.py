"""Tests for voice and TTS services."""

import pytest
from unittest.mock import MagicMock, patch

from services.voice_service import VoiceService


@pytest.fixture
def voice_service():
    """Create voice service instance."""
    return VoiceService()


class TestVoiceService:
    """Test voice service."""

    def test_voice_service_initialization(self):
        """Test voice service basic initialization."""
        with patch("services.voice_service.SPEECH_RECOGNITION_AVAILABLE", False):
            with patch("services.voice_service.PYTTSX3_AVAILABLE", False):
                service = VoiceService()
                assert service is not None
                assert service._recognizer is None
                assert service._tts_engine is None
                assert service._initialized is False

    def test_speech_recognition_not_available(self):
        """Test when speech recognition unavailable."""
        with patch("services.voice_service.SPEECH_RECOGNITION_AVAILABLE", False):
            with patch("services.voice_service.PYTTSX3_AVAILABLE", False):
                service = VoiceService()
                result = service.initialize()
                assert result is True
                assert service._recognizer is None

    def test_tts_not_available(self):
        """Test when TTS engine unavailable."""
        with patch("services.voice_service.SPEECH_RECOGNITION_AVAILABLE", False):
            with patch("services.voice_service.PYTTSX3_AVAILABLE", False):
                service = VoiceService()
                result = service.initialize()
                assert result is True
                assert service._tts_engine is None

    def test_speak_text_with_available_engine(self, voice_service):
        """Test speak_text with available TTS engine."""
        voice_service._tts_engine = MagicMock()
        voice_service._initialized = True
        
        with patch("services.voice_service.PYTTSX3_AVAILABLE", True):
            result = voice_service.speak_text("Hello world")
        
        assert result is True

    def test_speak_text_without_engine(self, voice_service):
        """Test speak_text without TTS engine."""
        voice_service._tts_engine = None
        
        result = voice_service.speak_text("Hello")
        
        assert result is False

    def test_speak_text_empty_string(self, voice_service):
        """Test speak_text with empty string."""
        voice_service._tts_engine = MagicMock()
        voice_service._initialized = True
        
        result = voice_service.speak_text("")
        
        assert result is False

    def test_get_available_voices(self, voice_service):
        """Test getting available voices."""
        mock_voice = MagicMock()
        mock_voice.id = "voice1"
        mock_voice.name = "English"
        
        voice_service._tts_engine = MagicMock()
        voice_service._tts_engine.getProperty.return_value = [mock_voice]
        
        result = voice_service.get_available_voices()
        
        assert isinstance(result, list)

    def test_set_voice_properties_rate(self, voice_service):
        """Test setting voice rate."""
        voice_service._tts_engine = MagicMock()
        
        voice_service.set_voice_properties(rate=100)
        
        assert voice_service._tts_engine is not None

    def test_set_voice_properties_volume(self, voice_service):
        """Test setting voice volume."""
        voice_service._tts_engine = MagicMock()
        
        voice_service.set_voice_properties(volume=0.8)
        
        assert voice_service._tts_engine is not None

    def test_settings_initialization(self, voice_service):
        """Test settings are loaded."""
        assert voice_service.settings is not None

    def test_multiple_speak_calls(self, voice_service):
        """Test multiple speak calls."""
        voice_service._tts_engine = MagicMock()
        voice_service._initialized = True
        
        with patch("services.voice_service.PYTTSX3_AVAILABLE", True):
            result1 = voice_service.speak_text("First")
            result2 = voice_service.speak_text("Second")
            result3 = voice_service.speak_text("Third")
        
        assert result1 is True
        assert result2 is True
        assert result3 is True


