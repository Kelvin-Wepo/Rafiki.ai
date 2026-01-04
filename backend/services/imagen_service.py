"""
Imagen Service - Google's Image Generation AI
Generates African presenter avatars using Imagen
"""

import os
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from PIL import Image
import io
import base64

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class ImagenService:
    """Service for generating avatars using Google's Imagen (via Gemini)"""
    
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self._initialized = False
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self._initialized = True
            logger.info("Imagen service initialized")
    
    def generate_african_avatar(
        self,
        name: str,
        skin_tone: str,
        hair_style: str,
        clothing: str,
        personality: str,
        background: str,
        language: str = "en-KE"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an African avatar using Imagen.
        
        Args:
            name: Presenter name
            skin_tone: Skin tone (light, medium, dark)
            hair_style: Hair style (natural, braids, twists, straight)
            clothing: Clothing style
            personality: Personality type
            background: Background setting
            language: Language/accent
        
        Returns:
            Dictionary with avatar image data or None if failed
        """
        if not self._initialized:
            logger.error("Imagen service not initialized - no API key")
            return None
        
        try:
            # Build detailed prompt for avatar generation
            prompt = self._build_avatar_prompt(
                name, skin_tone, hair_style, clothing, personality, background, language
            )
            
            logger.info(f"Generating avatar for {name} with prompt: {prompt[:100]}...")
            
            # Use Gemini's imagen capabilities via vision API
            model = genai.GenerativeModel('gemini-pro-vision')
            
            # For now, we'll use a text-based approach to describe the avatar
            # and store the prompt for later use with actual Imagen API
            
            avatar_data = {
                "id": f"avatar_{name.lower().replace(' ', '_')}",
                "name": name,
                "prompt": prompt,
                "skin_tone": skin_tone,
                "hair_style": hair_style,
                "clothing": clothing,
                "personality": personality,
                "background": background,
                "language": language,
                "status": "ready_for_generation"
            }
            
            logger.info(f"Avatar prompt created for {name}")
            return avatar_data
        
        except Exception as e:
            logger.error(f"Error generating avatar: {e}")
            return None
    
    def _build_avatar_prompt(
        self,
        name: str,
        skin_tone: str,
        hair_style: str,
        clothing: str,
        personality: str,
        background: str,
        language: str
    ) -> str:
        """Build detailed Imagen prompt for African avatar"""
        
        # Detailed descriptions for each attribute
        skin_tones = {
            "light": "light brown complexion",
            "medium": "medium brown complexion",
            "dark": "rich dark brown complexion"
        }
        
        hair_styles = {
            "natural": "natural textured afro hair",
            "braids": "beautiful braided hairstyle",
            "twists": "twisted protective hairstyle",
            "straight": "straight well-groomed hair"
        }
        
        clothing_styles = {
            "professional_suit": "professional business suit with tie",
            "traditional": "authentic African traditional attire",
            "casual": "casual professional business casual",
            "formal": "formal government official attire"
        }
        
        personalities = {
            "warm_friendly": "warm, welcoming, and friendly expression",
            "professional": "professional, confident, and authoritative demeanor",
            "patient": "patient, understanding, and calm presence",
            "encouraging": "encouraging, energetic, and inspirational attitude"
        }
        
        backgrounds = {
            "office": "modern professional office environment",
            "traditional": "cultural African background setting",
            "neutral": "clean neutral gray background",
            "government": "official government office backdrop"
        }
        
        # Build comprehensive prompt
        prompt = (
            f"Professional high-quality portrait of an African woman named {name}, "
            f"with {skin_tones.get(skin_tone, 'brown')} skin, "
            f"{hair_styles.get(hair_style, 'natural hair')}, "
            f"wearing {clothing_styles.get(clothing, 'professional attire')}, "
            f"with a {personalities.get(personality, 'professional')} expression, "
            f"in front of a {backgrounds.get(background, 'neutral background')}. "
            f"Studio lighting, professional photography, 4K quality, "
            f"portrait orientation, looking at camera. "
            f"African presenter style for {language} language content. "
            f"Professional, authentic, and inspiring appearance."
        )
        
        return prompt


# Global instance
imagen_service = ImagenService()
