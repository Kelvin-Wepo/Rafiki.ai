
"""
Lip-Sync Pipeline Debug Test Script

This script tests the lip-sync pipeline end-to-end with detailed logging.
Run with: python scripts/test_lipsync_debug.py

It will:
1. Validate the avatar image exists
2. Generate test audio using TTS (or use existing audio)
3. Run the lip-sync pipeline
4. Save debug artifacts (intermediate frames, logs)
5. Output the final video path
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Configure verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/lipsync_debug.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)


def create_test_audio(output_path: str, text: str = "Hello! I am Rafiki, your AI tax assistant.") -> str:
    """Generate test audio using pyttsx3 or gTTS"""
    logger.info(f"Creating test audio: {output_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    
    # Try pyttsx3 first (offline)
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Audio created with pyttsx3: {output_path}")
            return output_path
    except Exception as e:
        logger.warning(f"pyttsx3 failed: {e}")
    
    # Try gTTS (requires internet)
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='en')
        tts.save(output_path)
        logger.info(f"Audio created with gTTS: {output_path}")
        return output_path
    except Exception as e:
        logger.warning(f"gTTS failed: {e}")
    
    # Last resort: create silent audio with ffmpeg
    try:
        import subprocess
        duration = len(text) * 0.1  # Rough estimate
        cmd = [
            'ffmpeg', '-y', '-f', 'lavfi',
            '-i', f'anullsrc=r=16000:cl=mono',
            '-t', str(duration),
            '-acodec', 'pcm_s16le',
            output_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        logger.info(f"Silent audio created with ffmpeg: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"All audio generation methods failed: {e}")
        raise


async def test_lipsync_pipeline():
    """Run the lip-sync pipeline with test inputs"""
    logger.info("=" * 60)
    logger.info("LIP-SYNC PIPELINE DEBUG TEST")
    logger.info("=" * 60)
    
    # Paths
    base_dir = Path(__file__).parent.parent / "backend"
    avatar_path = base_dir / "assets/avatars/rafiki_avatar.png"
    test_audio_path = base_dir / "cache/test_audio.wav"
    output_path = base_dir / "cache/test_lipsync_output.mp4"
    
    # Step 1: Validate avatar
    logger.info("\n[TEST STEP 1] Checking avatar image...")
    if not avatar_path.exists():
        logger.error(f"Avatar not found at {avatar_path}")
        # List available avatars
        avatar_dir = base_dir / "assets/avatars"
        if avatar_dir.exists():
            avatars = list(avatar_dir.glob("*.png")) + list(avatar_dir.glob("*.jpg"))
            logger.info(f"Available avatars: {avatars}")
            if avatars:
                avatar_path = avatars[0]
                logger.info(f"Using first available avatar: {avatar_path}")
            else:
                logger.error("No avatar images found!")
                return None
        else:
            logger.error(f"Avatar directory does not exist: {avatar_dir}")
            return None
    else:
        import cv2
        img = cv2.imread(str(avatar_path))
        logger.info(f"Avatar loaded: {avatar_path}, shape={img.shape if img is not None else 'FAILED'}")
    
    # Step 2: Generate test audio
    logger.info("\n[TEST STEP 2] Generating test audio...")
    if not test_audio_path.exists():
        create_test_audio(str(test_audio_path))
    else:
        logger.info(f"Using existing test audio: {test_audio_path}")
    
    # Step 3: Import and initialize service
    logger.info("\n[TEST STEP 3] Initializing lip-sync service...")
    try:
        from services.wav2lip_service import get_wav2lip_service
        service = get_wav2lip_service()
        status = service.get_status()
        logger.info(f"Service status: {status}")
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}", exc_info=True)
        return None
    
    # Step 4: Run pipeline
    logger.info("\n[TEST STEP 4] Running lip-sync pipeline...")
    try:
        result = await service.generate_video(
            image_path=str(avatar_path),
            audio_path=str(test_audio_path),
            output_path=str(output_path),
            fps=25
        )
        logger.info(f"Pipeline completed! Output: {result}")
        
        # Verify output
        if os.path.exists(result):
            size = os.path.getsize(result)
            logger.info(f"Output video size: {size} bytes")
            
            # Get video info with ffprobe if available
            try:
                import subprocess
                cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', result]
                probe = subprocess.run(cmd, capture_output=True, text=True)
                logger.info(f"Video info: {probe.stdout[:500]}")
            except Exception:
                pass
            
            return result
        else:
            logger.error("Output file not created!")
            return None
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return None


def main():
    """Main entry point"""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Run async test
    result = asyncio.run(test_lipsync_pipeline())
    
    if result:
        logger.info("=" * 60)
        logger.info(f"SUCCESS! Output video: {result}")
        logger.info("=" * 60)
        print(f"\n✅ Lip-sync test completed successfully!")
        print(f"   Output: {result}")
        print(f"   Logs: logs/lipsync_debug.log")
        return 0
    else:
        logger.error("=" * 60)
        logger.error("FAILED! Check logs for details.")
        logger.error("=" * 60)
        print(f"\n❌ Lip-sync test failed. Check logs/lipsync_debug.log")
        return 1


if __name__ == "__main__":
    sys.exit(main())
