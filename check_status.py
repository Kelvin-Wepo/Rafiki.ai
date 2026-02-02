#!/usr/bin/env python3
"""
Show current Rafiki system status and SadTalker configuration
"""

import sys
from pathlib import Path

def check_component(name, check_func):
    """Check a component and print status"""
    try:
        result = check_func()
        if result:
            print(f"✅ {name}")
            if isinstance(result, str):
                print(f"   {result}")
        else:
            print(f"❌ {name}")
    except Exception as e:
        print(f"❌ {name}: {e}")

def main():
    print("=" * 70)
    print("Rafiki System Status")
    print("=" * 70)
    print()
    
    # Python environment
    print("📦 Python Environment")
    sys.path.insert(0, str(Path(__file__).parent / "backend"))
    
    check_component(
        "Python version",
        lambda: f"{sys.version.split()[0]}"
    )
    
    # Core services
    print("\n🔧 Core Services")
    
    check_component(
        "FastAPI",
        lambda: __import__('fastapi').__version__
    )
    
    check_component(
        "Google Gemini",
        lambda: bool(__import__('google.genai'))
    )
    
    check_component(
        "ElevenLabs",
        lambda: bool(__import__('elevenlabs'))
    )
    
    # SadTalker
    print("\n🎬 SadTalker Configuration")
    
    sadtalker_path = Path("/home/subchief/5TECH/SadTalker")
    sadtalker_venv = Path("/home/subchief/SadTalker/venv")
    checkpoints = sadtalker_path / "checkpoints"
    
    check_component(
        "SadTalker code",
        lambda: f"Found at {sadtalker_path}" if sadtalker_path.exists() else None
    )
    
    check_component(
        "SadTalker venv",
        lambda: f"Found at {sadtalker_venv}" if sadtalker_venv.exists() else None
    )
    
    if checkpoints.exists():
        files = list(checkpoints.glob("*.safetensors"))
        if files:
            check_component(
                "SadTalker checkpoints",
                lambda: f"{len(files)} checkpoints found"
            )
            for f in files:
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"      - {f.name} ({size_mb:.1f} MB)")
        else:
            print(f"❌ No checkpoints found in {checkpoints}")
    else:
        print(f"❌ Checkpoints directory not found: {checkpoints}")
    
    # Avatar assets
    print("\n🖼️  Avatar Assets")
    
    avatar_dir = Path(__file__).parent / "backend" / "assets" / "avatars"
    cache_dir = Path(__file__).parent / "backend" / "assets" / "avatar_cache"
    
    if avatar_dir.exists():
        avatars = list(avatar_dir.glob("*.png")) + list(avatar_dir.glob("*.jpg"))
        check_component(
            "Avatar images",
            lambda: f"{len(avatars)} images found"
        )
        for img in avatars[:3]:  # Show first 3
            size_mb = img.stat().st_size / (1024 * 1024)
            print(f"      - {img.name} ({size_mb:.2f} MB)")
    else:
        print(f"❌ Avatar directory not found: {avatar_dir}")
    
    if cache_dir.exists():
        cached = list(cache_dir.glob("*.mp4"))
        if cached:
            total_size = sum(f.stat().st_size for f in cached) / (1024 * 1024)
            check_component(
                "Cached videos",
                lambda: f"{len(cached)} videos, {total_size:.1f} MB total"
            )
        else:
            print(f"ℹ️  No cached videos yet (run pregenerate_videos.py)")
    else:
        print(f"ℹ️  Cache directory will be created on first use")
    
    # Configuration
    print("\n⚙️  SadTalker Configuration")
    
    try:
        from services.sadtalker_service import (
            MAX_AUDIO_LENGTH, USE_256_MODEL, ENABLE_CACHING, CACHE_EXPIRY_HOURS
        )
        print(f"   Max audio length: {MAX_AUDIO_LENGTH} seconds")
        print(f"   Use 256 model: {USE_256_MODEL}")
        print(f"   Caching enabled: {ENABLE_CACHING}")
        print(f"   Cache expiry: {CACHE_EXPIRY_HOURS} hours")
    except Exception as e:
        print(f"   Could not load config: {e}")
    
    # Performance estimate
    print("\n⚡ Performance Estimates (CPU)")
    print("   Audio generation: 2-3 seconds")
    print("   Video (3 sec): 1-3 minutes")
    print("   Video (10 sec): 4-10 minutes")
    print("   Cached video: <100 milliseconds")
    
    # Recommendations
    print("\n💡 Recommendations")
    print("   1. Use audio-only mode for real-time responses")
    print("   2. Pre-generate common phrases: python3 backend/pregenerate_videos.py")
    print("   3. Test SadTalker: python3 test_sadtalker_quick.py")
    print("   4. Consider GPU for practical video generation")
    
    print("\n" + "=" * 70)
    print("Documentation:")
    print("   - SADTALKER_OPTIMIZATIONS.md - Full optimization details")
    print("   - SADTALKER_TROUBLESHOOTING.md - Problem solving")
    print("   - SADTALKER_NEXT_STEPS.md - What to do next")
    print("=" * 70)

if __name__ == "__main__":
    main()
