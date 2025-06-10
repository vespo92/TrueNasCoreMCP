#!/usr/bin/env python3
"""
Example usage of TrueNAS Core MCP Server functions
This shows how to use the server programmatically
"""

import asyncio
from truenas_mcp_server import (
    list_users,
    get_user,
    get_system_info,
    list_pools,
    list_datasets,
    list_smb_shares
)

async def main():
    print("TrueNAS Core MCP Server - Example Usage")
    print("=" * 50)
    
    # Get system information
    print("\n1. Getting system information...")
    result = await get_system_info()
    if result["success"]:
        info = result["info"]
        print(f"   Hostname: {info.get('hostname')}")
        print(f"   Version: {info.get('version')}")
        print(f"   Uptime: {info.get('uptime')}")
    else:
        print(f"   Error: {result['error']}")
    
    # List users
    print("\n2. Listing users...")
    result = await list_users()
    if result["success"]:
        users = result["users"]
        custom_users = [u for u in users if not u["builtin"]]
        print(f"   Total users: {result['count']}")
        print(f"   Custom users: {len(custom_users)}")
        for user in custom_users[:3]:  # Show first 3 custom users
            print(f"   - {user['username']} ({user.get('full_name', 'No name')})")
    else:
        print(f"   Error: {result['error']}")
    
    # List pools
    print("\n3. Listing storage pools...")
    result = await list_pools()
    if result["success"]:
        pools = result["pools"]
        print(f"   Found {len(pools)} pools:")
        for pool in pools:
            print(f"   - {pool.get('name')} ({pool.get('status')})")
    else:
        print(f"   Error: {result['error']}")
    
    # List datasets
    print("\n4. Listing datasets...")
    result = await list_datasets()
    if result["success"]:
        datasets = result["datasets"]
        print(f"   Found {len(datasets)} datasets")
        # Show first 5 datasets
        for dataset in datasets[:5]:
            print(f"   - {dataset.get('name')}")
        if len(datasets) > 5:
            print(f"   ... and {len(datasets) - 5} more")
    else:
        print(f"   Error: {result['error']}")
    
    # List SMB shares
    print("\n5. Listing SMB shares...")
    result = await list_smb_shares()
    if result["success"]:
        shares = result["shares"]
        print(f"   Found {len(shares)} SMB shares:")
        for share in shares:
            print(f"   - {share.get('name')} -> {share.get('path')}")
    else:
        print(f"   Error: {result['error']}")

if __name__ == "__main__":
    # Note: Make sure .env is configured before running
    asyncio.run(main())
