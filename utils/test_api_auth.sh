#!/bin/bash

echo "🔍 TrueNAS API Direct Test"
echo "========================="
echo

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "   Run: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

# Run the Python test
python3 << 'EOF'
import httpx
import asyncio
import os
from pathlib import Path

async def test_direct():
    # Read .env file directly
    env_path = Path.cwd() / ".env"
    env_vars = {}
    
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                # Remove any comments
                if '#' in value:
                    value = value.split('#')[0].strip()
                env_vars[key] = value
    
    url = env_vars.get('TRUENAS_URL', '').strip()
    api_key = env_vars.get('TRUENAS_API_KEY', '').strip()
    
    print(f"\n🔑 Testing TrueNAS API directly")
    print(f"URL: {url}")
    print(f"API Key: {api_key[:10]}...{api_key[-10:]}")
    print(f"Key Length: {len(api_key)} characters")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"\n🌐 Attempting connection...")
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            response = await client.get(f"{url}/api/v2.0/system/info", headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                info = response.json()
                print(f"\n✅ SUCCESS! Connected to TrueNAS")
                print(f"Hostname: {info.get('hostname')}")
                print(f"Version: {info.get('version')}")
                print(f"Uptime: {info.get('uptime_seconds', 0) // 3600} hours")
                
                # Test pool endpoint too
                print(f"\n🏊 Testing pool endpoint...")
                pool_response = await client.get(f"{url}/api/v2.0/pool", headers=headers)
                if pool_response.status_code == 200:
                    pools = pool_response.json()
                    print(f"✅ Found {len(pools)} pool(s)")
                    for pool in pools:
                        print(f"   - {pool.get('name')}: {pool.get('status')}")
                
            elif response.status_code == 401:
                print(f"\n❌ Authentication Failed (401)")
                print(f"Response: {response.text[:200]}")
                
                # Check if it's a token format issue
                if "Invalid API key" in response.text:
                    print("\n⚠️  API key is not recognized by TrueNAS")
                    print("   Please verify the key in TrueNAS Web UI:")
                    print("   Settings → API Keys")
                    
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                    
    except httpx.ConnectError:
        print(f"\n❌ Connection Error: Cannot reach {url}")
        print("   - Check if TrueNAS is accessible")
        print("   - Verify the URL is correct")
        print("   - Check firewall settings")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")

asyncio.run(test_direct())
EOF

echo
echo "🏁 Test complete!"
