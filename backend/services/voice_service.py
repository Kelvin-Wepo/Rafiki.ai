"""
Voice processing service for speech recognition and text-to-speech.
"""

import io
import base64
import asyncio
from typing import Dict, Any, Optional
import tempfile
import os

from config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import speech libraries
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.warning("speech_recognition library not installed")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 library not installed")


class VoiceService:
    """
    Service for voice input/output processing.
    Handles speech recognition and text-to-speech.
    """
    
    def __init__(self):
        """Initialize voice service."""
        self.settings = get_settings()
        self._recognizer = None
        self._tts_engine = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize voice processing components.
        
        Returns:
            True if initialization successful
        """
        try:
            # Initialize speech recognizer
            if SPEECH_RECOGNITION_AVAILABLE:
                self._recognizer = sr.Recognizer()
                self._recognizer.pause_threshold = 0.8
                self._recognizer.phrase_threshold = 0.3
                self._recognizer.non_speaking_duration = 0.5
                logger.info("Speech recognizer initialized")
            else:
                logger.warning("Speech recognition not available")
            
            # Initialize TTS engine
            if PYTTSX3_AVAILABLE:
                try:
                    # Try espeak on Linux
                    self._tts_engine = pyttsx3.init('espeak')
                except Exception:
                    try:
                        # Fallback to default
                        self._tts_engine = pyttsx3.init()
                    except Exception as e:
                        logger.warning(f"Could not initialize TTS engine: {e}")
                        self._tts_engine = None
                
                if self._tts_engine:
                    # Configure TTS
                    self._tts_engine.setProperty('rate', self.settings.TTS_RATE)
                    
                    # Try to set voice
                    try:
                        voices = self._tts_engine.getProperty('voices')
                        if voices and len(voices) > self.settings.TTS_VOICE_ID:
                            self._tts_engine.setProperty(
                                'voice', 
                                voices[self.settings.TTS_VOICE_ID].id
                            )
                    except Exception as e:
                        logger.warning(f"Could not set TTS voice: {e}")
                    
                    logger.info("TTS engine initialized")
            else:
                logger.warning("TTS not available")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize voice service: {e}")
            return False
    
    async def transcribe_audio(
        self,
        audio_data: str,
        audio_format: str = "wav",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Base64 encoded audio data
            audio_format: Audio format (wav, mp3, etc.)
            language: Language code for recognition
        
        Returns:
            Transcription result with text and confidence
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            return {
                "success": False,
                "error": "Speech recognition not available"
            }
        
        if not self._initialized:
            self.initialize()
        
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(
                suffix=f".{audio_format}",
                delete=False
            ) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            try:
                # Load audio file
                with sr.AudioFile(temp_path) as source:
                    audio = self._recognizer.record(source)
                
                # Recognize speech
                lang = language or self.settings.SPEECH_RECOGNITION_LANGUAGE
                
                # Try Google Speech Recognition
                text = self._recognizer.recognize_google(audio, language=lang)
                
                logger.info(f"Transcribed: {text[:50]}...")
                
                return {
                    "success": True,
                    "text": text,
                    "confidence": 0.9,  # Google doesn't provide confidence
                    "language": lang
                }
                
            finally:
                # Clean up temp file
                os.unlink(temp_path)
            
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return {
                "success": False,
                "error": "Could not understand audio",
                "text": ""
            }
        except sr.RequestError as e:
            logger.error(f"Speech recognition request failed: {e}")
            return {
                "success": False,
                "error": f"Speech recognition service error: {e}"
            }
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def transcribe_from_microphone(
        self,
        timeout: int = 10,
        phrase_time_limit: int = 30,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe speech from microphone.
        
        Args:
            timeout: Seconds to wait for phrase to start
            phrase_time_limit: Maximum phrase length in seconds
            language: Language code for recognition
        
        Returns:
            Transcription result
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            return {
                "success": False,
                "error": "Speech recognition not available"
            }
        
        if not self._initialized:
            self.initialize()
        
        try:
            with sr.Microphone() as source:
                logger.info("Adjusting for ambient noise...")
                self._recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info("Listening...")
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            # Recognize speech
            lang = language or self.settings.SPEECH_RECOGNITION_LANGUAGE
            text = self._recognizer.recognize_google(audio, language=lang)
            
            logger.info(f"Transcribed from mic: {text[:50]}...")
            
            return {
                "success": True,
                "text": text,
                "confidence": 0.9,
                "language": lang
            }
            
        except sr.WaitTimeoutError:
            return {
                "success": False,
                "error": "No speech detected within timeout",
                "text": ""
            }
        except sr.UnknownValueError:
            return {
                "success": False,
                "error": "Could not understand audio",
                "text": ""
            }
        except sr.RequestError as e:
            logger.error(f"Speech recognition request failed: {e}")
            return {
                "success": False,
                "error": f"Speech recognition service error: {e}"
            }
        except Exception as e:
            logger.error(f"Microphone transcription error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def text_to_speech(
        self,
        text: str,
        output_format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert to speech
            output_format: Output audio format
        
        Returns:
            Audio data in base64 format
        """
        if not PYTTSX3_AVAILABLE or not self._tts_engine:
            return {
                "success": False,
                "error": "Text-to-speech not available"
            }
        
        if not self._initialized:
            self.initialize()
        
        try:
            # Create temp file for audio output
            with tempfile.NamedTemporaryFile(
                suffix=f".{output_format}",
                delete=False
            ) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Generate speech to file
                self._tts_engine.save_to_file(text, temp_path)
                self._tts_engine.runAndWait()
                
                # Read the file
                with open(temp_path, 'rb') as f:
                    audio_bytes = f.read()
                
                # Encode to base64
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                
                return {
                    "success": True,
                    "audio_data": audio_base64,
                    "audio_format": output_format,
                    "text": text
                }
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def speak_text(self, text: str) -> bool:
        """
        Speak text directly through speakers (synchronous).
        
        Args:
            text: Text to speak
        
        Returns:
            True if successful
        """
        if not PYTTSX3_AVAILABLE or not self._tts_engine:
            logger.warning("TTS not available for speaking")
            return False
        
        if not self._initialized:
            self.initialize()
        
        try:
            self._tts_engine.say(text)
            self._tts_engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"Error speaking text: {e}")
            return False
    
    def get_available_voices(self) -> list:
        """Get list of available TTS voices."""
        if not PYTTSX3_AVAILABLE or not self._tts_engine:
            return []
        
        if not self._initialized:
            self.initialize()
        
        try:
            voices = self._tts_engine.getProperty('voices')
            return [
                {
                    "id": i,
                    "name": voice.name,
                    "languages": getattr(voice, 'languages', []),
                    "gender": getattr(voice, 'gender', 'unknown')
                }
                for i, voice in enumerate(voices)
            ]
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []
    
    def set_voice_properties(
        self,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
        voice_id: Optional[int] = None
    ) -> bool:
        """
        Set TTS voice properties.
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume (0.0 to 1.0)
            voice_id: Voice index
        
        Returns:
            True if successful
        """
        if not self._tts_engine:
            return False
        
        try:
            if rate is not None:
                self._tts_engine.setProperty('rate', rate)
            
            if volume is not None:
                self._tts_engine.setProperty('volume', max(0.0, min(1.0, volume)))
            
            if voice_id is not None:
                voices = self._tts_engine.getProperty('voices')
                if voices and 0 <= voice_id < len(voices):
                    self._tts_engine.setProperty('voice', voices[voice_id].id)
            
            return True
        except Exception as e:
            logger.error(f"Error setting voice properties: {e}")
            return False


# Global service instance
voice_service = VoiceService()
