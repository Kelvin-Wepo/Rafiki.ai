#!/usr/bin/env python3
"""
Test script for multilingual support in Rafiki AI Assistant.
Tests English and Kiswahili language detection and TTS generation.
"""

import asyncio
import sys
sys.path.insert(0, '/home/subchief/5TECH/backend')

from services.language_service import language_detector
from services.gemini_service import gemini_service
from backend.utils.logger import get_logger

logger = get_logger(__name__)


async def test_language_detection():
    """Test language detection with various inputs."""
    print("=" * 60)
    print("Testing Language Detection")
    print("=" * 60)
    
    test_cases = [
        ("Hello, I need help with KRA nil returns", "en"),
        ("Habari, nataka msaada na nil returns", "sw"),
        ("Good morning, ninaweza kusaidia?", "mixed"),
        ("Nataka kufile nil returns for my business", "mixed"),
        ("I want to recover my KRA PIN please", "en"),
        ("Tafadhali nisaidie kupata KRA PIN mpya", "sw"),
    ]
    
    for text, expected in test_cases:
        detected, confidence = language_detector.detect(text)
        status = "✓" if (expected in ["mixed"] or detected == expected) else "✗"
        print(f"\n{status} Text: {text}")
        print(f"  Detected: {detected} ({confidence:.2f} confidence)")
        print(f"  Expected: {expected}")


async def test_code_switching():
    """Test code-switching detection."""
    print("\n" + "=" * 60)
    print("Testing Code-Switching Detection")
    print("=" * 60)
    
    text = "Hello, nataka msaada na KRA PIN. Can you help me? Asante sana."
    
    segments = language_detector.detect_code_switches(text)
    
    print(f"\nText: {text}")
    print(f"Found {len(segments)} segments:")
    
    for i, segment in enumerate(segments):
        print(f"\n  Segment {i+1}:")
        print(f"    Text: {segment['text']}")
        print(f"    Language: {segment['language']}")
        print(f"    Position: {segment['start']}-{segment['end']}")


async def test_gemini_responses():
    """Test Gemini responses in both languages."""
    print("\n" + "=" * 60)
    print("Testing Gemini AI Responses")
    print("=" * 60)
    
    # Initialize Gemini
    if not gemini_service.initialize():
        print("✗ Failed to initialize Gemini service")
        return
    
    print("✓ Gemini service initialized")
    
    test_messages = [
        ("I need help filing nil returns", "en"),
        ("Nataka msaada kufile nil returns", "sw"),
        ("Hello, ninaweza kupata KRA PIN?", "auto"),
    ]
    
    for message, language in test_messages:
        print(f"\n\nUser ({language}): {message}")
        
        try:
            response = await gemini_service.process_message(
                message,
                language=language
            )
            
            print(f"✓ Response generated:")
            print(f"  Text: {response.get('text', 'No response')[:200]}...")
            print(f"  Detected Language: {response.get('language_detected', 'unknown')}")
            print(f"  Confidence: {response.get('language_confidence', 0):.2f}")
            print(f"  Intent: {response.get('detected_intent', 'unknown')}")
            
        except Exception as e:
            print(f"✗ Error: {e}")


async def test_voice_features():
    """Test voice features for both languages."""
    print("\n" + "=" * 60)
    print("Testing Voice Features")
    print("=" * 60)
    
    from services.elevenlabs_service import ElevenLabsService
    
    service = ElevenLabsService()
    
    # Test available voices
    voices = service.get_kenyan_voices()
    print(f"\n✓ Found {len(voices)} Kenyan voices:")
    for name, voice in voices.items():
        langs = ", ".join(voice.get('languages', [voice.get('language')]))
        print(f"  - {voice['name']}: {voice['description']}")
        print(f"    Languages: {langs}")
    
    # Test speech optimization
    test_texts = [
        ("Welcome to Rafiki. I'll help you with KRA services.", "en", "government_guidance"),
        ("Karibu kwa Rafiki. Nitakusaidia na huduma za KRA.", "sw", "kiswahili_guidance"),
    ]
    
    print("\n\nTesting speech optimization:")
    for text, lang, content_type in test_texts:
        optimized = service.optimize_text_for_speech(text, content_type, lang)
        print(f"\n  Language: {lang}")
        print(f"  Original: {text}")
        print(f"  Optimized: {optimized}")


def test_language_features():
    """Test language service features."""
    print("\n" + "=" * 60)
    print("Testing Language Service Features")
    print("=" * 60)
    
    # Test keyword translation
    intents = ['kra_nil_returns', 'kra_pin_recovery', 'itax_help']
    
    for intent in intents:
        print(f"\n✓ Keywords for {intent}:")
        en_keywords = language_detector.translate_intent_keywords(intent, 'en')
        sw_keywords = language_detector.translate_intent_keywords(intent, 'sw')
        
        print(f"  English: {', '.join(en_keywords)}")
        print(f"  Kiswahili: {', '.join(sw_keywords)}")
    
    # Test code-switching support
    print(f"\n✓ Code-switching supported: {language_detector.supports_code_switching()}")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("RAFIKI AI - MULTILINGUAL SUPPORT TEST")
    print("=" * 60)
    
    try:
        # Run all tests
        await test_language_detection()
        await test_code_switching()
        test_language_features()
        await test_voice_features()
        await test_gemini_responses()
        
        print("\n" + "=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ Test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
