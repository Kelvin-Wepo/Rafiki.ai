#!/usr/bin/env python3
"""
Test ElevenLabs API Key validity
"""
import asyncio
import httpx
from ..config import get_settings

async def test_elevenlabs_api():
    settings = get_settings()
    api_key = settings.ELEVENLABS_API_KEY
    
    if not api_key:
        print("❌ No ElevenLabs API key configured")
        return False
    
    print(f"🔑 Testing API key: {api_key[:20]}...")
    
    # Test API key with a simple request
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.elevenlabs.io/v1/user",
                headers={"xi-api-key": api_key},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Key is valid!")
                print(f"   Subscription: {data.get('subscription', {}).get('tier', 'unknown')}")
                print(f"   Character count: {data.get('subscription', {}).get('character_count', 0)}")
                print(f"   Character limit: {data.get('subscription', {}).get('character_limit', 0)}")
                return True
            elif response.status_code == 401:
                print(f"❌ API Key is invalid or expired")
                print(f"   Response: {response.text}")
                return False
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing API key: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(test_elevenlabs_api())
