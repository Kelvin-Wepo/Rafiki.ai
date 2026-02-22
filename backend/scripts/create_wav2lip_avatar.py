#!/usr/bin/env python3
"""
Create a realistic Kenyan woman avatar optimized for Wav2Lip lip-syncing.

Wav2Lip requirements:
- Front-facing face with clear, visible lips
- 256x256 or 512x512 resolution recommended
- Good lighting, neutral background
- Visible face landmarks for lip detection

This script generates a high-quality avatar using various methods:
1. Download a free-to-use stock photo
2. Generate using Stable Diffusion API
3. Create a stylized vector portrait as fallback
"""

import os
import sys
from pathlib import Path
import requests
import base64

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_ASSETS = PROJECT_ROOT / "backend" / "assets" / "avatars"
FRONTEND_ASSETS = PROJECT_ROOT / "frontend" / "src" / "assets"
AVATAR_FILENAME = "rafiki_avatar.png"

# Ensure directories exist
BACKEND_ASSETS.mkdir(parents=True, exist_ok=True)
FRONTEND_ASSETS.mkdir(parents=True, exist_ok=True)


def download_avatar_from_url():
    """
    Download a professional Kenyan woman portrait from a free stock photo service.
    Using a curated, royalty-free image optimized for Wav2Lip.
    """
    print("📥 Attempting to download avatar from stock photo service...")
    
    # Free stock photo URLs (royalty-free African woman portraits)
    stock_urls = [
        # Unsplash direct links to professional African woman portraits
        "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=512&h=512&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1589156280159-27698a70f29e?w=512&h=512&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=512&h=512&fit=crop&crop=face",
        # Pexels alternatives
        "https://images.pexels.com/photos/3769021/pexels-photo-3769021.jpeg?auto=compress&cs=tinysrgb&w=512&h=512&fit=crop",
    ]
    
    for url in stock_urls:
        try:
            print(f"  Trying: {url[:60]}...")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200 and len(response.content) > 10000:
                # Verify it's an image
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    print(f"  ✅ Downloaded successfully ({len(response.content)} bytes)")
                    return response.content
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            continue
    
    return None


def generate_with_replicate_api():
    """
    Generate avatar using Replicate's Stable Diffusion API.
    Requires REPLICATE_API_TOKEN environment variable.
    """
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("⚠️  REPLICATE_API_TOKEN not set, skipping Replicate generation")
        return None
    
    print("🎨 Generating avatar with Replicate Stable Diffusion...")
    
    try:
        import replicate
        
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": """Professional portrait photo of a beautiful Kenyan woman in her early 30s.
                Warm intelligent brown eyes, genuine friendly smile showing teeth slightly.
                Natural African hairstyle with neat braids or locs.
                Wearing a professional light blue blouse.
                Rich warm brown skin tone, clear complexion.
                Looking directly at camera, front-facing view.
                Professional studio lighting, soft shadows.
                Neutral gray or beige background.
                High quality professional headshot.
                Perfect for AI assistant avatar.
                512x512 resolution, photorealistic.""",
                "negative_prompt": "sunglasses, glasses, hat, hands, fingers, cartoon, anime, drawing, blurry, distorted, ugly",
                "width": 512,
                "height": 512,
                "num_outputs": 1,
            }
        )
        
        if output and len(output) > 0:
            image_url = output[0]
            response = requests.get(image_url)
            if response.status_code == 200:
                print("  ✅ Generated successfully")
                return response.content
                
    except Exception as e:
        print(f"  ❌ Replicate generation failed: {e}")
    
    return None


def create_stylized_avatar():
    """
    Create a stylized vector-style avatar as fallback.
    This is optimized for Wav2Lip with clear face features.
    """
    print("🎨 Creating stylized avatar with PIL...")
    
    try:
        from PIL import Image, ImageDraw, ImageFilter
        import math
        
        # Create 512x512 image
        size = 512
        img = Image.new('RGB', (size, size), '#E8DCC8')  # Warm neutral background
        draw = ImageDraw.Draw(img)
        
        # Face shape (oval) - warm brown skin tone
        skin_color = '#8B5A3C'  # Warm brown
        face_center = (size // 2, size // 2 + 20)
        face_width = 180
        face_height = 220
        
        # Draw face
        face_bbox = [
            face_center[0] - face_width,
            face_center[1] - face_height,
            face_center[0] + face_width,
            face_center[1] + face_height
        ]
        draw.ellipse(face_bbox, fill=skin_color)
        
        # Neck
        neck_width = 80
        neck_bbox = [
            face_center[0] - neck_width,
            face_center[1] + 150,
            face_center[0] + neck_width,
            size + 50
        ]
        draw.rectangle(neck_bbox, fill=skin_color)
        
        # Shoulders and blouse (light blue)
        blouse_color = '#87CEEB'
        shoulder_points = [
            (0, size),
            (0, size - 100),
            (100, size - 150),
            (face_center[0] - neck_width - 20, face_center[1] + 180),
            (face_center[0] + neck_width + 20, face_center[1] + 180),
            (size - 100, size - 150),
            (size, size - 100),
            (size, size),
        ]
        draw.polygon(shoulder_points, fill=blouse_color)
        
        # Hair (dark brown/black with texture)
        hair_color = '#1A0F0A'
        
        # Main hair shape
        hair_points = []
        for angle in range(0, 360, 5):
            rad = math.radians(angle)
            if 60 < angle < 120:  # Forehead
                radius = face_width + 30
            elif 240 < angle < 300:  # Back/bottom
                radius = face_width + 60
            else:
                radius = face_width + 50
            
            x = face_center[0] + radius * math.cos(rad)
            y = face_center[1] - 30 + radius * 0.9 * math.sin(rad)
            hair_points.append((x, y))
        
        draw.polygon(hair_points, fill=hair_color)
        
        # Forehead (expose some face)
        forehead_bbox = [
            face_center[0] - face_width + 40,
            face_center[1] - face_height + 60,
            face_center[0] + face_width - 40,
            face_center[1] - 50
        ]
        draw.ellipse(forehead_bbox, fill=skin_color)
        
        # Eyes
        eye_color = '#3D2314'  # Dark brown
        eye_white = '#FFFFFF'
        eye_y = face_center[1] - 30
        eye_spacing = 70
        eye_width = 35
        eye_height = 20
        
        for eye_x in [face_center[0] - eye_spacing, face_center[0] + eye_spacing]:
            # Eye white
            eye_bbox = [
                eye_x - eye_width,
                eye_y - eye_height,
                eye_x + eye_width,
                eye_y + eye_height
            ]
            draw.ellipse(eye_bbox, fill=eye_white)
            
            # Iris
            iris_size = 18
            draw.ellipse([
                eye_x - iris_size,
                eye_y - iris_size,
                eye_x + iris_size,
                eye_y + iris_size
            ], fill=eye_color)
            
            # Pupil
            pupil_size = 8
            draw.ellipse([
                eye_x - pupil_size,
                eye_y - pupil_size,
                eye_x + pupil_size,
                eye_y + pupil_size
            ], fill='#000000')
            
            # Eye highlight
            draw.ellipse([
                eye_x - 15,
                eye_y - 12,
                eye_x - 8,
                eye_y - 5
            ], fill='#FFFFFF')
        
        # Eyebrows
        eyebrow_color = '#1A0F0A'
        for brow_x in [face_center[0] - eye_spacing, face_center[0] + eye_spacing]:
            direction = 1 if brow_x < face_center[0] else -1
            brow_points = [
                (brow_x - 40 * direction, eye_y - 35),
                (brow_x + 30 * direction, eye_y - 45),
                (brow_x + 35 * direction, eye_y - 40),
                (brow_x - 35 * direction, eye_y - 30),
            ]
            draw.polygon(brow_points, fill=eyebrow_color)
        
        # Nose
        nose_color = '#7D4E35'  # Slightly darker
        nose_y = face_center[1] + 30
        nose_points = [
            (face_center[0], eye_y + 10),
            (face_center[0] - 25, nose_y + 30),
            (face_center[0], nose_y + 25),
            (face_center[0] + 25, nose_y + 30),
        ]
        draw.polygon(nose_points, fill=nose_color)
        
        # Nostrils
        draw.ellipse([face_center[0] - 20, nose_y + 20, face_center[0] - 8, nose_y + 32], fill='#5A3A28')
        draw.ellipse([face_center[0] + 8, nose_y + 20, face_center[0] + 20, nose_y + 32], fill='#5A3A28')
        
        # LIPS - Important for Wav2Lip!
        # Lips must be clearly defined and visible
        lip_color = '#9E4B4B'  # Natural lip color
        lip_highlight = '#B85C5C'
        lip_y = face_center[1] + 90
        lip_width = 50
        
        # Upper lip
        upper_lip_points = [
            (face_center[0] - lip_width, lip_y),
            (face_center[0] - lip_width // 2, lip_y - 8),
            (face_center[0] - 5, lip_y - 5),
            (face_center[0], lip_y - 10),  # Cupid's bow
            (face_center[0] + 5, lip_y - 5),
            (face_center[0] + lip_width // 2, lip_y - 8),
            (face_center[0] + lip_width, lip_y),
            (face_center[0], lip_y + 3),
        ]
        draw.polygon(upper_lip_points, fill=lip_color)
        
        # Lower lip (fuller)
        lower_lip_bbox = [
            face_center[0] - lip_width + 5,
            lip_y - 2,
            face_center[0] + lip_width - 5,
            lip_y + 25
        ]
        draw.ellipse(lower_lip_bbox, fill=lip_color)
        
        # Lip line
        draw.line([
            (face_center[0] - lip_width + 3, lip_y),
            (face_center[0] + lip_width - 3, lip_y)
        ], fill='#6D3030', width=2)
        
        # Lip highlight
        draw.ellipse([
            face_center[0] - 15,
            lip_y + 5,
            face_center[0] + 15,
            lip_y + 15
        ], fill=lip_highlight)
        
        # Slight smile lines
        draw.arc([face_center[0] - lip_width - 20, lip_y - 30, face_center[0] - lip_width + 10, lip_y + 20], 
                 start=300, end=60, fill='#7D4E35', width=2)
        draw.arc([face_center[0] + lip_width - 10, lip_y - 30, face_center[0] + lip_width + 20, lip_y + 20], 
                 start=120, end=240, fill='#7D4E35', width=2)
        
        # Cheek highlights
        cheek_color = '#A06850'
        for cheek_x in [face_center[0] - 100, face_center[0] + 100]:
            draw.ellipse([
                cheek_x - 30,
                face_center[1] + 20,
                cheek_x + 30,
                face_center[1] + 60
            ], fill=cheek_color)
        
        # Ears (partially visible)
        ear_color = skin_color
        for ear_x, direction in [(face_center[0] - face_width + 10, -1), (face_center[0] + face_width - 10, 1)]:
            ear_bbox = [
                ear_x - 25 * direction,
                face_center[1] - 20,
                ear_x + 15 * direction,
                face_center[1] + 60
            ]
            draw.ellipse(ear_bbox, fill=ear_color)
        
        # Apply subtle blur for softer appearance
        img = img.filter(ImageFilter.SMOOTH)
        
        # Save to bytes
        from io import BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG', quality=95)
        
        print("  ✅ Stylized avatar created successfully")
        return buffer.getvalue()
        
    except ImportError:
        print("  ❌ PIL not available")
        return None
    except Exception as e:
        print(f"  ❌ Error creating avatar: {e}")
        return None


def create_photorealistic_avatar_svg():
    """
    Create a high-quality photorealistic-style avatar using advanced drawing.
    """
    print("🎨 Creating photorealistic-style avatar...")
    
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
        import math
        import random
        
        # Create 512x512 image with gradient background
        size = 512
        img = Image.new('RGB', (size, size), '#D4C4B0')
        draw = ImageDraw.Draw(img)
        
        # Add subtle gradient to background
        for y in range(size):
            factor = 1 - (y / size) * 0.1
            color = tuple(int(c * factor) for c in (212, 196, 176))
            draw.line([(0, y), (size, y)], fill=color)
        
        # Redraw on gradient
        draw = ImageDraw.Draw(img)
        
        # Face center and dimensions
        cx, cy = size // 2, size // 2 + 10
        face_w, face_h = 160, 200
        
        # Base skin color (warm brown)
        skin_base = (139, 90, 60)
        skin_light = (165, 120, 90)
        skin_shadow = (100, 65, 45)
        
        # Draw neck first
        neck_points = [
            (cx - 60, cy + 160),
            (cx - 70, size + 20),
            (cx + 70, size + 20),
            (cx + 60, cy + 160),
        ]
        draw.polygon(neck_points, fill=skin_base)
        
        # Draw shoulders and clothing
        blouse_color = (135, 206, 235)  # Light blue
        collar_points = [
            (0, size),
            (0, size - 80),
            (80, size - 140),
            (cx - 80, cy + 200),
            (cx - 40, cy + 180),
            (cx, cy + 220),
            (cx + 40, cy + 180),
            (cx + 80, cy + 200),
            (size - 80, size - 140),
            (size, size - 80),
            (size, size),
        ]
        draw.polygon(collar_points, fill=blouse_color)
        
        # Face oval with multiple passes for depth
        for i in range(3):
            offset = i * 5
            shade = tuple(min(255, c + i * 8) for c in skin_base)
            draw.ellipse([
                cx - face_w + offset,
                cy - face_h + offset,
                cx + face_w - offset,
                cy + face_h - offset
            ], fill=shade)
        
        # Hair
        hair_color = (26, 15, 10)
        
        # Main hair mass
        for angle in range(-60, 240, 2):
            rad = math.radians(angle)
            base_radius = face_w + 45
            variance = random.randint(-5, 5)
            
            x1 = cx + (base_radius + variance) * math.cos(rad)
            y1 = cy - 40 + (base_radius * 0.85 + variance) * math.sin(rad)
            x2 = cx + (base_radius + 20 + variance) * math.cos(rad)
            y2 = cy - 40 + (base_radius * 0.85 + 20 + variance) * math.sin(rad)
            
            draw.line([(x1, y1), (x2, y2)], fill=hair_color, width=4)
        
        # Hair fill
        hair_ellipse = [cx - face_w - 35, cy - face_h - 50, cx + face_w + 35, cy + 60]
        draw.ellipse(hair_ellipse, fill=hair_color)
        
        # Expose forehead
        forehead_bbox = [cx - face_w + 30, cy - face_h + 50, cx + face_w - 30, cy - 40]
        draw.ellipse(forehead_bbox, fill=skin_base)
        
        # Eyes
        eye_y = cy - 25
        for eye_x, direction in [(cx - 55, -1), (cx + 55, 1)]:
            # Eye socket shadow
            draw.ellipse([eye_x - 32, eye_y - 18, eye_x + 32, eye_y + 18], fill=skin_shadow)
            
            # Eye white
            draw.ellipse([eye_x - 28, eye_y - 14, eye_x + 28, eye_y + 14], fill=(255, 252, 248))
            
            # Iris (dark brown)
            iris_x = eye_x + direction * 2
            draw.ellipse([iris_x - 14, eye_y - 14, iris_x + 14, eye_y + 14], fill=(61, 35, 20))
            
            # Pupil
            draw.ellipse([iris_x - 6, eye_y - 6, iris_x + 6, eye_y + 6], fill=(0, 0, 0))
            
            # Eye highlight
            draw.ellipse([iris_x - 10, eye_y - 10, iris_x - 4, eye_y - 4], fill=(255, 255, 255))
            
            # Upper eyelid
            draw.arc([eye_x - 30, eye_y - 20, eye_x + 30, eye_y + 10], start=180, end=0, fill=hair_color, width=3)
            
            # Lower lash line
            draw.arc([eye_x - 28, eye_y - 5, eye_x + 28, eye_y + 18], start=10, end=170, fill=skin_shadow, width=1)
        
        # Eyebrows
        for brow_x, direction in [(cx - 55, -1), (cx + 55, 1)]:
            points = [
                (brow_x - 35 * direction, eye_y - 32),
                (brow_x + 10 * direction, eye_y - 42),
                (brow_x + 30 * direction, eye_y - 38),
                (brow_x + 28 * direction, eye_y - 35),
                (brow_x + 5 * direction, eye_y - 38),
                (brow_x - 32 * direction, eye_y - 28),
            ]
            draw.polygon(points, fill=hair_color)
        
        # Nose
        nose_y = cy + 35
        
        # Nose bridge shadow
        draw.polygon([
            (cx - 8, eye_y + 15),
            (cx + 8, eye_y + 15),
            (cx + 15, nose_y),
            (cx - 15, nose_y),
        ], fill=skin_shadow)
        
        # Nose tip
        draw.ellipse([cx - 22, nose_y - 5, cx + 22, nose_y + 20], fill=skin_base)
        
        # Nostrils
        draw.ellipse([cx - 18, nose_y + 8, cx - 6, nose_y + 18], fill=(80, 50, 35))
        draw.ellipse([cx + 6, nose_y + 8, cx + 18, nose_y + 18], fill=(80, 50, 35))
        
        # LIPS - Critical for Wav2Lip
        lip_y = cy + 85
        lip_width = 45
        lip_color = (158, 75, 75)
        lip_dark = (110, 50, 50)
        lip_light = (184, 92, 92)
        
        # Upper lip shape
        upper_lip = [
            (cx - lip_width, lip_y),
            (cx - lip_width // 2, lip_y - 6),
            (cx - 8, lip_y - 3),
            (cx, lip_y - 8),  # Cupid's bow peak
            (cx + 8, lip_y - 3),
            (cx + lip_width // 2, lip_y - 6),
            (cx + lip_width, lip_y),
            (cx, lip_y + 2),
        ]
        draw.polygon(upper_lip, fill=lip_color)
        
        # Lower lip
        draw.ellipse([cx - lip_width + 8, lip_y - 3, cx + lip_width - 8, lip_y + 22], fill=lip_color)
        
        # Lip line
        draw.line([(cx - lip_width + 2, lip_y - 1), (cx + lip_width - 2, lip_y - 1)], fill=lip_dark, width=2)
        
        # Lower lip highlight
        draw.ellipse([cx - 18, lip_y + 4, cx + 18, lip_y + 14], fill=lip_light)
        
        # Cheeks
        for cheek_x in [cx - 80, cx + 80]:
            # Subtle blush
            cheek_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            cheek_draw = ImageDraw.Draw(cheek_layer)
            cheek_draw.ellipse([cheek_x - 35, cy + 20, cheek_x + 35, cy + 70], fill=(180, 100, 100, 30))
            img = Image.alpha_composite(img.convert('RGBA'), cheek_layer).convert('RGB')
            draw = ImageDraw.Draw(img)
        
        # Jaw contour
        draw.arc([cx - face_w + 20, cy, cx + face_w - 20, cy + face_h + 40], start=20, end=160, fill=skin_shadow, width=2)
        
        # Ears (partially visible)
        for ear_x, direction in [(cx - face_w + 15, -1), (cx + face_w - 15, 1)]:
            draw.ellipse([ear_x - 20, cy - 10, ear_x + 15, cy + 50], fill=skin_base)
        
        # Apply filters for realism
        img = img.filter(ImageFilter.SMOOTH_MORE)
        
        # Enhance
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(0.8)
        
        # Save
        from io import BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG', quality=95)
        
        print("  ✅ Photorealistic-style avatar created")
        return buffer.getvalue()
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_avatar(image_data: bytes, backend_path: Path, frontend_path: Path):
    """Save avatar to both backend and frontend locations."""
    try:
        # Save to backend
        with open(backend_path, 'wb') as f:
            f.write(image_data)
        print(f"  📁 Saved to: {backend_path}")
        
        # Save to frontend
        with open(frontend_path, 'wb') as f:
            f.write(image_data)
        print(f"  📁 Saved to: {frontend_path}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error saving: {e}")
        return False


def main():
    """Main function to create and save the avatar."""
    print("=" * 60)
    print("🎭 Rafiki Avatar Generator for Wav2Lip")
    print("=" * 60)
    print()
    
    backend_path = BACKEND_ASSETS / AVATAR_FILENAME
    frontend_path = FRONTEND_ASSETS / AVATAR_FILENAME
    
    # Try different methods in order
    image_data = None
    
    # Method 1: Try to download from stock photo
    image_data = download_avatar_from_url()
    
    # Method 2: Try Replicate API (if available)
    if not image_data:
        image_data = generate_with_replicate_api()
    
    # Method 3: Create photorealistic-style avatar
    if not image_data:
        image_data = create_photorealistic_avatar_svg()
    
    # Method 4: Fallback to stylized avatar
    if not image_data:
        image_data = create_stylized_avatar()
    
    if image_data:
        print()
        print("💾 Saving avatar...")
        if save_avatar(image_data, backend_path, frontend_path):
            print()
            print("✅ Avatar created successfully!")
            print(f"   Backend:  {backend_path}")
            print(f"   Frontend: {frontend_path}")
            print()
            print("🎬 The avatar is optimized for Wav2Lip lip-syncing with:")
            print("   - Clear, visible lips for accurate lip detection")
            print("   - Front-facing pose for best results")
            print("   - 512x512 resolution (recommended for Wav2Lip)")
            print("   - Good lighting and neutral expression")
            return 0
    
    print()
    print("❌ Failed to create avatar")
    return 1


if __name__ == "__main__":
    sys.exit(main())
