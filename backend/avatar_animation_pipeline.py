#!/usr/bin/env python3
"""
Complete Avatar Animation Pipeline
Generates an image with Imagen 3, then animates it with SadTalker lip-sync
"""

import os
import sys
import asyncio
import tempfile
import base64
from pathlib import Path
import argparse
import logging

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.imagen_service import ImagenService
from services.sadtalker_service import get_sadtalker_service
from services.elevenlabs_service import ElevenLabsService
from utils.logger import logger

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class AvatarAnimationPipeline:
    """Complete pipeline for generating and animating avatars"""
    
    def __init__(self, output_dir="./avatar_output"):
        """Initialize the pipeline"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.imagen = ImagenService()
        self.sadtalker = get_sadtalker_service()
        self.elevenlabs = ElevenLabsService()
        
        logger.info(f"Pipeline initialized. Output dir: {self.output_dir}")
    
    def generate_image_with_imagen(self, prompt, num_variations=1):
        """
        Generate avatar image using Imagen 3
        
        Args:
            prompt: Text prompt for image generation
            num_variations: Number of variations to generate
            
        Returns:
            List of image paths
        """
        logger.info("🎨 Generating avatar image with Imagen...")
        print("\n" + "="*70)
        print("STEP 1: GENERATE AVATAR IMAGE WITH IMAGEN 3")
        print("="*70)
        
        try:
            result = self.imagen.generate_image(
                prompt=prompt,
                image_size="512x512",
                num_images=num_variations,
                quality_filter=True
            )
            
            if not result or not result.get('images'):
                logger.error("Failed to generate images")
                print("❌ Failed to generate images")
                return []
            
            image_paths = []
            for idx, image_data in enumerate(result['images']):
                image_path = self.output_dir / f"avatar_variation_{idx+1}.png"
                
                # Save image
                if isinstance(image_data, str):
                    # Base64 encoded
                    image_bytes = base64.b64decode(image_data)
                    with open(image_path, 'wb') as f:
                        f.write(image_bytes)
                else:
                    # PIL Image
                    image_data.save(image_path, 'PNG', quality=95)
                
                image_paths.append(image_path)
                logger.info(f"✓ Saved image: {image_path}")
                print(f"✅ Variation {idx+1} saved: {image_path}")
            
            return image_paths
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            print(f"❌ Error: {e}")
            return []
    
    def generate_audio_with_elevenlabs(self, text, language="en-US", voice="Habari"):
        """
        Generate audio using ElevenLabs TTS
        
        Args:
            text: Text to convert to speech
            language: Language code
            voice: Voice name
            
        Returns:
            Path to audio file
        """
        logger.info("🎤 Generating audio with ElevenLabs...")
        print("\n" + "="*70)
        print("STEP 2: GENERATE AUDIO WITH ELEVENLABS TTS")
        print("="*70)
        
        try:
            audio_path = self.output_dir / "response_audio.wav"
            
            result = self.elevenlabs.synthesize_speech(
                text=text,
                voice_name=voice,
                language_code=language,
                output_path=str(audio_path)
            )
            
            if result and os.path.exists(audio_path):
                logger.info(f"✓ Audio saved: {audio_path}")
                print(f"✅ Audio generated: {audio_path}")
                return audio_path
            else:
                logger.warning("Audio generation returned no file")
                print("⚠️  Audio generation failed, creating sample audio...")
                return self._create_sample_audio()
                
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            print(f"❌ Error: {e}")
            print("⚠️  Creating sample audio instead...")
            return self._create_sample_audio()
    
    def _create_sample_audio(self):
        """Create a sample audio file for testing"""
        try:
            import wave
            import struct
            import math
            
            audio_path = self.output_dir / "sample_audio.wav"
            duration = 3  # 3 seconds
            sample_rate = 44100
            frequency = 440  # A4 note
            
            # Generate sine wave
            frames = []
            for i in range(int(sample_rate * duration)):
                value = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
                frames.append(struct.pack('<h', value))
            
            # Write WAV file
            with wave.open(str(audio_path), 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(b''.join(frames))
            
            logger.info(f"Sample audio created: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Sample audio creation failed: {e}")
            return None
    
    async def animate_with_sadtalker(self, image_path, audio_path):
        """
        Animate image with SadTalker using audio
        
        Args:
            image_path: Path to avatar image
            audio_path: Path to audio file
            
        Returns:
            Path to output video
        """
        logger.info("🎬 Animating with SadTalker...")
        print("\n" + "="*70)
        print("STEP 3: ANIMATE WITH SADTALKER LIP-SYNC")
        print("="*70)
        
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image not found: {image_path}")
                print(f"❌ Image not found: {image_path}")
                return None
            
            if not os.path.exists(audio_path):
                logger.error(f"Audio not found: {audio_path}")
                print(f"❌ Audio not found: {audio_path}")
                return None
            
            logger.info(f"Image: {image_path}")
            logger.info(f"Audio: {audio_path}")
            print(f"📸 Image: {image_path}")
            print(f"🔊 Audio: {audio_path}")
            print("⏳ Processing... (this may take a while)")
            
            video_path, error = await self.sadtalker.generate_video(
                audio_path=str(audio_path),
                avatar_id="custom",
                image_path=str(image_path),
                preprocess="full",
                still_mode=False,
                expression_scale=1.0
            )
            
            if video_path and os.path.exists(video_path):
                logger.info(f"✓ Video generated: {video_path}")
                print(f"✅ Video generated: {video_path}")
                return video_path
            else:
                logger.error(f"Video generation failed: {error}")
                print(f"❌ Video generation failed: {error}")
                return None
                
        except Exception as e:
            logger.error(f"SadTalker animation error: {e}")
            print(f"❌ Error: {e}")
            return None
    
    async def run_complete_pipeline(self, text, image_prompt=None, voice="Habari"):
        """
        Run the complete pipeline:
        1. Generate image with Imagen
        2. Generate audio with ElevenLabs
        3. Animate with SadTalker
        
        Args:
            text: Text to speak
            image_prompt: Prompt for image generation (uses default if None)
            voice: Voice for TTS
            
        Returns:
            Dict with paths to image and video
        """
        print("\n" + "="*70)
        print("🎬 RAFIKI AVATAR ANIMATION PIPELINE")
        print("="*70)
        
        # Default image prompt
        if not image_prompt:
            image_prompt = """
            Professional portrait photo of a warm, friendly Kenyan woman in her early 30s.
            She has an approachable, genuine smile and intelligent eyes that convey trustworthiness.
            She's wearing professional smart casual attire - a light blue blouse.
            Natural hairstyle, beautiful dark skin tone.
            Head and shoulders framing, centered composition, facing camera directly.
            Neutral beige background. Soft, even professional lighting.
            High quality photorealistic portrait suitable for a professional AI assistant.
            Resolution optimized for web: 512x512 pixels.
            """
        
        # Step 1: Generate image
        logger.info("Starting pipeline execution...")
        image_paths = self.generate_image_with_imagen(image_prompt, num_variations=1)
        
        if not image_paths:
            print("\n❌ Failed to generate image. Aborting pipeline.")
            return None
        
        image_path = image_paths[0]
        
        # Step 2: Generate audio
        audio_path = self.generate_audio_with_elevenlabs(text, voice=voice)
        
        if not audio_path:
            print("\n❌ Failed to generate audio. Aborting pipeline.")
            return None
        
        # Step 3: Animate with SadTalker
        video_path = await self.animate_with_sadtalker(image_path, audio_path)
        
        # Summary
        print("\n" + "="*70)
        print("✅ PIPELINE COMPLETE")
        print("="*70)
        
        result = {
            "success": video_path is not None,
            "image_path": str(image_path),
            "audio_path": str(audio_path),
            "video_path": str(video_path) if video_path else None
        }
        
        if video_path:
            print(f"\n🎉 Success! Generated talking avatar video:")
            print(f"  📸 Avatar image: {image_path}")
            print(f"  🔊 Audio: {audio_path}")
            print(f"  🎬 Video: {video_path}")
        else:
            print(f"\n⚠️  Partial success:")
            print(f"  📸 Avatar image: {image_path}")
            print(f"  🔊 Audio: {audio_path}")
            print(f"  🎬 Video: Failed to generate")
        
        return result


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate and animate avatar with Imagen + SadTalker"
    )
    
    parser.add_argument(
        "--text",
        default="Hello! I am Rafiki, your AI assistant. How can I help you today?",
        help="Text to speak (default: greeting)"
    )
    
    parser.add_argument(
        "--prompt",
        default=None,
        help="Image generation prompt (uses default if not provided)"
    )
    
    parser.add_argument(
        "--voice",
        default="Habari",
        help="Voice name for TTS (default: Habari)"
    )
    
    parser.add_argument(
        "--output",
        default="./avatar_output",
        help="Output directory (default: ./avatar_output)"
    )
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = AvatarAnimationPipeline(output_dir=args.output)
    
    # Run pipeline
    result = await pipeline.run_complete_pipeline(
        text=args.text,
        image_prompt=args.prompt,
        voice=args.voice
    )
    
    if result:
        print(f"\n📊 Results saved to: {args.output}")
        return 0
    else:
        print("\n❌ Pipeline failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
