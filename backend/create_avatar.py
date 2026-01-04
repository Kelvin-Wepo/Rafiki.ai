#!/usr/bin/env python3
from PIL import Image, ImageDraw
import os

# Create avatar directory
avatar_dir = "assets/avatars"
os.makedirs(avatar_dir, exist_ok=True)

# Create a beautiful gradient avatar for Rafiki
img = Image.new('RGB', (512, 512), color='#f5f5f5')
draw = ImageDraw.Draw(img)

# Draw gradient background (light blue to cream)
for y in range(512):
    r = int(245 - (25 * y / 512))
    g = int(245 - (45 * y / 512))
    b = int(245 - (65 * y / 512))
    draw.line([(0, y), (512, y)], fill=(r, g, b))

# Draw face circle (warm brown skin tone for Kenyan woman)
circle_center = 256
circle_radius = 180

draw.ellipse(
    [(circle_center - circle_radius, circle_center - circle_radius - 30),
     (circle_center + circle_radius, circle_center + circle_radius - 30)],
    fill='#C9825F'  # Warm brown Kenyan skin tone
)

# Draw eyes
eye_y = 180
left_eye_x, right_eye_x = 200, 312
eye_radius = 18

# Eyes (whites)
draw.ellipse([(left_eye_x - eye_radius, eye_y - eye_radius),
              (left_eye_x + eye_radius, eye_y + eye_radius)],
             fill='white')
draw.ellipse([(right_eye_x - eye_radius, eye_y - eye_radius),
              (right_eye_x + eye_radius, eye_y + eye_radius)],
             fill='white')

# Pupils
pupil_radius = 10
draw.ellipse([(left_eye_x - pupil_radius, eye_y - pupil_radius),
              (left_eye_x + pupil_radius, eye_y + pupil_radius)],
             fill='#2c2c2c')
draw.ellipse([(right_eye_x - pupil_radius, eye_y - pupil_radius),
              (right_eye_x + pupil_radius, eye_y + pupil_radius)],
             fill='#2c2c2c')

# Eyebrows
draw.line([(left_eye_x - 25, eye_y - 40), (left_eye_x + 25, eye_y - 42)], fill='#3d3d3d', width=4)
draw.line([(right_eye_x - 25, eye_y - 40), (right_eye_x + 25, eye_y - 42)], fill='#3d3d3d', width=4)

# Mouth (warm smile)
mouth_y = 340
mouth_width = 70
draw.arc([(circle_center - mouth_width, mouth_y - 20),
          (circle_center + mouth_width, mouth_y + 40)],
         0, 180, fill='#A0574A', width=5)

# Save avatar
avatar_path = os.path.join(avatar_dir, "rafiki_avatar.png")
img.save(avatar_path, 'PNG')
print(f"✅ Avatar created: {avatar_path}")
