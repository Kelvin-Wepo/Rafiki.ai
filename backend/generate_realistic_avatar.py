#!/usr/bin/env python3
"""
Generate realistic avatar with Google's Gemini Vision API
Using image generation via proper API method
"""

import os
import sys
import requests
from pathlib import Path

# Your API keys
GEMINI_API_KEY = "AIzaSyDgR5KbuW5IKAMc8vW0xvoTvr5WsxruPs8"
OUTPUT_DIR = Path("/home/subchief/5TECH/backend/assets/avatars")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_avatar_with_image_generation_api():
    """
    Generate avatar using Imagen API via REST endpoint
    """
    print("🎨 Generating realistic avatar with Imagen API...\n")
    
    # Use Google's Imagen API endpoint
    url = "https://us-central1-aiplatform.googleapis.com/v1/projects/octo-project-444411/locations/us-central1/publishers/google/models/imagegeneration@006:predict"
    
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "instances": [
            {
                "prompt": """
                Professional portrait photo of a beautiful Kenyan woman in her late 20s/early 30s.
                She has warm, intelligent eyes and a genuine, welcoming smile.
                She is wearing a light blue professional blouse/shirt.
                Her skin tone is a rich, warm brown.
                Natural African hairstyle, elegant and professional.
                Head and shoulders framing, centered composition.
                She is looking directly at the camera with a friendly expression.
                Professional studio lighting with soft shadows.
                Neutral beige or light blue background.
                High quality, photorealistic portrait.
                Professional headshot style suitable for an AI assistant avatar.
                No glasses, no obstructions, clear face.
                Resolution: 512x512 pixels.
                """
            }
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1"
        }
    }
    
    try:
        print("📡 Calling Imagen API...")
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            print("✅ API Response: Success!")
            data = response.json()
            print(f"Response: {data}\n")
            return data
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}\n")
            return None
            
    except Exception as e:
        print(f"❌ Error calling Imagen API: {e}\n")
        return None


def generate_avatar_with_stable_diffusion():
    """
    Fallback: Generate avatar using Hugging Face Stable Diffusion API
    """
    print("🎨 Generating avatar with Stable Diffusion...\n")
    
    # Using Hugging Face's free inference API
    HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    if not HF_API_KEY:
        print("⚠️  No Hugging Face API key found")
        return None
    
    url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
    
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    payload = {
        "inputs": """
        Professional portrait photo of a beautiful Kenyan woman, 
        warm smile, light blue blouse, professional headshot, 
        512x512, photorealistic, high quality
        """
    }
    
    try:
        print("📡 Calling Stable Diffusion API...")
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            print("✅ API Response: Success!")
            
            # Save image
            avatar_path = OUTPUT_DIR / "rafiki_avatar_hf.png"
            with open(avatar_path, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Avatar saved: {avatar_path}\n")
            return str(avatar_path)
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}\n")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None


def create_enhanced_avatar_locally():
    """
    Create an enhanced version of the existing avatar with better colors
    """
    print("🎨 Enhancing existing avatar with better design...\n")
    
    try:
        from PIL import Image, ImageDraw, ImageFilter
        import random
        
        # Create a beautiful avatar with enhanced design
        width, height = 512, 512
        
        # Create image with gradient background
        img = Image.new('RGB', (width, height), color='white')
        pixels = img.load()
        
        # Create smooth gradient background (light blue to cream)
        for y in range(height):
            ratio = y / height
            r = int(245 - (30 * ratio))
            g = int(245 - (45 * ratio))
            b = int(245 - (70 * ratio))
            
            for x in range(width):
                pixels[x, y] = (r, g, b)
        
        # Apply soft blur to background for polish
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Draw face (warm brown Kenyan skin tone)
        face_color = (201, 130, 95)  # Warm brown
        
        # Face oval
        face_bbox = [100, 80, 412, 420]
        draw.ellipse(face_bbox, fill=face_color)
        
        # Neck and shoulders
        draw.rectangle([180, 380, 332, 450], fill=face_color)
        
        # Draw professional blue blouse/shirt
        blouse_color = (65, 140, 180)  # Professional blue
        draw.rectangle([120, 350, 392, 450], fill=blouse_color)
        draw.ellipse([140, 330, 372, 380], fill=blouse_color)  # Collar
        
        # Eyes with depth
        eye_white = (255, 255, 255)
        iris_color = (40, 20, 10)  # Dark brown
        
        # Left eye
        draw.ellipse([180, 200, 230, 250], fill=eye_white)
        draw.ellipse([195, 215, 215, 235], fill=iris_color)
        draw.ellipse([205, 220, 210, 225], fill=(255, 255, 255))  # Highlight
        
        # Right eye  
        draw.ellipse([282, 200, 332, 250], fill=eye_white)
        draw.ellipse([297, 215, 317, 235], fill=iris_color)
        draw.ellipse([307, 220, 312, 225], fill=(255, 255, 255))  # Highlight
        
        # Eyebrows
        eyebrow_color = (50, 30, 20)
        draw.arc([170, 190, 240, 210], 0, 180, fill=eyebrow_color, width=5)
        draw.arc([272, 190, 342, 210], 0, 180, fill=eyebrow_color, width=5)
        
        # Nose (simple triangle shape)
        nose_color = (180, 100, 70)
        draw.line([(256, 260), (256, 310)], fill=nose_color, width=3)
        draw.ellipse([245, 305, 267, 320], fill=nose_color)
        
        # Mouth with warm smile
        mouth_color = (160, 80, 60)  # Warm reddish-brown
        # Draw smile arc
        draw.arc([200, 310, 312, 360], 0, 180, fill=mouth_color, width=4)
        # Fill smile with lighter color
        for y in range(330, 350):
            for x in range(210, 302):
                # Create smile shape
                dist_from_center = ((x - 256) ** 2 + (y - 335) ** 2) ** 0.5
                if dist_from_center < 50:
                    pixels[x, y] = (210, 140, 110)
        
        # Hair (natural African hair)
        hair_color = (20, 10, 5)
        
        # Draw hair outline
        hair_points = []
        for angle in range(0, 360, 10):
            import math
            rad = math.radians(angle)
            # Hair sits above the face
            x = 256 + 170 * math.cos(rad)
            y = 100 + 140 * math.sin(rad)
            if y < 200:  # Only top half
                hair_points.append((x, y))
        
        if len(hair_points) > 2:
            draw.polygon(hair_points + [(100, 100), (412, 100)], fill=hair_color)
        
        # Add subtle texture to hair with small dots
        for _ in range(100):
            x = random.randint(150, 362)
            y = random.randint(80, 180)
            draw.ellipse([x, y, x+2, y+2], fill=(10, 5, 0))
        
        # Add professional lighting effect (subtle highlight)
        highlight_color = (255, 255, 255, 80)
        draw.ellipse([150, 120, 220, 180], fill=highlight_color)
        
        # Save the enhanced avatar
        avatar_path = OUTPUT_DIR / "rafiki_avatar.png"
        img.save(avatar_path, 'PNG', quality=95)
        
        file_size = avatar_path.stat().st_size / 1024
        print(f"✅ Enhanced avatar created!")
        print(f"   📸 Path: {avatar_path}")
        print(f"   📊 Size: {file_size:.2f} KB")
        print(f"   🖼️  Dimensions: 512x512 pixels")
        print(f"   👩 Description: Professional Kenyan woman, warm smile, blue blouse\n")
        
        return str(avatar_path)
        
    except Exception as e:
        print(f"❌ Error creating avatar: {e}\n")
        return None


def main():
    """Main execution"""
    
    print("\n" + "="*70)
    print("🎨 AVATAR GENERATION - WITH HUMAN TOUCH")
    print("="*70 + "\n")
    
    # Try Imagen API first
    result = generate_avatar_with_image_generation_api()
    
    if result:
        print("✅ Successfully generated with Imagen API!")
        return 0
    
    # Fallback to Stable Diffusion
    print("⚠️  Trying Stable Diffusion fallback...\n")
    result = generate_avatar_with_stable_diffusion()
    
    if result:
        print("✅ Successfully generated with Stable Diffusion!")
        return 0
    
    # Final fallback: Enhanced local avatar
    print("⚠️  Using enhanced local avatar generation...\n")
    result = create_enhanced_avatar_locally()
    
    if result:
        print("=" * 70)
        print("✅ AVATAR READY FOR USE")
        print("=" * 70 + "\n")
        print(f"The avatar is now available at: {result}")
        print("Copy it to the frontend public folder: cp {result} ../frontend/public/rafiki_avatar.png")
        return 0
    else:
        print("❌ All avatar generation methods failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
