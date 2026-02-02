 #!/usr/bin/env python3
"""
Pre-generate common phrase videos for faster responses
Run this during startup or low-traffic periods to build cache
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.sadtalker_service import get_sadtalker_service
from backend.services.elevenlabs_service import get_elevenlabs_service

async def main():
    """Pre-generate videos for common phrases"""
    print("=" * 70)
    print("SadTalker Video Pre-generation")
    print("=" * 70)
    print("\nThis will pre-generate videos for common phrases to speed up responses.")
    print("The videos will be cached and reused when users ask common questions.\n")
    
    # Get services
    sadtalker_service = get_sadtalker_service()
    elevenlabs_service = get_elevenlabs_service()
    
    # Show current cache stats
    print("Current Cache Stats:")
    stats = sadtalker_service.get_cache_stats()
    print(f"  - Cached videos: {stats.get('cached_videos', 0)}")
    print(f"  - Total size: {stats.get('total_size_mb', 0)} MB")
    print(f"  - Cache directory: {stats.get('cache_dir', 'N/A')}\n")
    
    # Show phrases that will be generated
    print(f"Common phrases to generate ({len(sadtalker_service.common_phrases)}):")
    for i, phrase in enumerate(sadtalker_service.common_phrases, 1):
        print(f"  {i}. {phrase[:60]}{'...' if len(phrase) > 60 else ''}")
    
    print("\n" + "=" * 70)
    response = input("\nProceed with generation? [y/N]: ").strip().lower()
    
    if response != 'y':
        print("Cancelled.")
        return
    
    print("\nStarting pre-generation...\n")
    
    # Pre-generate videos
    results = await sadtalker_service.pregenerate_common_phrases(
        voice_service=elevenlabs_service,
        avatar_id="rafiki_avatar"
    )
    
    # Show results
    print("\n" + "=" * 70)
    print("Pre-generation Complete!")
    print("=" * 70)
    print(f"\n✅ Generated: {len(results['generated'])}")
    for phrase in results['generated']:
        print(f"   - {phrase}")
    
    print(f"\n📦 Already cached: {len(results['cached'])}")
    for phrase in results['cached']:
        print(f"   - {phrase}")
    
    if results['failed']:
        print(f"\n❌ Failed: {len(results['failed'])}")
        for item in results['failed']:
            print(f"   - {item['phrase']}: {item['error']}")
    
    # Show updated cache stats
    print("\nUpdated Cache Stats:")
    stats = sadtalker_service.get_cache_stats()
    print(f"  - Cached videos: {stats.get('cached_videos', 0)}")
    print(f"  - Total size: {stats.get('total_size_mb', 0)} MB")
    print(f"  - In-memory entries: {stats.get('in_memory_entries', 0)}\n")
    
    print("Videos are now cached and will load instantly when requested!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
