"""
Voice Detection Diagnostics Utility
Run this to verify all voice components are working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.voice_service import voice_service, SPEECH_RECOGNITION_AVAILABLE, PYTTSX3_AVAILABLE
from ..config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def check_dependencies():
    """Check if required dependencies are installed."""
    print_header("Checking Dependencies")
    
    status = {
        "Speech Recognition": SPEECH_RECOGNITION_AVAILABLE,
        "PyTTSx3 (TTS)": PYTTSX3_AVAILABLE,
    }
    
    for dep, available in status.items():
        status_str = "✅ INSTALLED" if available else "❌ NOT INSTALLED"
        print(f"{dep:<30} {status_str}")
    
    if not SPEECH_RECOGNITION_AVAILABLE or not PYTTSX3_AVAILABLE:
        print("\n⚠️  Missing dependencies! Install with:")
        print("   pip install speech_recognition pyttsx3")
        return False
    
    return True


def check_voice_service_init():
    """Check if voice service initializes correctly."""
    print_header("Checking Voice Service Initialization")
    
    try:
        settings = get_settings()
        print(f"Settings loaded: ✅")
        print(f"  Speech Language: {settings.SPEECH_RECOGNITION_LANGUAGE}")
        print(f"  TTS Rate: {settings.TTS_RATE}")
        print(f"  TTS Voice ID: {settings.TTS_VOICE_ID}")
        
        success = voice_service.initialize()
        if success:
            print(f"Voice Service Initialization: ✅ SUCCESS")
        else:
            print(f"Voice Service Initialization: ❌ FAILED")
            return False
            
        # Check recognizer
        if voice_service._recognizer:
            print(f"\nRecognizer Settings:")
            print(f"  Pause Threshold: {voice_service._recognizer.pause_threshold}s")
            print(f"  Phrase Threshold: {voice_service._recognizer.phrase_threshold}")
            print(f"  Non-speaking Duration: {voice_service._recognizer.non_speaking_duration}s")
            print(f"  Energy Threshold: {voice_service._recognizer.energy_threshold}")
        
        # Check TTS
        if voice_service._tts_engine:
            voices = voice_service._tts_engine.getProperty('voices')
            rate = voice_service._tts_engine.getProperty('rate')
            print(f"\nTTS Engine Settings:")
            print(f"  Available Voices: {len(voices)}")
            print(f"  Speech Rate: {rate}")
        
        return True
        
    except Exception as e:
        logger.error(f"Voice service init error: {e}", exc_info=True)
        print(f"Voice Service Initialization: ❌ FAILED")
        print(f"  Error: {e}")
        return False


async def test_tts():
    """Test text-to-speech functionality."""
    print_header("Testing Text-to-Speech")
    
    try:
        result = await voice_service.text_to_speech("Hello, this is a test.")
        
        if result.get("success"):
            print("Text-to-Speech: ✅ SUCCESS")
            print(f"  Audio data size: {len(result.get('audio_data', ''))} bytes")
            print(f"  Format: {result.get('format', 'unknown')}")
        else:
            print("Text-to-Speech: ❌ FAILED")
            print(f"  Error: {result.get('error', 'Unknown error')}")
            
        return result.get("success", False)
        
    except Exception as e:
        logger.error(f"TTS test error: {e}", exc_info=True)
        print("Text-to-Speech: ❌ ERROR")
        print(f"  Error: {e}")
        return False


async def test_microphone_detection():
    """Test microphone input detection."""
    print_header("Testing Microphone Input")
    
    try:
        import speech_recognition as sr
        
        with sr.Microphone() as source:
            print("🎤 Speak now! (listening for 5 seconds...)")
            recognizer = sr.Recognizer()
            recognizer.adjust_for_ambient_noise(source, duration=2)
            
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                print(f"Microphone: ✅ Audio captured")
                print(f"  Audio duration: {len(audio.frame_data) / audio.sample_rate:.2f}s")
                print(f"  Sample rate: {audio.sample_rate} Hz")
                print(f"  Channels: {audio.sample_width} bytes per sample")
                
                # Try to transcribe
                try:
                    text = recognizer.recognize_google(audio, language="en-KE")
                    print(f"Transcription: ✅ SUCCESS")
                    print(f"  Text: '{text}'")
                    return True
                except sr.UnknownValueError:
                    print(f"Transcription: ⚠️  Could not understand audio")
                    print("  Try speaking more clearly")
                    return False
                    
            except sr.RequestError as e:
                print(f"Transcription: ❌ Service error")
                print(f"  Error: {e}")
                print("  Check internet connection and Google Speech API")
                return False
                
    except Exception as e:
        logger.error(f"Microphone test error: {e}", exc_info=True)
        print("Microphone: ❌ ERROR")
        print(f"  Error: {e}")
        return False


async def run_diagnostics():
    """Run all diagnostic checks."""
    print("\n")
    print("╔════════════════════════════════════════════════════════╗")
    print("║      Voice Detection Diagnostic Tool v1.0              ║")
    print("║      eCitizen Voice Assistant                          ║")
    print("╚════════════════════════════════════════════════════════╝")
    
    results = {
        "Dependencies": check_dependencies(),
        "Voice Service": check_voice_service_init(),
        "Text-to-Speech": await test_tts(),
    }
    
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60 + "\n")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ All diagnostics passed! Voice detection should work.")
    else:
        print("❌ Some diagnostics failed. See details above.")
        print("\nFor microphone test, run:")
        print("  python backend/test_units.py")
        print("\nFor more help, see: VOICE_DETECTION_DEBUG.md")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_diagnostics())
