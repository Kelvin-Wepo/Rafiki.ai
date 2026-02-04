"""
Voice processing service for speech recognition and text-to-speech.
"""

import io
import base64
import asyncio
from typing import Dict, Any, Optional
import tempfile
import os

from backend.config import get_settings
from backend.utils.logger import get_logger

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

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub library not installed - WebM format support disabled")


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
                # Tuned for better voice detection
                self._recognizer.pause_threshold = 0.5  # Wait 500ms of silence before ending phrase
                self._recognizer.phrase_threshold = 0.1  # Lower threshold to detect speech earlier
                self._recognizer.non_speaking_duration = 0.3  # Shorter silence tolerance
                self._recognizer.energy_threshold = 4000  # Adjust for noisy environments
                logger.info("Speech recognizer initialized with optimized settings")
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
    
    def _detect_audio_format(self, audio_bytes: bytes) -> str:
        """
        Detect audio format from file headers (magic numbers).
        
        Args:
            audio_bytes: Raw audio data bytes
            
        Returns:
            Detected format ('wav', 'webm', 'mp3', 'flac', or 'unknown')
        """
        if len(audio_bytes) < 4:
            return 'unknown'
        
        # Check for magic numbers
        if audio_bytes[:4] == b'RIFF' and audio_bytes[8:12] == b'WAVE':
            return 'wav'
        elif audio_bytes[:4] == b'\x1aELF':  # Note: FLAC header is 0xfLaC
            return 'flac'
        elif audio_bytes[:3] == b'ID3' or audio_bytes[:2] == b'\xff\xfb':
            return 'mp3'
        elif audio_bytes[:4] == b'\x1a\x45\xdf\xa3':  # EBML header (WebM)
            return 'webm'
        elif audio_bytes[:4] == b'fLaC':
            return 'flac'
        else:
            # Log first bytes for debugging
            logger.warning(f"Unknown audio format. First 16 bytes: {audio_bytes[:16].hex()}")
            return 'unknown'
    
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
            audio_format: Audio format (wav, mp3, webm, etc.)
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
            # Validate audio data is not empty
            if not audio_data:
                logger.warning("Empty audio data provided")
                return {
                    "success": False,
                    "error": "No audio data provided"
                }
            
            # Decode base64 audio
            try:
                audio_bytes = base64.b64decode(audio_data)
            except Exception as e:
                logger.error(f"Failed to decode base64 audio: {e}")
                return {
                    "success": False,
                    "error": f"Invalid audio data format: {e}"
                }
            
            if not audio_bytes:
                logger.warning("Audio bytes are empty after decoding")
                return {
                    "success": False,
                    "error": "Audio data is empty after decoding"
                }
            
            logger.info(f"Received audio data: {len(audio_bytes)} bytes (declared format: {audio_format})")
            
            # Detect actual audio format from file headers
            detected_format = self._detect_audio_format(audio_bytes)
            logger.info(f"Detected audio format: {detected_format}")
            
            # Use detected format if the provided format is generic or unknown
            if audio_format in ('wav', 'unknown') and detected_format != 'unknown':
                audio_format = detected_format
                logger.info(f"Using detected format: {audio_format}")
            
            # Write to temporary file with correct extension
            with tempfile.NamedTemporaryFile(
                suffix=f".{audio_format}",
                delete=False
            ) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            logger.info(f"Audio written to temporary file: {temp_path} ({audio_format})")
            
            try:
                # For WebM, we need to use pydub to convert it
                if audio_format == 'webm':
                    logger.info("WebM format detected, attempting to convert...")
                    if PYDUB_AVAILABLE:
                        try:
                            audio_segment = AudioSegment.from_file(temp_path, format='webm')
                            # Convert to WAV for speech recognition
                            wav_path = temp_path.replace('.webm', '.wav')
                            audio_segment.export(wav_path, format='wav')
                            os.unlink(temp_path)  # Remove WebM file
                            temp_path = wav_path
                            logger.info(f"✅ Converted WebM to WAV: {wav_path}")
                        except Exception as e:
                            logger.warning(f"Could not convert WebM with pydub: {e}, trying direct reading...")
                    else:
                        logger.warning("pydub not available - cannot convert WebM format")
                
                # Load audio file
                with sr.AudioFile(temp_path) as source:
                    audio = self._recognizer.record(source)
                
                logger.info(f"Audio loaded successfully ({len(audio.frame_data)} bytes)")
                
                # Recognize speech
                lang = language or self.settings.SPEECH_RECOGNITION_LANGUAGE
                
                # Try Google Speech Recognition
                logger.info(f"Attempting recognition with language: {lang}")
                text = self._recognizer.recognize_google(audio, language=lang)
                
                logger.info(f"✅ Transcribed: {text[:50]}...")
                
                return {
                    "success": True,
                    "text": text,
                    "confidence": 0.9,  # Google doesn't provide confidence
                    "language": lang
                }
                
            finally:
                # Clean up temp files
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                # Check for converted WAV file
                for ext in ['.wav', '.webm']:
                    cleanup_path = temp_path.replace('.wav', ext).replace('.webm', ext)
                    if os.path.exists(cleanup_path) and cleanup_path != temp_path:
                        try:
                            os.unlink(cleanup_path)
                        except Exception:
                            pass
            
        except sr.UnknownValueError:
            logger.warning("Could not understand audio - speech not recognized")
            return {
                "success": False,
                "error": "Could not understand audio. Please speak clearly.",
                "text": ""
            }
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return {
                "success": False,
                "error": f"Speech recognition service error. Please try again."
            }
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Transcription failed: {str(e)}"
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
