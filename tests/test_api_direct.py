#!/usr/bin/env python3
"""Quick TrueNAS API Key Test"""

import httpx
import asyncio
import os
from pathlib import Path

async def test_direct():
    # Read .env file directly
    env_path = Path(__file__).parent / ".env"
    env_vars = {}
    
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    
    url = env_vars.get('TRUENAS_URL', '').strip()
    api_key = env_vars.get('TRUENAS_API_KEY', '').strip()
    
    print(f"🔍 Testing TrueNAS API directly")
    print(f"URL: {url}")
    print(f"API Key: {api_key[:10]}...{api_key[-10:]}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(f"{url}/api/v2.0/system/info", headers=headers)
            print(f"\nStatus Code: {response.status_code}")
            
            if response.status_code == 200:
                info = response.json()
                print(f"✅ SUCCESS! Connected to: {info.get('hostname')}")
                print(f"Version: {info.get('version')}")
            else:
                print(f"❌ Failed: {response.text[:200]}")
                
                # Try without Bearer prefix
                headers["Authorization"] = api_key
                response2 = await client.get(f"{url}/api/v2.0/system/info", headers=headers)
                if response2.status_code == 200:
                    print("\n✅ Works without 'Bearer' prefix!")
                else:
                    print("\n❌ Also failed without Bearer prefix")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_direct())
