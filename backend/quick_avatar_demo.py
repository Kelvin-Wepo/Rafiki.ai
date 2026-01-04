#!/usr/bin/env python3
"""
Quick Avatar Animation Demo
Fast way to test image generation + SadTalker animation
"""

import os
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from services.imagen_service import ImagenService
from services.sadtalker_service import get_sadtalker_service
from services.elevenlabs_service import ElevenLabsService
from utils.logger import logger


async def quick_demo():
    """Run a quick demo"""
    
    print("\n" + "="*70)
    print("🎬 QUICK AVATAR ANIMATION DEMO")
    print("="*70 + "\n")
    
    # Output directory
    output_dir = Path("./avatar_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Generate image with Imagen
    print("📸 Step 1: Generating avatar image...")
    try:
        imagen = ImagenService()
        
        prompt = """
        Beautiful portrait of a Kenyan woman, warm smile, professional attire,
        soft lighting, neutral background, 512x512 pixels, photorealistic
        """
        
        result = imagen.generate_image(
            prompt=prompt,
            image_size="512x512",
            num_images=1
        )
        
        if result and result.get('images'):
            image_data = result['images'][0]
            image_path = output_dir / "avatar_image.png"
            
            # Save image
            if isinstance(image_data, str):
                import base64
                image_bytes = base64.b64decode(image_data)
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)
            else:
                image_data.save(image_path, 'PNG')
            
            print(f"✅ Image saved: {image_path}\n")
        else:
            print("⚠️  Could not generate image with Imagen\n")
            image_path = None
            
    except Exception as e:
        print(f"⚠️  Imagen error: {e}\n")
        image_path = None
    
    # Step 2: Generate audio with ElevenLabs
    print("🎤 Step 2: Generating audio...")
    try:
        elevenlabs = ElevenLabsService()
        audio_path = output_dir / "avatar_audio.wav"
        
        result = elevenlabs.synthesize_speech(
            text="Hello! I am Rafiki, your AI assistant from Kenya.",
            voice_name="Habari",
            output_path=str(audio_path)
        )
        
        if os.path.exists(audio_path):
            print(f"✅ Audio saved: {audio_path}\n")
        else:
            print("⚠️  Could not generate audio with ElevenLabs\n")
            audio_path = None
            
    except Exception as e:
        print(f"⚠️  ElevenLabs error: {e}\n")
        audio_path = None
    
    # Step 3: Animate with SadTalker
    if image_path and audio_path:
        print("🎬 Step 3: Animating with SadTalker...")
        try:
            sadtalker = get_sadtalker_service()
            
            video_path, error = await sadtalker.generate_video(
                audio_path=str(audio_path),
                avatar_id="custom",
                image_path=str(image_path),
                preprocess="full",
                still_mode=False,
                expression_scale=1.0
            )
            
            if video_path and os.path.exists(video_path):
                print(f"✅ Video saved: {video_path}\n")
                print("="*70)
                print("🎉 SUCCESS! Talking avatar video generated!")
                print("="*70)
                print(f"\nGenerated files:")
                print(f"  📸 Image: {image_path}")
                print(f"  🔊 Audio: {audio_path}")
                print(f"  🎬 Video: {video_path}\n")
            else:
                print(f"❌ Video generation failed: {error}\n")
                
        except Exception as e:
            print(f"❌ SadTalker error: {e}\n")
    else:
        print("⚠️  Skipping animation - image or audio missing\n")
    
    print("✅ Demo complete!")


if __name__ == "__main__":
    try:
        asyncio.run(quick_demo())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
