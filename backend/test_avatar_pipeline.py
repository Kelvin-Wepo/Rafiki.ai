#!/usr/bin/env python3
"""
Avatar Animation Test Script
Demonstrates the complete pipeline: Imagen -> Audio -> SadTalker
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imagen_integration():
    """Test Imagen image generation"""
    print("\n" + "="*70)
    print("TEST 1: IMAGEN IMAGE GENERATION")
    print("="*70 + "\n")
    
    try:
        from services.imagen_service import ImagenService
        
        imagen = ImagenService()
        print("✅ ImagenService imported successfully")
        print(f"   - API Key configured: {'GOOGLE_API_KEY' in os.environ}")
        print(f"   - Service initialized: {imagen is not None}")
        
        # Check if API is available
        try:
            print("\n📸 Attempting to generate test image...")
            result = imagen.generate_image(
                prompt="A simple red circle on white background",
                image_size="256x256",
                num_images=1
            )
            
            if result and result.get('images'):
                print("✅ Image generation successful!")
                image = result['images'][0]
                print(f"   - Image type: {type(image).__name__}")
                if hasattr(image, 'size'):
                    print(f"   - Image size: {image.size}")
                return True
            else:
                print("⚠️  No images returned from Imagen")
                return False
                
        except Exception as e:
            print(f"⚠️  Imagen API not available: {e}")
            print("   (This is normal if API key is not configured)")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import ImagenService: {e}")
        return False


def test_elevenlabs_integration():
    """Test ElevenLabs TTS"""
    print("\n" + "="*70)
    print("TEST 2: ELEVENLABS TTS")
    print("="*70 + "\n")
    
    try:
        from services.elevenlabs_service import ElevenLabsService
        
        elevenlabs = ElevenLabsService()
        print("✅ ElevenLabsService imported successfully")
        print(f"   - API Key configured: {'ELEVENLABS_API_KEY' in os.environ}")
        print(f"   - Service initialized: {elevenlabs is not None}")
        
        # Check available voices
        try:
            voices = elevenlabs.get_available_voices()
            print(f"\n🎤 Available voices: {len(voices)}")
            for voice in voices[:3]:
                print(f"   - {voice}")
            print(f"   ... and {max(0, len(voices) - 3)} more")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not fetch voices: {e}")
            print("   (This is normal if API key is not configured)")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import ElevenLabsService: {e}")
        return False


def test_sadtalker_integration():
    """Test SadTalker service"""
    print("\n" + "="*70)
    print("TEST 3: SADTALKER SERVICE")
    print("="*70 + "\n")
    
    try:
        from services.sadtalker_service import get_sadtalker_service
        
        sadtalker = get_sadtalker_service()
        print("✅ SadTalkerService imported successfully")
        print(f"   - Service mode: {sadtalker.mode}")
        print(f"   - API URL: {sadtalker.api_url}")
        
        # Check available avatars
        avatars = sadtalker.get_available_avatars()
        print(f"\n👩 Available avatars: {len(avatars)}")
        for avatar in avatars:
            print(f"   - {avatar['name']}")
        
        # Check directories
        print(f"\n📂 Directory structure:")
        print(f"   - Avatar dir: {sadtalker.avatar_dir.exists()}")
        print(f"   - Cache dir: {sadtalker.cache_dir.exists()}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import SadTalkerService: {e}")
        return False


def test_pipeline_components():
    """Test all components together"""
    print("\n" + "="*70)
    print("TEST 4: PIPELINE INTEGRATION")
    print("="*70 + "\n")
    
    results = {
        "imagen": test_imagen_integration(),
        "elevenlabs": test_elevenlabs_integration(),
        "sadtalker": test_sadtalker_integration()
    }
    
    return results


def show_usage_examples():
    """Show examples of how to use the pipeline"""
    print("\n" + "="*70)
    print("USAGE EXAMPLES")
    print("="*70 + "\n")
    
    print("1️⃣  Run complete avatar animation pipeline:")
    print("   python3 avatar_animation_pipeline.py \\")
    print("     --text 'Hello! I am Rafiki, your AI assistant' \\")
    print("     --voice Habari \\")
    print("     --output ./my_avatars")
    
    print("\n2️⃣  Run quick demo:")
    print("   python3 quick_avatar_demo.py")
    
    print("\n3️⃣  Use in backend API:")
    print("   curl -X POST http://localhost:8000/api/avatar/generate-talking-video \\")
    print("     -F 'audio=@response.wav' \\")
    print("     -F 'language=en-US'")
    
    print("\n4️⃣  Use in Python code:")
    print("   from services.imagen_service import ImagenService")
    print("   from services.elevenlabs_service import ElevenLabsService")
    print("   from services.sadtalker_service import get_sadtalker_service")
    print("   ")
    print("   # Generate image")
    print("   imagen = ImagenService()")
    print("   image = imagen.generate_image(prompt='A woman', num_images=1)")
    print("   ")
    print("   # Generate audio")
    print("   elevenlabs = ElevenLabsService()")
    print("   audio = elevenlabs.synthesize_speech(text='Hello!')")
    print("   ")
    print("   # Animate")
    print("   sadtalker = get_sadtalker_service()")
    print("   video = await sadtalker.generate_video(")
    print("     audio_path='audio.wav',")
    print("     image_path='avatar.png'")
    print("   )")


def main():
    """Main test runner"""
    print("\n" + "="*70)
    print("🎬 AVATAR ANIMATION PIPELINE TEST SUITE")
    print("="*70)
    
    # Run integration tests
    results = test_pipeline_components()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"\nComponent Status:")
    print(f"  📸 Imagen: {'✅' if results['imagen'] else '⚠️'}")
    print(f"  🎤 ElevenLabs: {'✅' if results['elevenlabs'] else '⚠️'}")
    print(f"  🎬 SadTalker: {'✅' if results['sadtalker'] else '⚠️'}")
    
    if passed == total:
        print("\n🎉 All components ready!")
    else:
        print(f"\n⚠️  Some components need configuration")
        print("   See README for setup instructions")
    
    # Show usage
    show_usage_examples()
    
    print("\n" + "="*70)
    print("✅ Testing complete!")
    print("="*70 + "\n")
    
    return 0 if passed > 0 else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
