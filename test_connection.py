#!/usr/bin/env python3
"""
Test script to verify TrueNAS API connection
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

async def test_connection():
    # Load environment variables
    load_dotenv()
    
    base_url = os.getenv("TRUENAS_URL")
    api_key = os.getenv("TRUENAS_API_KEY")
    verify_ssl = os.getenv("TRUENAS_VERIFY_SSL", "true").lower() == "true"
    
    if not base_url or not api_key:
        print("❌ Error: Please configure TRUENAS_URL and TRUENAS_API_KEY in .env file")
        return
    
    print(f"🔍 Testing connection to: {base_url}")
    print(f"🔐 SSL Verification: {verify_ssl}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(
        base_url=f"{base_url}/api/v2.0",
        headers=headers,
        verify=verify_ssl,
        timeout=30.0
    ) as client:
        try:
            # Test system info endpoint
            print("\n📊 Testing system info endpoint...")
            response = await client.get("/system/info")
            response.raise_for_status()
            
            info = response.json()
            print(f"✅ Connected to: {info.get('hostname', 'Unknown')}")
            print(f"✅ Version: {info.get('version', 'Unknown')}")
            
            # Test user endpoint
            print("\n👥 Testing user endpoint...")
            response = await client.get("/user")
            response.raise_for_status()
            
            users = response.json()
            user_count = len(users)
            custom_users = [u for u in users if not u.get('builtin', True)]
            
            print(f"✅ Found {user_count} total users")
            print(f"✅ Found {len(custom_users)} custom users")
            
            if custom_users:
                print("\n📋 Custom users:")
                for user in custom_users:
                    print(f"   - {user.get('username')} ({user.get('full_name', 'No name')})")
            
            print("\n✨ Connection test successful!")
            
        except httpx.HTTPError as e:
            print(f"\n❌ Connection failed: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Status: {e.response.status_code}")
                print(f"   Details: {e.response.text}")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🚀 TrueNAS Core MCP Server - Connection Test")
    print("=" * 50)
    asyncio.run(test_connection())
