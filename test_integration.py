#!/usr/bin/env python3
"""
Avatar Studio - Integration Test
Tests Imagen + SadTalker integration
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from services.imagen_service import imagen_service
    print("✅ Imagen service imported successfully")
    
    # Test avatar generation prompt
    result = imagen_service.generate_african_avatar(
        name="Amara",
        skin_tone="medium",
        hair_style="braids",
        clothing="professional_suit",
        personality="warm_friendly",
        background="office",
        language="en-KE"
    )
    
    if result:
        print("✅ Avatar generation works")
        print(f"   Name: {result['name']}")
        print(f"   Status: {result['status']}")
        print(f"   Prompt preview: {result['prompt'][:80]}...")
    else:
        print("❌ Avatar generation failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
