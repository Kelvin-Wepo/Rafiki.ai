"""
Test script for avatar personality system

Tests the personality presets and generation methods
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.sadtalker_service import SadTalkerService


async def test_personality_system():
    """Test the personality system"""
    
    print("🎭 Testing Avatar Personality System\n")
    print("=" * 50)
    
    # Initialize service
    service = SadTalkerService()
    
    # Test 1: Default personality
    print("\n1. Default Personality:")
    print(f"   Current: {service.get_personality()}")
    print(f"   Settings: {service.settings}")
    
    # Test 2: Available personalities
    print("\n2. Available Personalities:")
    for name, preset in service.PERSONALITY_PRESETS.items():
        print(f"   - {name}:")
        for key, value in preset.items():
            print(f"     {key}: {value}")
    
    # Test 3: Change personality
    print("\n3. Testing Personality Changes:")
    for personality in ['professional', 'excited', 'calm', 'friendly']:
        success = service.set_personality(personality)
        if success:
            print(f"   ✓ Changed to '{personality}'")
            print(f"     Expression scale: {service.settings['expression_scale']}")
            print(f"     Still mode: {service.settings['still_mode']}")
            print(f"     Enhancer: {service.settings['enhancer']}")
        else:
            print(f"   ✗ Failed to change to '{personality}'")
    
    # Test 4: Invalid personality
    print("\n4. Testing Invalid Personality:")
    success = service.set_personality('invalid_mood')
    if not success:
        print("   ✓ Correctly rejected invalid personality")
    else:
        print("   ✗ Unexpectedly accepted invalid personality")
    
    # Test 5: Check available avatars
    print("\n5. Available Avatars:")
    avatars = service.get_available_avatars()
    for avatar in avatars:
        print(f"   - {avatar['name']} (ID: {avatar['id']})")
        if avatar['path']:
            print(f"     Path: {avatar['path']}")
    
    # Test 6: Settings persistence
    print("\n6. Settings Persistence Test:")
    service.set_personality('excited')
    print(f"   Set to 'excited': expression_scale = {service.settings['expression_scale']}")
    
    service.set_personality('calm')
    print(f"   Set to 'calm': expression_scale = {service.settings['expression_scale']}")
    
    print("\n" + "=" * 50)
    print("✅ Personality system tests completed!\n")


if __name__ == "__main__":
    asyncio.run(test_personality_system())
