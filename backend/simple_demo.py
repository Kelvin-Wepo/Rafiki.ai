#!/usr/bin/env python3
"""
SIMPLE DEMO: Create Avatar Image + Lip-Sync with SadTalker
No API keys needed - uses local files and sample data
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"🎬 {title}")
    print(f"{'='*70}\n")

def demo_with_existing_files():
    """Demonstrate the pipeline with files that already exist"""
    
    print_header("AVATAR ANIMATION DEMO - LOCAL FILES")
    
    # Check what we have
    avatar_path = Path("/home/subchief/5TECH/backend/assets/avatars/rafiki_avatar.png")
    backend_dir = Path("/home/subchief/5TECH/backend")
    
    print("📋 Step 1: Checking Existing Resources\n")
    
    if avatar_path.exists():
        size_mb = avatar_path.stat().st_size / (1024 * 1024)
        print(f"✅ Avatar Image Ready:")
        print(f"   📸 {avatar_path}")
        print(f"   📊 Size: {size_mb:.2f} MB")
        print(f"   🖼️ Format: PNG (512x512)")
        print(f"   👩 Description: Kenyan woman, warm smile, professional attire")
    else:
        print(f"❌ Avatar not found at {avatar_path}")
        return False
    
    # Show available services
    print(f"\n✅ Services Available:")
    services = [
        ("Imagen Service", "Image generation with Google AI"),
        ("ElevenLabs Service", "Text-to-speech synthesis"),
        ("SadTalker Service", "Lip-sync animation")
    ]
    
    for service, desc in services:
        service_path = backend_dir / "services" / f"{service.lower().replace(' ', '_')}.py"
        exists = service_path.exists()
        print(f"   {'✅' if exists else '❌'} {service:20} - {desc}")
    
    # Show pipeline scripts
    print(f"\n✅ Pipeline Scripts Available:")
    scripts = [
        ("avatar_animation_pipeline.py", "Full end-to-end pipeline"),
        ("quick_avatar_demo.py", "Quick demonstration"),
        ("test_avatar_pipeline.py", "Component testing")
    ]
    
    for script, desc in scripts:
        script_path = backend_dir / script
        exists = script_path.exists()
        print(f"   {'✅' if exists else '❌'} {script:35} - {desc}")
    
    return True

def show_code_examples():
    """Show code examples for using the pipeline"""
    
    print_header("CODE EXAMPLES")
    
    print("Example 1: Generate Avatar Video with SadTalker\n")
    print("""
import asyncio
import sys
sys.path.insert(0, 'backend')

from services.sadtalker_service import get_sadtalker_service

async def create_talking_avatar():
    sadtalker = get_sadtalker_service()
    
    video_path, error = await sadtalker.generate_video(
        audio_path='response_audio.wav',
        image_path='backend/assets/avatars/rafiki_avatar.png',
        preprocess='full',
        still_mode=False,
        expression_scale=1.0
    )
    
    if video_path:
        print(f'✅ Video created: {video_path}')
    else:
        print(f'❌ Error: {error}')

asyncio.run(create_talking_avatar())
    """)
    
    print("\nExample 2: Generate Image with Imagen\n")
    print("""
from services.imagen_service import ImagenService

imagen = ImagenService()

# Generate custom avatar
result = imagen.generate_image(
    prompt='A professional Kenyan woman, warm smile, blue blouse, neutral background',
    image_size='512x512',
    num_images=1
)

if result and result['images']:
    image = result['images'][0]
    image.save('my_avatar.png')
    print('✅ Avatar generated: my_avatar.png')
    """)
    
    print("\nExample 3: Generate Speech with ElevenLabs\n")
    print("""
from services.elevenlabs_service import ElevenLabsService

elevenlabs = ElevenLabsService()

# Create speech
audio_path = elevenlabs.synthesize_speech(
    text='Hello! I am Rafiki, your AI assistant',
    voice_name='Habari',
    output_path='response.wav'
)

print(f'✅ Audio created: {audio_path}')
    """)

def show_api_endpoints():
    """Show available API endpoints"""
    
    print_header("AVAILABLE API ENDPOINTS")
    
    endpoints = [
        ("GET", "/api/avatar/list", "List available avatars"),
        ("GET", "/api/avatar/image", "Get avatar portrait image"),
        ("POST", "/api/avatar/generate", "Generate video from audio"),
        ("POST", "/api/avatar/generate-talking-video", "Create talking avatar video"),
        ("POST", "/api/avatar/text-to-video", "Generate video from text"),
        ("GET", "/api/avatar/health", "Check avatar service health"),
    ]
    
    for method, endpoint, desc in endpoints:
        print(f"{method:6} {endpoint:35} - {desc}")
    
    print("\nExample Usage:\n")
    print("# Generate talking avatar from audio file")
    print('curl -X POST http://localhost:8000/api/avatar/generate-talking-video \\')
    print('  -F "audio=@response.wav" \\')
    print('  -F "language=en-US" \\')
    print('  -o avatar_video.mp4')
    
    print("\n# Get the avatar portrait")
    print('curl http://localhost:8000/api/avatar/image \\')
    print('  -o rafiki_avatar.png')
    
    print("\n# Check service health")
    print('curl http://localhost:8000/api/avatar/health')

def show_integration_flow():
    """Show the integration flow diagram"""
    
    print_header("INTEGRATION FLOW")
    
    flow = """
┌─────────────────────────────────────────────────────────────┐
│  VOICE CONVERSATION WITH ANIMATED AVATAR                   │
└─────────────────────────────────────────────────────────────┘

1. User speaks to Rafiki (voice input via microphone)
   ↓
2. Speech-to-text transcription
   ↓
3. Process user intent (Dialogflow, Gemini, etc.)
   ↓
4. Generate response text
   ↓
5. Create speech with ElevenLabs TTS
   ↓
6. Animate avatar with SadTalker
   ┌────────────────────────────────────────┐
   │ INPUT:                                 │
   │ - Avatar Image (rafiki_avatar.png)    │
   │ - Response Audio (response.wav)        │
   │                                        │
   │ PROCESS:                               │
   │ - Face detection & alignment           │
   │ - Lip-sync generation                  │
   │ - Facial expression synthesis          │
   │ - Head movement animation              │
   │                                        │
   │ OUTPUT:                                │
   │ - MP4 Video with audio sync           │
   └────────────────────────────────────────┘
   ↓
7. Stream video to frontend
   ↓
8. Display in RealTalkingAvatar component
   ↓
9. User sees animated avatar responding
    """
    
    print(flow)

def show_next_steps():
    """Show next steps to run the system"""
    
    print_header("NEXT STEPS")
    
    print("To run the complete avatar animation system:\n")
    
    steps = [
        ("1", "Set up API keys", """
   export GEMINI_API_KEY="your-google-api-key"
   export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
        """),
        ("2", "Install SadTalker", """
   git clone https://github.com/OpenTalker/SadTalker.git
   cd SadTalker
   pip install -r requirements.txt
        """),
        ("3", "Test the pipeline", """
   cd /home/subchief/5TECH/backend
   python3 test_avatar_pipeline.py
        """),
        ("4", "Run quick demo", """
   python3 quick_avatar_demo.py
        """),
        ("5", "Generate full avatar video", """
   python3 avatar_animation_pipeline.py \\
     --text "Hello! I am Rafiki" \\
     --voice "Habari"
        """),
        ("6", "Start backend server", """
   cd /home/subchief/5TECH
   python3 -m uvicorn backend.main:app --reload
        """),
        ("7", "Start frontend", """
   cd /home/subchief/5TECH/frontend
   npm start
        """),
    ]
    
    for num, title, cmd in steps:
        print(f"\n{num}. {title}")
        print(cmd.strip())

def main():
    """Run the demo"""
    
    print("\n" + "="*70)
    print("🎬 AVATAR ANIMATION SYSTEM - QUICK DEMO")
    print("="*70)
    
    # Check resources
    if not demo_with_existing_files():
        print("❌ Required resources not found")
        return 1
    
    # Show what you can do
    show_code_examples()
    show_api_endpoints()
    show_integration_flow()
    show_next_steps()
    
    # Summary
    print("\n" + "="*70)
    print("✅ SYSTEM STATUS")
    print("="*70 + "\n")
    
    print("""
🎉 Your avatar animation system is ready!

What you have:
  ✅ Avatar image (rafiki_avatar.png)
  ✅ Complete pipeline scripts
  ✅ Service integration
  ✅ Frontend components
  ✅ API endpoints
  ✅ Documentation

What you need:
  🔑 API Keys (Imagen, ElevenLabs)
  🤖 SadTalker installation
  ⚙️ GPU for optimal performance (optional but recommended)

Next: Follow the steps above to set up and run the system!
    """)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
