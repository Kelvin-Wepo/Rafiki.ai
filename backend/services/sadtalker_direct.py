"""
Direct SadTalker Integration
Uses SadTalker directly without API server for better performance
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# Add SadTalker to path
SADTALKER_PATH = Path(__file__).parent.parent.parent / "SadTalker"
# Use the actual venv path where packages are installed - SadTalker code is in /home/subchief/5TECH/SadTalker
# but the Python environment with all packages is in /home/subchief/SadTalker/venv
SADTALKER_VENV_PYTHON = Path("/home/subchief/SadTalker/venv/bin/python")
sys.path.insert(0, str(SADTALKER_PATH))

def check_sadtalker_available() -> bool:
    """Check if SadTalker is properly installed"""
    try:
        # Check if SadTalker directory exists
        if not SADTALKER_PATH.exists():
            print(f"❌ SadTalker not found at {SADTALKER_PATH}")
            return False
        
        # Check for checkpoints
        checkpoint_dir = SADTALKER_PATH / "checkpoints"
        if not checkpoint_dir.exists() or not any(checkpoint_dir.iterdir()):
            print(f"❌ SadTalker checkpoints not found at {checkpoint_dir}")
            print("   Run: cd SadTalker && bash scripts/download_models.sh")
            return False
        
        # Check if venv Python exists
        if not SADTALKER_VENV_PYTHON.exists():
            print(f"❌ SadTalker venv Python not found at {SADTALKER_VENV_PYTHON}")
            return False
        
        # Check if torch is installed in venv using subprocess
        result = subprocess.run(
            [str(SADTALKER_VENV_PYTHON), "-c", "import torch; print(torch.__version__)"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"❌ PyTorch not available in SadTalker venv")
            print(f"   Install with: cd {SADTALKER_PATH} && source venv/bin/activate && pip install -r requirements.txt")
            return False
        
        print(f"✅ PyTorch {result.stdout.strip()} available in SadTalker venv")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"❌ SadTalker check timed out")
        return False
    except Exception as e:
        print(f"❌ SadTalker check failed: {e}")
        return False


def generate_video_direct(
    source_image: str,
    driven_audio: str,
    output_path: str,
    preprocess: str = 'crop',
    still_mode: bool = False,
    expression_scale: float = 1.0,
    enhancer: bool = False,
    batch_size: int = 1,  # Reduced to 1 for stability
    size: int = 256,
    pose_style: int = 0
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate talking head video directly using SadTalker in its own venv
    
    Args:
        source_image: Path to source image
        driven_audio: Path to audio file
        output_path: Path to save output video
        preprocess: 'crop', 'resize', 'full', 'extcrop', 'extfull'
        still_mode: Reduce head motion
        expression_scale: Scale of facial expressions
        enhancer: Use GFPGAN face enhancer
        batch_size: Batch size for generation
        size: Face model resolution (256 or 512)
        pose_style: Pose style (0-46)
    
    Returns:
        Tuple of (output_path, error_message)
    """
    import json
    import tempfile
    
    try:
        # Create config file for subprocess
        config = {
            'source_image': source_image,
            'driven_audio': driven_audio,
            'output_path': output_path,
            'preprocess': preprocess,
            'still_mode': still_mode,
            'expression_scale': expression_scale,
            'enhancer': enhancer,
            'batch_size': batch_size,
            'size': size,
            'pose_style': pose_style
        }
        
        # Write config to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_file = f.name
        
        try:
            # Run SadTalker in its own venv
            runner_script = SADTALKER_PATH / "run_sadtalker.py"
            
            print(f"🎬 Generating video with SadTalker...")
            print(f"   Source: {source_image}")
            print(f"   Audio: {driven_audio}")
            print(f"   Settings: preprocess={preprocess}, still={still_mode}, scale={expression_scale}")
            print(f"   Size: {size}x{size}, Batch: {batch_size}, Enhancer: {enhancer}")
            print(f"   ⏳ This may take 2-5 minutes on CPU...")
            
            result = subprocess.run(
                [str(SADTALKER_VENV_PYTHON), str(runner_script), config_file],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout for CPU generation
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}  # Force unbuffered output
            )
            
            # Parse result
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout.strip())
                    if output.get('success'):
                        video_path = output.get('output_path')
                        if video_path and os.path.exists(video_path):
                            print(f"✅ Video generated successfully: {video_path}")
                            return video_path, None
                        else:
                            return None, "Video file not found after generation"
                    else:
                        error = output.get('error', 'Unknown error')
                        print(f"❌ SadTalker failed: {error}")
                        return None, error
                except json.JSONDecodeError:
                    print(f"❌ Failed to parse SadTalker output")
                    print(f"   stdout: {result.stdout}")
                    print(f"   stderr: {result.stderr}")
                    return None, "Failed to parse generation output"
            else:
                print(f"❌ SadTalker process failed with code {result.returncode}")
                print(f"   stderr: {result.stderr}")
                return None, f"Generation failed: {result.stderr}"
        
        finally:
            # Clean up config file
            try:
                os.unlink(config_file)
            except:
                pass
        
    except subprocess.TimeoutExpired:
        print(f"❌ SadTalker generation timed out (600s)")
        print(f"   💡 Tip: This is normal on CPU. Consider:")
        print(f"      - Using audio-only mode (instant)")
        print(f"      - Getting a GPU (50-100x faster)")
        print(f"      - Pre-generating common phrases")
        return None, "Video generation timed out"
    except Exception as e:
        print(f"❌ SadTalker error: {e}")
        import traceback
        traceback.print_exc()
        return None, str(e)


if __name__ == '__main__':
    # Test the integration
    print("Testing SadTalker integration...")
    
    if check_sadtalker_available():
        print("✅ SadTalker is available and ready!")
    else:
        print("❌ SadTalker is not properly configured")
        sys.exit(1)
