"""
Google Cloud Text-to-Speech Service
Provides natural voice synthesis using Google Cloud TTS API
"""

import os
import tempfile
from typing import Optional
from google.cloud import texttospeech
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleTTSService:
    """
    Service for Google Cloud Text-to-Speech integration.
    Provides high-quality, natural-sounding voice synthesis.
    """
    
    def __init__(self):
        """Initialize Google TTS service."""
        self.settings = get_settings()
        self._client = None
        self._initialized = False
        
        # Available voices with Kenyan/African accents
        self.VOICES = {
            "en-GB-Neural2-A": {
                "name": "British Female (Neural)",
                "gender": "FEMALE",
                "language": "en-GB",
                "description": "Clear, professional female voice"
            },
            "en-GB-Neural2-B": {
                "name": "British Male (Neural)",
                "gender": "MALE",
                "language": "en-GB",
                "description": "Warm, natural male voice"
            },
            "en-US-Neural2-C": {
                "name": "American Female (Neural)",
                "gender": "FEMALE",
                "language": "en-US",
                "description": "Natural, friendly female voice"
            },
            "en-US-Neural2-D": {
                "name": "American Male (Neural)",
                "gender": "MALE",
                "language": "en-US",
                "description": "Confident, clear male voice"
            },
            "en-US-Neural2-J": {
                "name": "American Male Casual (Neural)",
                "gender": "MALE",
                "language": "en-US",
                "description": "Warm, conversational male voice"
            }
        }
        
        # Default voice - warm, natural male voice
        self.default_voice = "en-US-Neural2-J"
    
    def initialize(self) -> bool:
        """
        Initialize the Google TTS client.
        
        Returns:
            True if initialization successful
        """
        try:
            # Prefer service account credentials (GOOGLE_APPLICATION_CREDENTIALS); fall back to API key if provided
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if credentials_path:
                self._client = texttospeech.TextToSpeechClient()
                self._initialized = True
                logger.info("Google Cloud TTS service initialized successfully using service account credentials")
                return True

            # If no service account JSON is provided, allow initializing with an API key
            if self.settings.GOOGLE_API_KEY:
                try:
                    from google.api_core.client_options import ClientOptions
                    client_options = ClientOptions(api_key=self.settings.GOOGLE_API_KEY)
                    self._client = texttospeech.TextToSpeechClient(client_options=client_options)
                    self._initialized = True
                    logger.info("Google Cloud TTS service initialized using API key")
                    return True
                except Exception as e:
                    logger.error(f"Failed to initialize Google Cloud TTS with API key: {e}")
                    return False

            logger.warning("Google Cloud credentials not configured for TTS (set GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_API_KEY)")
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud TTS: {e}")
            return False
    
    async def text_to_speech(
        self,
        text: str,
        voice_name: Optional[str] = None,
        language: str = "en",
        speaking_rate: float = 1.0,
        pitch: float = 0.0
    ) -> Optional[bytes]:
        """
        Convert text to speech using Google Cloud TTS.
        
        Args:
            text: Text to convert to speech
            voice_name: Voice to use (defaults to warm male voice)
            language: Language code
            speaking_rate: Speaking rate (0.25 to 4.0)
            pitch: Voice pitch adjustment (-20.0 to 20.0)
            
        Returns:
            Audio data in MP3 format, or None on error
        """
        if not self._initialized:
            if not self.initialize():
                return None
        
        try:
            # Select voice
            if not voice_name or voice_name not in self.VOICES:
                voice_name = self.default_voice
            
            voice_config = self.VOICES[voice_name]
            
            # Set up the synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure the voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config["language"],
                name=voice_name,
                ssml_gender=getattr(
                    texttospeech.SsmlVoiceGender, 
                    voice_config["gender"]
                )
            )
            
            # Configure audio output
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
                pitch=pitch,
                effects_profile_id=["small-bluetooth-speaker-class-device"]
            )
            
            # Perform the text-to-speech request
            response = self._client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            logger.info(f"Generated TTS audio with Google Cloud (voice: {voice_name})")
            return response.audio_content
            
        except Exception as e:
            logger.error(f"Google Cloud TTS failed: {e}")
            return None
    
    async def text_to_speech_file(
        self,
        text: str,
        voice_name: Optional[str] = None,
        language: str = "en"
    ) -> Optional[str]:
        """
        Convert text to speech and save to a temporary file.
        
        Args:
            text: Text to convert to speech
            voice_name: Voice to use
            language: Language code
            
        Returns:
            Path to the generated audio file, or None on error
        """
        try:
            audio_data = await self.text_to_speech(text, voice_name, language)
            
            if not audio_data:
                return None
            
            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".mp3",
                delete=False
            )
            temp_file.write(audio_data)
            temp_file.close()
            
            logger.info(f"Generated TTS audio file (Google Cloud): {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Google Cloud TTS file generation error: {e}")
            return None
    
    def get_available_voices(self):
        """Get list of available voices."""
        return self.VOICES


# Create singleton instance
google_tts_service = GoogleTTSService()
