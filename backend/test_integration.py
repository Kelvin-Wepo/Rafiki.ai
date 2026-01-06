"""
Integration test script for backend services
Tests ElevenLabs TTS and SadTalker connectivity
"""

import asyncio
import httpx
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from services.elevenlabs_service import ElevenLabsService
from services.sadtalker_service import SadTalkerService
from config import get_settings


async def test_services():
    """Test all services"""
    settings = get_settings()
    
    print("=" * 60)
    print("Backend Integration Test")
    print("=" * 60)
    
    # Test 1: Check ElevenLabs API Key
    print("\n1. Testing ElevenLabs Configuration...")
    if settings.ELEVENLABS_API_KEY:
        print(f"   ✓ ElevenLabs API key is configured (starts with: {settings.ELEVENLABS_API_KEY[:8]}...)")
    else:
        print("   ✗ ElevenLabs API key NOT configured")
        print("     Set ELEVENLABS_API_KEY in your .env file")
    
    # Test 2: Check SadTalker API
    print("\n2. Testing SadTalker API...")
    sadtalker_url = os.getenv("SADTALKER_API_URL", "http://localhost:7860")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{sadtalker_url}/")
            if response.status_code == 200:
                print(f"   ✓ SadTalker API is running at {sadtalker_url}")
            else:
                print(f"   ? SadTalker API responded with status {response.status_code}")
    except httpx.ConnectError:
        print(f"   ✗ SadTalker API NOT available at {sadtalker_url}")
        print("     Start SadTalker with: python app.py --share")
    except Exception as e:
        print(f"   ✗ SadTalker API error: {e}")
    
    # Test 3: Check Avatar Files
    print("\n3. Checking Avatar Files...")
    sadtalker_service = SadTalkerService()
    avatars = sadtalker_service.get_available_avatars()
    if avatars:
        print(f"   ✓ Found {len(avatars)} avatar(s):")
        for avatar in avatars:
            print(f"     - {avatar['id']}: {avatar['name']}")
            if avatar.get('path'):
                exists = os.path.exists(avatar['path'])
                print(f"       File exists: {exists}")
    else:
        print("   ✗ No avatars found in assets/avatars/")
    
    # Test 4: Test ElevenLabs TTS (if API key is set)
    print("\n4. Testing ElevenLabs TTS...")
    if settings.ELEVENLABS_API_KEY:
        elevenlabs_service = ElevenLabsService()
        try:
            result = await elevenlabs_service.text_to_speech(
                text="Hello, this is a test.",
                voice_name="rachel"
            )
            if result and result.get('success') and result.get('audio_data'):
                print("   ✓ ElevenLabs TTS is working")
                # Test file generation
                audio_path = await elevenlabs_service.text_to_speech_file(
                    text="Hello, this is a test.",
                    voice_name="rachel"
                )
                if audio_path and os.path.exists(audio_path):
                    print(f"   ✓ Audio file generated: {audio_path}")
                    # Cleanup
                    os.unlink(audio_path)
                else:
                    print("   ✗ Failed to generate audio file")
            else:
                error = result.get('error', 'Unknown error') if result else 'No result'
                print(f"   ✗ ElevenLabs TTS failed: {error}")
        except Exception as e:
            print(f"   ✗ ElevenLabs TTS error: {e}")
    else:
        print("   - Skipped (no API key)")
    
    # Test 5: Test Fallback TTS (pyttsx3)
    print("\n5. Testing Fallback TTS (pyttsx3)...")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        print("   ✓ pyttsx3 is available")
    except ImportError:
        print("   ✗ pyttsx3 is NOT installed")
        print("     Install with: pip install pyttsx3")
    except Exception as e:
        print(f"   ✗ pyttsx3 error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    issues = []
    if not settings.ELEVENLABS_API_KEY:
        issues.append("Set ELEVENLABS_API_KEY in .env")
    
    # Check SadTalker
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(f"{sadtalker_url}/")
    except:
        issues.append("Start SadTalker API on port 7860")
    
    if issues:
        print("To fix backend issues:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("✓ All services are configured correctly!")
    
    return len(issues) == 0


if __name__ == "__main__":
    success = asyncio.run(test_services())
    sys.exit(0 if success else 1)
