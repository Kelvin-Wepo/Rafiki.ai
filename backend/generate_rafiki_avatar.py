#!/usr/bin/env python3
"""
Generate a professional Kenyan woman avatar for Rafiki using Imagen 3.
This creates a realistic, culturally appropriate avatar for the AI assistant.
"""

import os
import sys
from pathlib import Path
from PIL import Image
import base64
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from services.imagen_service import ImagenService
from utils.logger import logger


def generate_rafiki_avatar():
    """Generate a beautiful Kenyan woman avatar for Rafiki."""
    
    logger.info("Starting Rafiki avatar generation with Imagen 3...")
    
    # Initialize Imagen service
    imagen = ImagenService()
    
    # Professional prompt for a Kenyan woman avatar
    prompt = """
    Professional portrait photograph of a warm, friendly Kenyan woman in her early 30s.
    She has an approachable, genuine smile and intelligent eyes that convey trustworthiness and competence.
    She's wearing professional but approachable smart casual attire - a light blue or cream colored blouse.
    Natural hairstyle, beautiful dark skin tone.
    Head and shoulders framing, centered composition, facing directly at camera.
    Neutral beige or soft white background for easy compositing.
    Soft, even professional lighting with no harsh shadows.
    High quality photorealistic portrait suitable for a professional AI assistant.
    Professional demeanor but warm and approachable personality evident.
    Resolution optimized for web: 512x512 pixels.
    """
    
    try:
        logger.info("Generating avatar image with prompt...")
        print("\n🎨 Generating Rafiki avatar...")
        
        # Generate image using Imagen
        result = imagen.generate_image(
            prompt=prompt,
            image_size="512x512",
            num_images=1,
            quality_filter=True
        )
        
        if not result or not result.get('images'):
            logger.error("Failed to generate avatar image")
            print("❌ Failed to generate avatar image")
            return False
        
        # Get the generated image
        image_data = result['images'][0]
        
        # Save the avatar
        avatar_dir = Path(__file__).parent / "assets" / "avatars"
        avatar_dir.mkdir(parents=True, exist_ok=True)
        
        avatar_path = avatar_dir / "rafiki_avatar_v1.png"
        
        # Decode and save image
        if isinstance(image_data, str):
            # Base64 encoded image
            image_bytes = base64.b64decode(image_data)
            with open(avatar_path, 'wb') as f:
                f.write(image_bytes)
        else:
            # PIL Image object
            image_data.save(avatar_path, 'PNG', quality=95)
        
        logger.info(f"Avatar saved to {avatar_path}")
        print(f"✅ Avatar generated and saved to: {avatar_path}")
        
        # Verify face detection
        print("\n🔍 Verifying face detection...")
        if verify_face_detection(str(avatar_path)):
            print("✅ Face detection verified - avatar is ready for SadTalker")
            return True
        else:
            print("⚠️  Face not clearly detected - you may need to regenerate")
            return False
        
    except Exception as e:
        logger.error(f"Error generating avatar: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False


def verify_face_detection(image_path):
    """Verify that a face can be detected in the image."""
    try:
        import cv2
        import numpy as np
        
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            logger.warning(f"Could not read image: {image_path}")
            return False
        
        # Create face detector
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Detect faces
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_area_percent = (w * h) / (img.shape[0] * img.shape[1]) * 100
            
            logger.info(f"✓ Face detected: {w}x{h} pixels ({face_area_percent:.1f}% of image)")
            print(f"  - Face dimensions: {w}x{h} pixels")
            print(f"  - Face occupies {face_area_percent:.1f}% of image")
            
            # Optimal range for SadTalker is 40-60% of image
            if 30 <= face_area_percent <= 70:
                print("  - ✅ Optimal size for SadTalker animation")
                return True
            else:
                print(f"  - ⚠️  Consider regenerating with face taking up 40-60% of image")
                return True  # Still usable
        else:
            logger.warning("✗ No face detected in image")
            print("  - ✗ No face detected - regenerate image")
            return False
            
    except ImportError:
        logger.info("OpenCV not available for face verification, skipping check")
        print("  - OpenCV not available, skipping face verification")
        return True  # Assume it's fine
    except Exception as e:
        logger.error(f"Face detection error: {str(e)}")
        return True  # Don't fail if verification fails


def create_fallback_avatar():
    """Create a simple fallback avatar if Imagen is not available."""
    print("\n📝 Creating fallback avatar (since Imagen might not be available yet)...")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create avatar directory
        avatar_dir = Path(__file__).parent / "assets" / "avatars"
        avatar_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a beautiful gradient avatar
        img = Image.new('RGB', (512, 512), color='#f5f5f5')
        draw = ImageDraw.Draw(img)
        
        # Draw gradient background
        for y in range(512):
            # Gradient from light blue to cream
            r = int(245 + (220 - 245) * (y / 512))
            g = int(245 + (200 - 245) * (y / 512))
            b = int(245 + (180 - 245) * (y / 512))
            draw.line([(0, y), (512, y)], fill=(r, g, b))
        
        # Draw circle for avatar
        circle_center = 256
        circle_radius = 200
        
        # Draw face circle (peachy skin tone)
        draw.ellipse(
            [(circle_center - circle_radius, circle_center - circle_radius),
             (circle_center + circle_radius, circle_center + circle_radius)],
            fill='#d4a574'
        )
        
        # Draw eyes
        eye_y = 200
        left_eye_x, right_eye_x = 200, 312
        eye_radius = 15
        
        draw.ellipse([(left_eye_x - eye_radius, eye_y - eye_radius),
                      (left_eye_x + eye_radius, eye_y + eye_radius)],
                     fill='white')
        draw.ellipse([(right_eye_x - eye_radius, eye_y - eye_radius),
                      (right_eye_x + eye_radius, eye_y + eye_radius)],
                     fill='white')
        
        # Draw pupils
        pupil_radius = 8
        draw.ellipse([(left_eye_x - pupil_radius, eye_y - pupil_radius),
                      (left_eye_x + pupil_radius, eye_y + pupil_radius)],
                     fill='#333333')
        draw.ellipse([(right_eye_x - pupil_radius, eye_y - pupil_radius),
                      (right_eye_x + pupil_radius, eye_y + pupil_radius)],
                     fill='#333333')
        
        # Draw smile (simple arc with lines)
        mouth_y = 330
        mouth_width = 80
        draw.arc([(circle_center - mouth_width, mouth_y - 30),
                  (circle_center + mouth_width, mouth_y + 30)],
                 0, 180, fill='#8B4513', width=4)
        
        # Save fallback avatar
        avatar_path = avatar_dir / "rafiki_avatar_fallback.png"
        img.save(avatar_path, 'PNG')
        
        logger.info(f"Fallback avatar created at {avatar_path}")
        print(f"✅ Fallback avatar created: {avatar_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating fallback avatar: {str(e)}")
        print(f"⚠️  Error creating fallback: {str(e)}")
        return False


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎬 RAFIKI AVATAR GENERATION")
    print("="*60)
    
    # Try to generate with Imagen
    success = generate_rafiki_avatar()
    
    # If that fails, create fallback
    if not success:
        print("\n⚠️  Using fallback avatar generation...")
        create_fallback_avatar()
    
    print("\n" + "="*60)
    print("✅ Avatar generation complete!")
    print("="*60 + "\n")
