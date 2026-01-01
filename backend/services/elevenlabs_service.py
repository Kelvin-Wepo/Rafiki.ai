"""
ElevenLabs Conversational AI Service
Handles signed URL generation and text-to-speech via ElevenLabs API
Optimized for warm Kenyan accent voices with natural pacing and emphasis
"""

import httpx
import base64
import re
from typing import Optional, Dict, Any, List
from config import get_settings
from utils.logger import get_logger

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
        # Primary warm female voices
        "noah": {
            "voice_id": "n2svSAHTQ6OWjZIVJ4WL",  # Warm, friendly male voice
            "name": "Noah",
            "description": "Warm, friendly Kenyan male voice - great for welcoming and patient guidance",
            "language": "en-KE",
            "accent": "Kenyan",
            "tone": "warm, patient, conversational"
        },
        "aria": {
            "voice_id": "XB0fDUnXU5powFXDhCwa",  # Warm female voice
            "name": "Aria",
            "description": "Warm, professional female voice with natural Kenyan accent",
            "language": "en-KE",
            "accent": "Kenyan",
            "tone": "warm, professional, accessible"
        },
        "sage": {
            "voice_id": "5ND885W2NyJmB6mcKrFt",  # Mature, warm voice
            "name": "Sage",
            "description": "Mature, warm voice perfect for patient guidance and support",
            "language": "en-KE",
            "accent": "Kenyan",
            "tone": "warm, patient, supportive"
        },
        "rachel": {
            "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Default warm voice
            "name": "Rachel",
            "description": "Clear, warm voice suitable for government service guidance",
            "language": "en",
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
    
    # Speech optimization for different content types
    SPEECH_OPTIMIZATION = {
        "government_guidance": {
            "speech_rate": 0.95,  # Slightly slower for clarity
            "pause_duration_ms": 400,  # Natural pauses between sentences
            "emphasis_words": ["KRA", "PIN", "iTax", "nil returns", "step"]
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
        }
    }
    
    def __init__(self):
        """Initialize ElevenLabs service with Kenyan voice support."""
        self.settings = get_settings()
        self.api_key = self.settings.ELEVENLABS_API_KEY
        self.agent_id = self.settings.ELEVENLABS_AGENT_ID
        self._client = None
        
        # Set default voice - preferring Noah (warm Kenyan male voice)
        self.default_voice_id = self.KENYAN_VOICES.get("noah", {}).get("voice_id") or self.settings.ELEVENLABS_VOICE_ID
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
    
    def optimize_text_for_speech(self, text: str, content_type: str = "conversational") -> str:
        """
        Optimize text for natural speech delivery with proper pauses and emphasis.
        
        Args:
            text: Text to optimize
            content_type: Type of content (government_guidance, conversational, accessibility)
            
        Returns:
            Optimized text with speech markers
        """
        # Ensure content_type is valid
        if content_type not in self.SPEECH_OPTIMIZATION:
            content_type = "conversational"
        
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
        optimize_speech: bool = True
    ) -> Dict[str, Any]:
        """
        Convert text to speech using ElevenLabs TTS API with Kenyan voice.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID (optional)
            voice_name: Kenyan voice name (noah, aria, sage, rachel)
            model_id: TTS model to use
            output_format: Audio output format
            content_type: Type of content for speech optimization
            optimize_speech: Whether to optimize text for natural speech
            
        Returns:
            Dict with audio data (base64) or error
        """
        try:
            # Select voice: prefer voice_name for Kenyan voices
            if voice_name and voice_name.lower() in self.KENYAN_VOICES:
                result = self.select_kenyan_voice(voice_name)
                if not result.get("success"):
                    logger.warning(f"Could not select voice {voice_name}, using default")
                target_voice = self.default_voice_id
            else:
                target_voice = voice_id or self.default_voice_id
            
            # Optimize text for natural speech
            optimized_text = text
            if optimize_speech:
                optimized_text = self.optimize_text_for_speech(text, content_type)
            
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
                    f"Text: {len(text)} chars, Content type: {content_type}"
                )
                return {
                    "success": True,
                    "audio_data": audio_data,
                    "content_type": f"audio/{output_format.split('_')[0]}",
                    "text_length": len(text),
                    "voice_name": self.current_voice_name,
                    "voice_id": target_voice,
                    "speech_type": content_type
                }
            else:
                error_msg = f"TTS failed: {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
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
