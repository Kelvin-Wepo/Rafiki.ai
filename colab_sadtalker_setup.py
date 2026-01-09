#!/usr/bin/env python3
"""
Google Colab SadTalker Setup
This notebook will run on Colab with GPU for fast video generation
"""

# Cell 1: Setup and Installation
setup_code = '''
# Install required packages
!pip install -q torch torchvision torchaudio
!pip install -q gradio==3.50.2
!pip install -q imageio-ffmpeg
!pip install -q gfpgan
!pip install -q basicsr
!pip install -q realesrgan
!pip install -q safetensors
!pip install -q ngrok pyngrok

# Clone SadTalker
!git clone https://github.com/OpenTalker/SadTalker.git
%cd SadTalker

# Download models
!bash scripts/download_models.sh

# Install dependencies
!pip install -q -r requirements.txt

print("✅ Setup complete!")
'''

# Cell 2: Start API Server with ngrok
api_server_code = '''
from pyngrok import ngrok
import threading
import time

# Set ngrok auth token (you'll need to get this from ngrok.com)
# !ngrok config add-authtoken YOUR_NGROK_TOKEN

def start_gradio():
    """Start Gradio interface"""
    import gradio as gr
    from inference import SadTalker
    
    sad_talker = SadTalker(
        checkpoint_path='checkpoints',
        config_path='src/config',
        lazy_load=True
    )
    
    def generate_video(source_image, driven_audio, preprocess='crop', 
                      still_mode=False, expression_scale=1.0, enhancer=False):
        """Generate talking head video"""
        try:
            result = sad_talker.test(
                source_image=source_image,
                driven_audio=driven_audio,
                preprocess=preprocess,
                still_mode=still_mode,
                expression_scale=expression_scale,
                enhancer='gfpgan' if enhancer else None,
                batch_size=1,
                size=256
            )
            return result
        except Exception as e:
            return f"Error: {str(e)}"
    
    interface = gr.Interface(
        fn=generate_video,
        inputs=[
            gr.Image(type="filepath", label="Source Image"),
            gr.Audio(type="filepath", label="Driven Audio"),
            gr.Dropdown(['crop', 'resize', 'full'], value='crop', label="Preprocess"),
            gr.Checkbox(label="Still Mode (minimal head movement)"),
            gr.Slider(0.0, 2.0, value=1.0, label="Expression Scale"),
            gr.Checkbox(label="Use Face Enhancer")
        ],
        outputs=gr.Video(label="Generated Video"),
        title="SadTalker - GPU Accelerated",
        description="Fast talking head video generation with GPU"
    )
    
    interface.launch(share=True, server_port=7860)

# Start server in background
thread = threading.Thread(target=start_gradio)
thread.daemon = True
thread.start()

# Create public URL with ngrok
public_url = ngrok.connect(7860)
print(f"\\n{'='*70}")
print(f"🚀 SadTalker API is running!")
print(f"{'='*70}")
print(f"\\nPublic URL: {public_url}")
print(f"\\nCopy this URL to use in your backend!")
print(f"{'='*70}\\n")

# Keep alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\\nShutting down...")
'''

# Cell 3: Test Generation
test_code = '''
# Upload test files or use examples
from IPython.display import Video
import os

# Use example files
source_image = "examples/source_image/full_body_1.png"
driven_audio = "examples/driven_audio/bus_chinese.wav"

# Generate video
print("Generating video...")
result = sad_talker.test(
    source_image=source_image,
    driven_audio=driven_audio,
    preprocess='crop',
    still_mode=False,
    expression_scale=1.0,
    batch_size=1,
    size=256
)

print(f"✅ Video generated: {result}")
Video(result)
'''

if __name__ == "__main__":
    print("=" * 70)
    print("Google Colab SadTalker Setup")
    print("=" * 70)
    print()
    print("Copy the code blocks below into Google Colab cells:")
    print()
    print("-" * 70)
    print("CELL 1: Setup")
    print("-" * 70)
    print(setup_code)
    print()
    print("-" * 70)
    print("CELL 2: Start API Server")
    print("-" * 70)
    print(api_server_code)
    print()
    print("-" * 70)
    print("CELL 3: Test (Optional)")
    print("-" * 70)
    print(test_code)
    print()
    print("=" * 70)
