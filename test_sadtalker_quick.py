#!/usr/bin/env python3
"""
Quick SadTalker test - minimal setup
Tests if SadTalker can generate a video without timing out
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from services.sadtalker_direct import check_sadtalker_available, generate_video_direct
import tempfile
import subprocess

def create_test_audio(duration=3):
    """Create a short test audio file"""
    output = tempfile.mktemp(suffix=".wav")
    
    # Generate 3 second beep using ffmpeg
    subprocess.run([
        'ffmpeg', '-f', 'lavfi', '-i', 
        f'sine=frequency=440:duration={duration}',
        '-ar', '16000', '-ac', '1', output, '-y'
    ], capture_output=True)
    
    return output if Path(output).exists() else None

def main():
    print("=" * 70)
    print("SadTalker Quick Test")
    print("=" * 70)
    
    # 1. Check if SadTalker is available
    print("\n1. Checking SadTalker installation...")
    if not check_sadtalker_available():
        print("\n❌ SadTalker is not properly configured!")
        print("   Please run: cd SadTalker && bash scripts/download_models.sh")
        return 1
    
    print("✅ SadTalker is available\n")
    
    # 2. Check avatar image
    print("2. Checking avatar image...")
    avatar_path = Path(__file__).parent / "backend" / "assets" / "avatars" / "rafiki_avatar.png"
    if not avatar_path.exists():
        print(f"❌ Avatar not found: {avatar_path}")
        return 1
    print(f"✅ Avatar found: {avatar_path}\n")
    
    # 3. Create test audio
    print("3. Creating test audio (3 seconds)...")
    audio_path = create_test_audio(3)
    if not audio_path:
        print("❌ Failed to create test audio")
        return 1
    print(f"✅ Test audio created: {audio_path}\n")
    
    # 4. Generate video
    print("4. Generating video with SadTalker...")
    print("   ⏳ This will take 1-3 minutes on CPU...")
    print("   Settings: 256x256, crop preprocessing, no enhancer")
    print("   Starting now...\n")
    
    output_path = tempfile.mktemp(suffix=".mp4")
    
    video_path, error = generate_video_direct(
        source_image=str(avatar_path),
        driven_audio=audio_path,
        output_path=output_path,
        preprocess='crop',
        still_mode=False,
        expression_scale=1.0,
        enhancer=False,
        batch_size=1,
        size=256,
        pose_style=0
    )
    
    # 5. Check results
    print("\n" + "=" * 70)
    if video_path and Path(video_path).exists():
        size_mb = Path(video_path).stat().st_size / (1024 * 1024)
        print("✅ SUCCESS! Video generated!")
        print(f"   Path: {video_path}")
        print(f"   Size: {size_mb:.2f} MB")
        print("\nYou can play it with: ffplay " + video_path)
        print("=" * 70)
        return 0
    else:
        print("❌ FAILED! Video generation failed")
        print(f"   Error: {error}")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
