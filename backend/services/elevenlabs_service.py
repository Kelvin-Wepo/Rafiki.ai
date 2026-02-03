"""
ElevenLabs Conversational AI Service
Handles signed URL generation and text-to-speech via ElevenLabs API
Optimized for warm Kenyan accent voices with natural pacing and emphasis
"""

import httpx
import base64
import re
from typing import Optional, Dict, Any, List
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ElevenLabsService:
    """
    Service for ElevenLabs Conversational AI integration.
    Provides signed URL generation for secure WebSocket connections
    and text-to-speech functionality with Kenyan-accent voices.
    """
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    # Warm Kenyan voices available in ElevenLabs
    KENYAN_VOICES = {
        # Primary warm male voice from user's account
        "noah": {
            "voice_id": "iEwEUVNDPmshU0IJrWmj",  # Noah - Conversational and Friendly (from user's ElevenLabs account)
            "name": "Noah",
            "description": "Warm, friendly conversational voice - great for welcoming and patient guidance",
            "language": "en",
            "languages": ["en", "sw"],  # Supports both English and Kiswahili
            "accent": "Natural",
            "tone": "warm, patient, conversational, chill"
        },
        "aria": {
            "voice_id": "XB0fDUnXU5powFXDhCwa",  # Warm female voice
            "name": "Aria",
            "description": "Warm, professional female voice with natural Kenyan accent",
            "language": "en-KE",
            "languages": ["en", "sw"],
            "accent": "Kenyan",
            "tone": "warm, professional, accessible"
        },
        "sage": {
            "voice_id": "5ND885W2NyJmB6mcKrFt",  # Mature, warm voice
            "name": "Sage",
            "description": "Mature, warm voice perfect for patient guidance and support",
            "language": "en-KE",
            "languages": ["en", "sw"],
            "accent": "Kenyan",
            "tone": "warm, patient, supportive"
        },
        "rachel": {
            "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Default warm voice
            "name": "Rachel",
            "description": "Clear, warm voice suitable for government service guidance",
            "language": "en",
            "languages": ["en", "sw"],  # Multilingual support
            "accent": "Neutral",
            "tone": "warm, clear, helpful"
        }
    }
    
    # Voice settings optimized for clarity and natural speech
    VOICE_SETTINGS_OPTIMIZED = {
        "stability": 0.6,  # Balanced stability for natural variation
        "similarity_boost": 0.8,  # High similarity for consistent voice personality
        "style": 0.5,  # Moderate style for expressiveness
        "use_speaker_boost": True  # Enhance voice clarity
    }
    
    # Speech optimization for different content types and languages
    SPEECH_OPTIMIZATION = {
        "government_guidance": {
            "speech_rate": 0.95,  # Slightly slower for clarity
            "pause_duration_ms": 400,  # Natural pauses between sentences
            "emphasis_words": ["KRA", "PIN", "iTax", "nil returns", "step", "important"]
        },
        "conversational": {
            "speech_rate": 1.0,  # Normal speech rate
            "pause_duration_ms": 300,  # Natural conversational pauses
            "emphasis_words": ["Rafiki", "help", "excellent", "confirmed"]
        },
        "accessibility": {
            "speech_rate": 0.85,  # Slower for accessibility
            "pause_duration_ms": 500,  # Longer pauses for comprehension
            "emphasis_words": ["important", "next", "confirm", "click"]
        },
        # Kiswahili-specific optimization
        "kiswahili_guidance": {
            "speech_rate": 0.92,  # Slightly slower for Kiswahili clarity
            "pause_duration_ms": 420,  # Natural Kiswahili pauses
            "emphasis_words": ["KRA", "PIN", "iTax", "hatua", "muhimu", "tafadhali"]
        },
        "kiswahili_conversational": {
            "speech_rate": 0.98,  # Near-normal for conversational Kiswahili
            "pause_duration_ms": 320,  # Natural pauses
            "emphasis_words": ["Rafiki", "asante", "karibu", "sawa", "ndiyo"]
        }
    }
    
    def __init__(self):
        """Initialize ElevenLabs service with Kenyan voice support."""
        self.settings = get_settings()
        self.api_key = self.settings.ELEVENLABS_API_KEY
        self.agent_id = self.settings.ELEVENLABS_AGENT_ID
        self.branch_id = getattr(self.settings, 'ELEVENLABS_BRANCH_ID', None)
        self._client = None
        
        # Set default voice - using Noah (Kenyan male voice for both EN and SW)
        self.default_voice_id = self.KENYAN_VOICES["noah"]["voice_id"]
        self.current_voice_name = "Noah"
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def get_kenyan_voices(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available Kenyan-optimized voices.
        
        Returns:
            Dict mapping voice names to voice configurations
        """
        return self.KENYAN_VOICES
    
    def select_kenyan_voice(self, voice_name: str = "noah") -> Dict[str, Any]:
        """
        Select a Kenyan voice by name.
        
        Args:
            voice_name: Voice name (noah, aria, sage, rachel)
            
        Returns:
            Dict with voice configuration or error
        """
        if voice_name.lower() not in self.KENYAN_VOICES:
            available = ", ".join(self.KENYAN_VOICES.keys())
            return {
                "success": False,
                "error": f"Voice not found. Available: {available}"
            }
        
        voice = self.KENYAN_VOICES[voice_name.lower()]
        self.default_voice_id = voice["voice_id"]
        self.current_voice_name = voice["name"]
        logger.info(f"Selected Kenyan voice: {voice['name']}")
        
        return {
            "success": True,
            "voice": voice
        }
    
    def optimize_text_for_speech(self, text: str, content_type: str = "conversational", language: str = "en") -> str:
        """
        Optimize text for natural speech delivery with proper pauses and emphasis.
        Supports both English and Kiswahili with appropriate speech patterns.
        
        Args:
            text: Text to optimize
            content_type: Type of content (government_guidance, conversational, accessibility)
            language: Language code ('en' for English, 'sw' for Kiswahili)
            
        Returns:
            Optimized text with speech markers
        """
        # Adjust content_type for Kiswahili
        if language == 'sw':
            if content_type == "government_guidance":
                content_type = "kiswahili_guidance"
            elif content_type == "conversational":
                content_type = "kiswahili_conversational"
        
        # Ensure content_type is valid
        if content_type not in self.SPEECH_OPTIMIZATION:
            content_type = "kiswahili_conversational" if language == 'sw' else "conversational"
        
        config = self.SPEECH_OPTIMIZATION[content_type]
        emphasis_words = config.get("emphasis_words", [])
        
        optimized = text
        
        # Add emphasis to important words/phrases using ElevenLabs markers
        for word in emphasis_words:
            # Case-insensitive replacement with emphasis markers
            pattern = re.compile(f"\\b{word}\\b", re.IGNORECASE)
            optimized = pattern.sub(f"**{word}**", optimized)
        
        # Add natural pauses at sentence boundaries for clarity
        optimized = optimized.replace(".", ".\n")
        optimized = optimized.replace("?", "?\n")
        optimized = optimized.replace("!", "!\n")
        
        return optimized.strip()
    
    async def get_signed_url(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a signed URL for WebSocket connection to ElevenLabs agent.
        This allows secure connections without exposing API key in frontend.
        
        Args:
            agent_id: Optional agent ID override (defaults to configured agent)
            
        Returns:
            Dict with signed_url and expiration info
        """
        try:
            target_agent = agent_id or self.agent_id
            
            if not target_agent:
                return {
                    "success": False,
                    "error": "No agent ID configured"
                }
            
            if not self.api_key:
                return {
                    "success": False,
                    "error": "ElevenLabs API key not configured"
                }
            
            # Request signed URL from ElevenLabs
            response = await self.client.get(
                f"/convai/conversation/get_signed_url",
                params={"agent_id": target_agent}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Generated signed URL for agent {target_agent} with voice {self.current_voice_name}")
                return {
                    "success": True,
                    "signed_url": data.get("signed_url"),
                    "agent_id": target_agent,
                    "voice": self.current_voice_name,
                    "voice_id": self.default_voice_id
                }
            else:
                error_msg = f"Failed to get signed URL: {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error(f"Error getting signed URL: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        voice_name: Optional[str] = None,
        model_id: str = "eleven_multilingual_v2",
        output_format: str = "mp3_44100_128",
        content_type: str = "conversational",
        optimize_speech: bool = True,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Convert text to speech using ElevenLabs TTS API with Kenyan voice.
        Supports both English and Kiswahili with natural pronunciation.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID (optional)
            voice_name: Kenyan voice name (noah, aria, sage, rachel)
            model_id: TTS model to use (eleven_multilingual_v2 supports Kiswahili)
            output_format: Audio output format
            content_type: Type of content for speech optimization
            optimize_speech: Whether to optimize text for natural speech
            language: Language code ('en' for English, 'sw' for Kiswahili)
            
        Returns:
            Dict with audio data (base64) or error
        """
        try:
            # Select voice: prefer voice_name for Kenyan voices
            target_voice = None
            
            if voice_name and voice_name.lower() in self.KENYAN_VOICES:
                # Get voice from KENYAN_VOICES dict
                voice_config = self.KENYAN_VOICES[voice_name.lower()]
                target_voice = voice_config["voice_id"]
                voice_display_name = voice_config["name"]
                logger.info(f"Selected Kenyan voice: {voice_display_name} for language: {language}")
            elif voice_id:
                # Use provided voice_id directly
                target_voice = voice_id
            else:
                # Use default voice from settings (Rachel)
                target_voice = self.default_voice_id
                logger.info(f"Using default voice: {self.current_voice_name} for language: {language}")
            
            # Optimize text for natural speech with language support
            optimized_text = text
            if optimize_speech:
                optimized_text = self.optimize_text_for_speech(text, content_type, language)
            
            # Prepare voice settings optimized for Kenyan accent clarity
            voice_settings = self.VOICE_SETTINGS_OPTIMIZED.copy()
            
            response = await self.client.post(
                f"/text-to-speech/{target_voice}",
                json={
                    "text": optimized_text,
                    "model_id": model_id,
                    "voice_settings": voice_settings
                },
                params={"output_format": output_format}
            )
            
            if response.status_code == 200:
                audio_data = base64.b64encode(response.content).decode("utf-8")
                logger.info(
                    f"Generated TTS audio using {self.current_voice_name} voice. "
                    f"Text: {len(text)} chars, Language: {language}, Content type: {content_type}"
                )
                return {
                    "success": True,
                    "audio_data": audio_data,
                    "content_type": f"audio/{output_format.split('_')[0]}",
                    "text_length": len(text),
                    "voice_name": self.current_voice_name,
                    "voice_id": target_voice,
                    "speech_type": content_type,
                    "language": language
                }
            else:
                error_msg = f"TTS failed: {response.status_code}"
                try:
                    error_detail = response.json()
                    logger.error(f"{error_msg} - Detail: {error_detail}")

                    # Detect subscription/payment issues and make a clear log
                    detail_status = None
                    if isinstance(error_detail, dict):
                        detail_status = error_detail.get("detail", {}).get("status") or error_detail.get("status")

                    if response.status_code == 402 or detail_status == "payment_required":
                        logger.warning("ElevenLabs returned 402 Payment Required for the requested voice. This usually means your subscription does not allow library voices via the API. Consider selecting a different voice or upgrading your subscription.")

                except Exception:
                    logger.error(f"{error_msg} - Voice ID: {target_voice}")

                # Try Google Cloud TTS fallback
                logger.warning(f"ElevenLabs failed with {response.status_code}. Trying Google Cloud TTS fallback...")
                return await self._google_tts_text_fallback(text, language)
                
        except Exception as e:
            logger.error(f"TTS error: {e}")
            # Try Google Cloud TTS fallback on exception
            try:
                return await self._google_tts_text_fallback(text, language)
            except Exception as fallback_error:
                logger.error(f"Google Cloud TTS fallback also failed: {fallback_error}")
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def text_to_speech_file(
        self,
        text: str,
        language: str = "en",
        voice_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Convert text to speech and save to a temporary file.
        Used by SadTalker service for avatar animation.
        Falls back to pyttsx3 if ElevenLabs is unavailable.
        
        Args:
            text: Text to convert to speech
            language: Language code ('en' or 'sw')
            voice_name: Optional voice name (defaults to 'noah' for Kenyan accent)
            
        Returns:
            Path to the generated audio file, or None on error
        """
        try:
            import tempfile
            
            # Auto-select Noah (Kenyan accent) if no voice specified
            if not voice_name:
                voice_name = "noah"  # Default to Kenyan accent voice
            
            # Try ElevenLabs first
            result = await self.text_to_speech(
                text=text,
                voice_name=voice_name,
                language=language,
                output_format="mp3_44100_128"
            )
            
            if result.get("success"):
                # Decode audio and save to file
                audio_data = base64.b64decode(result["audio_data"])
                
                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=".mp3",
                    delete=False
                )
                temp_file.write(audio_data)
                temp_file.close()
                
                logger.info(f"Generated TTS audio file (ElevenLabs): {temp_file.name}")
                return temp_file.name
            
            # ElevenLabs failed - try Google Cloud TTS fallback
            logger.warning(f"ElevenLabs TTS failed: {result.get('error')}. Trying Google Cloud TTS fallback...")
            return await self._google_tts_fallback(text)
            
        except Exception as e:
            logger.error(f"TTS file generation error: {e}")
            # Try Google Cloud TTS fallback on any exception
            try:
                return await self._google_tts_fallback(text)
            except Exception as fallback_error:
                logger.error(f"Google Cloud TTS fallback also failed: {fallback_error}")
                # Final fallback to espeak
                try:
                    return await self._pyttsx3_fallback(text)
                except Exception as final_error:
                    logger.error(f"espeak fallback also failed: {final_error}")
                    return None
    
    async def _google_tts_fallback(self, text: str) -> Optional[str]:
        """
        Generate TTS audio using Google Cloud TTS as fallback.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Path to the generated MP3 file, or None on error
        """
        try:
            from backend.services.google_tts_service import google_tts_service
            
            # Initialize if needed
            if not google_tts_service._initialized:
                google_tts_service.initialize()
            
            # Generate audio file
            audio_file = await google_tts_service.text_to_speech_file(
                text=text,
                voice_name="en-US-Neural2-J",  # Warm male voice
                language="en"
            )
            
            if audio_file:
                logger.info(f"Generated TTS audio file (Google Cloud fallback): {audio_file}")
                return audio_file
            
            # If Google TTS fails, fall back to espeak
            logger.warning("Google Cloud TTS fallback failed, trying espeak...")
            return await self._pyttsx3_fallback(text)
            
        except Exception as e:
            logger.error(f"Google Cloud TTS fallback error: {e}")
            # Final fallback to espeak
            return await self._pyttsx3_fallback(text)
    
    async def _google_tts_text_fallback(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Generate TTS audio using Google Cloud TTS as fallback for text_to_speech method.
        
        Args:
            text: Text to convert to speech
            language: Language code
            
        Returns:
            Dict with audio data (base64) or error
        """
        try:
            from backend.services.google_tts_service import google_tts_service
            
            # Initialize if needed
            if not google_tts_service._initialized:
                initialized = google_tts_service.initialize()
                if not initialized:
                    logger.warning("Google Cloud TTS not initialized (missing credentials). Please set GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_API_KEY.")
                    return {"success": False, "error": "google_tts_not_initialized", "message": "Google Cloud credentials not configured"}
            
            # Generate audio bytes
            audio_bytes = await google_tts_service.text_to_speech(
                text=text,
                voice_name="en-US-Neural2-J",  # Warm male voice
                language=language
            )

            if audio_bytes:
                audio_data = base64.b64encode(audio_bytes).decode('utf-8')
                logger.info(f"Generated TTS audio using Google Cloud TTS fallback. Text: {len(text)} chars")
                return {
                    "success": True,
                    "audio_data": audio_data,
                    "content_type": "audio/mp3",
                    "text_length": len(text),
                    "voice_name": "Google Cloud Neural2-J",
                    "voice_id": "en-US-Neural2-J",
                    "speech_type": "conversational",
                    "language": language
                }
            else:
                logger.error("Google Cloud TTS returned no audio bytes")
                return {"success": False, "error": "no_audio", "message": "Google Cloud TTS returned no audio"}
            
        except Exception as e:
            logger.error(f"Google Cloud TTS text fallback error: {e}")
            return {
                "success": False,
                "error": f"All TTS methods failed. Last error: {str(e)}"
            }
    
    async def _pyttsx3_fallback(self, text: str) -> Optional[str]:
        """
        Generate TTS audio using espeak as a fallback.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Path to the generated WAV file, or None on error
        """
        try:
            import tempfile
            import subprocess
            import shutil
            
            # Create temp file for output
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            )
            temp_file.close()
            
            # Check if espeak is available
            espeak_path = shutil.which('espeak') or shutil.which('espeak-ng')
            if not espeak_path:
                logger.error("espeak not installed. Install with: sudo apt install espeak")
                return None
            
            # Generate audio using espeak
            result = subprocess.run(
                [espeak_path, '-w', temp_file.name, '-s', '150', text],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"espeak failed: {result.stderr}")
                return None
            
            # Verify file was created
            import os
            if os.path.getsize(temp_file.name) < 100:
                logger.error("espeak generated empty or too small audio file")
                return None
            
            logger.info(f"Generated TTS audio file (espeak fallback): {temp_file.name}")
            return temp_file.name
            
        except subprocess.TimeoutExpired:
            logger.error("espeak timed out")
            return None
        except Exception as e:
            logger.error(f"espeak fallback error: {e}")
            return None
    
    async def get_voices(self) -> Dict[str, Any]:
        """
        Get available ElevenLabs voices with Kenyan voice preferences.
        
        Returns:
            Dict with list of available voices, Kenyan voices highlighted
        """
        try:
            response = await self.client.get("/voices")
            
            if response.status_code == 200:
                data = response.json()
                all_voices = [
                    {
                        "voice_id": v["voice_id"],
                        "name": v["name"],
                        "labels": v.get("labels", {}),
                        "preview_url": v.get("preview_url"),
                        "is_kenyan_optimized": False  # Default for API voices
                    }
                    for v in data.get("voices", [])
                ]
                
                # Add Kenyan-optimized voices to the list
                kenyan_voices = [
                    {
                        **voice,
                        "is_kenyan_optimized": True,
                        "preview_url": None  # Not available yet
                    }
                    for voice in self.KENYAN_VOICES.values()
                ]
                
                combined_voices = kenyan_voices + all_voices
                
                return {
                    "success": True,
                    "voices": combined_voices,
                    "kenyan_voices": list(self.KENYAN_VOICES.keys()),
                    "default_voice": self.current_voice_name
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get voices: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            # Return at least the Kenyan voices even if API call fails
            return {
                "success": True,
                "voices": [
                    {**voice, "is_kenyan_optimized": True, "preview_url": None}
                    for voice in self.KENYAN_VOICES.values()
                ],
                "kenyan_voices": list(self.KENYAN_VOICES.keys()),
                "default_voice": self.current_voice_name,
                "note": "Showing Kenyan-optimized voices only (API unavailable)"
            }
    
    async def get_agent_info(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about an ElevenLabs conversational agent.
        
        Args:
            agent_id: Agent ID to query (defaults to configured agent)
            
        Returns:
            Dict with agent information including voice configuration
        """
        try:
            target_agent = agent_id or self.agent_id
            
            response = await self.client.get(f"/convai/agents/{target_agent}")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "agent": {
                        "agent_id": data.get("agent_id"),
                        "name": data.get("name"),
                        "conversation_config": data.get("conversation_config", {}),
                        "voice": {
                            "current": self.current_voice_name,
                            "voice_id": self.default_voice_id,
                            "available_kenyan_voices": list(self.KENYAN_VOICES.keys())
                        }
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get agent info: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error getting agent info: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
elevenlabs_service = ElevenLabsService()
