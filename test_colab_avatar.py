#!/usr/bin/env python3
"""
Test Colab GPU Avatar Generation
"""
import requests
import time

# Test endpoint
url = "http://localhost:8000/api/avatar/text-to-video"

# Test payload - simple text to video generation (Form data)
payload = {
    "text": "Hello! This is a test of the Colab GPU acceleration.",
    "avatar_id": "rafiki_avatar",
    "language": "en",
    "use_elevenlabs": "true",
    "personality": "friendly"
}

print("🚀 Testing Colab GPU Avatar Generation...")
print(f"📡 Colab URL: https://7c0e8200f810.ngrok-free.app")
print(f"🎯 Endpoint: {url}")
print(f"📝 Text: {payload['text']}")
print("\n⏳ Sending request...\n")

start_time = time.time()

try:
    response = requests.post(url, data=payload, timeout=120)
    
    elapsed = time.time() - start_time
    
    print(f"✅ Response Status: {response.status_code}")
    print(f"⏱️  Time taken: {elapsed:.2f}s")
    print(f"📦 Content-Type: {response.headers.get('content-type', 'unknown')}")
    
    if response.status_code == 200:
        content_type = response.headers.get('content-type', '')
        
        if 'video' in content_type or 'audio' in content_type:
            # Binary response (video/audio file)
            size_mb = len(response.content) / (1024 * 1024)
            print(f"📁 File size: {size_mb:.2f} MB")
            print(f"🎬 Successfully generated {'video' if 'video' in content_type else 'audio'}!")
            print(f"✨ Colab GPU is working!")
        else:
            print(f"\n📄 Response text:")
            print(response.text[:500])
    else:
        print(f"\n❌ Error response:")
        print(response.text[:500])
    
except requests.exceptions.Timeout:
    print("⏰ Request timed out after 120 seconds")
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to backend. Is it running?")
except Exception as e:
    print(f"❌ Error: {e}")
