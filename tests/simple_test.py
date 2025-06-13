#!/usr/bin/env python3
"""
Simple test script to verify TrueNAS MCP Server is working
No external test dependencies required
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path to import truenas_mcp_server
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import truenas_mcp_server
    print("✅ Successfully imported truenas_mcp_server module")
except ImportError as e:
    print(f"❌ Failed to import truenas_mcp_server: {e}")
    sys.exit(1)

# Check environment variables
print("\n🔍 Checking environment variables...")
truenas_url = os.getenv("TRUENAS_URL")
truenas_api_key = os.getenv("TRUENAS_API_KEY")
truenas_verify_ssl = os.getenv("TRUENAS_VERIFY_SSL", "true")

if not truenas_url:
    print("❌ TRUENAS_URL not set")
    print("   Please set it in your .env file or environment")
else:
    print(f"✅ TRUENAS_URL: {truenas_url}")

if not truenas_api_key:
    print("❌ TRUENAS_API_KEY not set")
    print("   Please set it in your .env file or environment")
else:
    print(f"✅ TRUENAS_API_KEY: {truenas_api_key[:10]}...")

print(f"✅ TRUENAS_VERIFY_SSL: {truenas_verify_ssl}")

# Test basic function availability
print("\n🔍 Checking available functions...")
functions = [
    "list_users",
    "get_system_info",
    "list_pools",
    "list_datasets",
    "create_dataset",
    "modify_dataset_permissions",
    "create_nfs_export",
]

for func_name in functions:
    if hasattr(truenas_mcp_server, func_name):
        print(f"✅ Function available: {func_name}")
    else:
        print(f"❌ Function missing: {func_name}")

# Try debug connection if environment is set
if truenas_url and truenas_api_key:
    print("\n🔌 Testing debug connection...")
    
    async def test_debug():
        try:
            result = await truenas_mcp_server.debug_connection()
            print("✅ Debug connection successful")
            print(f"   Environment: {result.get('environment', {})}")
            print(f"   Client status: {result.get('client_status', 'unknown')}")
        except Exception as e:
            print(f"❌ Debug connection failed: {e}")
    
    asyncio.run(test_debug())
else:
    print("\n⚠️  Skipping connection test - environment variables not set")

print("\n✅ Basic functionality check complete!")
print("\nTo test actual TrueNAS connection, run:")
print("   python tests/test_connection.py")
