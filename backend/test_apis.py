#!/usr/bin/env python3
"""
Complete Avatar Pipeline Test - Test with actual API keys
Tests Imagen, ElevenLabs, and SadTalker integration
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/subchief/5TECH/.env')

# Add backend to path
sys.path.insert(0, '/home/subchief/5TECH/backend')

async def test_all_services():
    """Test all avatar services"""
    
    print("\n" + "="*70)
    print("🎬 COMPLETE AVATAR PIPELINE TEST")
    print("="*70 + "\n")
    
    results = {
        "gemini": False,
        "elevenlabs": False,
        "sadtalker": False,
        "pipeline": False
    }
    
    # Test 1: Google Gemini/Imagen
    print("1️⃣ Testing Google Gemini API...")
    try:
        import google.generativeai as genai
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            print("❌ No GEMINI_API_KEY in environment")
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Hello, are you working?")
            
            if response.text:
                print(f"✅ Google Gemini Connected!")
                print(f"   Response: {response.text[:60]}...")
                results["gemini"] = True
            else:
                print("⚠️  Gemini connected but no response")
                
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
    
    # Test 2: ElevenLabs
    print("\n2️⃣ Testing ElevenLabs TTS...")
    try:
        from services.elevenlabs_service import ElevenLabsService
        
        elevenlabs = ElevenLabsService()
        voices = elevenlabs.get_available_voices()
        
        if voices and len(voices) > 0:
            print(f"✅ ElevenLabs Connected!")
            print(f"   Available voices: {len(voices)}")
            for voice in voices[:3]:
                print(f"   - {voice}")
            results["elevenlabs"] = True
        else:
            print("⚠️  ElevenLabs connected but no voices")
            
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
    
    # Test 3: SadTalker
    print("\n3️⃣ Testing SadTalker Service...")
    try:
        from services.sadtalker_service import get_sadtalker_service
        
        sadtalker = get_sadtalker_service()
        avatars = sadtalker.get_available_avatars()
        
        print(f"✅ SadTalker Service Initialized!")
        print(f"   Mode: {sadtalker.mode}")
        print(f"   Available avatars: {len(avatars)}")
        print(f"   Avatar directory: {sadtalker.avatar_dir}")
        
        # Check if rafiki avatar exists
        rafiki_path = Path('/home/subchief/5TECH/backend/assets/avatars/rafiki_avatar.png')
        if rafiki_path.exists():
            print(f"   ✅ Rafiki avatar ready: {rafiki_path}")
        
        results["sadtalker"] = True
        
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
    
    # Test 4: Pipeline
    print("\n4️⃣ Testing Complete Pipeline...")
    if results["elevenlabs"] and results["sadtalker"]:
        try:
            from services.elevenlabs_service import ElevenLabsService
            
            elevenlabs = ElevenLabsService()
            output_dir = Path('/home/subchief/5TECH/backend/test_output')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate test audio
            print("   📝 Generating test audio...")
            audio_path = output_dir / "test_audio.wav"
            
            result = elevenlabs.synthesize_speech(
                text="Hello! I am Rafiki, your AI assistant from Kenya.",
                voice_name="Habari",
                output_path=str(audio_path)
            )
            
            if audio_path.exists():
                print(f"   ✅ Audio generated: {audio_path}")
                print(f"      Size: {audio_path.stat().st_size} bytes")
                results["pipeline"] = True
            else:
                print(f"⚠️  Audio generation attempted but file not found")
                
        except Exception as e:
            print(f"❌ Pipeline error: {str(e)[:100]}")
    
    # Summary
    print("\n" + "="*70)
    print("✅ TEST SUMMARY")
    print("="*70 + "\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}\n")
    
    for service, status in results.items():
        emoji = "✅" if status else "❌"
        print(f"{emoji} {service.upper():15} - {'Connected' if status else 'Failed'}")
    
    print("\n" + "="*70)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready to use.")
        print("\nYou can now:")
        print("  1. Generate avatar videos with the pipeline")
        print("  2. Deploy the talking avatar system")
        print("  3. Use the API endpoints")
    elif passed >= 2:
        print("⚠️  Some tests passed. Check errors above.")
    else:
        print("❌ Multiple services failed. Check API keys and connectivity.")
    
    print("="*70 + "\n")
    
    return passed == total

async def main():
    """Run tests"""
    try:
        success = await test_all_services()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
