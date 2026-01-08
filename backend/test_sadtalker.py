#!/usr/bin/env python3
"""
Test SadTalker Integration
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

print("🔍 Testing SadTalker Integration...\n")

# Test 1: Check if SadTalker directory exists
sadtalker_path = backend_path.parent / "SadTalker"
print(f"1. SadTalker directory: {sadtalker_path}")
if sadtalker_path.exists():
    print("   ✅ Found")
else:
    print("   ❌ Not found")
    sys.exit(1)

# Test 2: Check checkpoints
checkpoint_dir = sadtalker_path / "checkpoints"
print(f"\n2. Checkpoints directory: {checkpoint_dir}")
if checkpoint_dir.exists():
    checkpoints = list(checkpoint_dir.glob("*.safetensors")) + list(checkpoint_dir.glob("*.pth.tar"))
    if checkpoints:
        print(f"   ✅ Found {len(checkpoints)} checkpoint files:")
        for cp in checkpoints:
            size_mb = cp.stat().st_size / (1024 * 1024)
            print(f"      - {cp.name} ({size_mb:.1f} MB)")
    else:
        print("   ❌ No checkpoint files found")
        sys.exit(1)
else:
    print("   ❌ Not found")
    sys.exit(1)

# Test 3: Check Python dependencies
print(f"\n3. Checking Python dependencies...")
try:
    sys.path.insert(0, str(sadtalker_path))
    
    print("   - Importing gradio...", end=" ")
    import gradio
    print(f"✅ v{gradio.__version__}")
    
    print("   - Importing torch...", end=" ")
    import torch
    print(f"✅ v{torch.__version__}")
    
    print("   - Importing SadTalker modules...", end=" ")
    from src.gradio_demo import SadTalker
    print("✅ Success")
    
except ImportError as e:
    print(f"❌ Failed: {e}")
    print("\n   Install dependencies:")
    print(f"   cd {sadtalker_path}")
    print("   source venv/bin/activate")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# Test 4: Try to initialize SadTalker
print(f"\n4. Initializing SadTalker...")
try:
    os.chdir(sadtalker_path)
    sad_talker = SadTalker(
        checkpoint_path='checkpoints',
        config_path='src/config',
        lazy_load=True
    )
    print("   ✅ SadTalker initialized successfully!")
except Exception as e:
    print(f"   ❌ Initialization failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ All checks passed! SadTalker is ready to use.")
print("="*50)
print("\nYou can now generate talking avatars!")
print(f"\nTo start the API server:")
print(f"  cd {sadtalker_path}")
print(f"  ./start_server.sh")
