#!/usr/bin/env python3
"""
Test script for TrueNAS MCP Server Phase 2 features
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

async def test_phase2_features():
    # Load environment variables
    load_dotenv()
    
    base_url = os.getenv("TRUENAS_URL")
    api_key = os.getenv("TRUENAS_API_KEY")
    verify_ssl = os.getenv("TRUENAS_VERIFY_SSL", "true").lower() == "true"
    
    if not base_url or not api_key:
        print("❌ Error: Please configure TRUENAS_URL and TRUENAS_API_KEY in .env file")
        return
    
    print(f"🔍 Testing Phase 2 features on: {base_url}")
    
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
        
        # Test dataset properties endpoint
        print("\n📊 Testing dataset properties...")
        try:
            response = await client.get("/pool/dataset")
            response.raise_for_status()
            datasets = response.json()
            
            if datasets:
                print(f"✅ Found {len(datasets)} datasets")
                # Show first dataset's properties as example
                first_dataset = datasets[0]
                print(f"\n📁 Example dataset: {first_dataset.get('name')}")
                print(f"   Compression: {first_dataset.get('compression', {}).get('value', 'N/A')}")
                print(f"   Used: {first_dataset.get('used', {}).get('value', 'N/A')}")
                print(f"   Available: {first_dataset.get('available', {}).get('value', 'N/A')}")
            else:
                print("⚠️  No datasets found")
        except Exception as e:
            print(f"❌ Failed to test dataset properties: {e}")
        
        # Test filesystem permissions endpoint
        print("\n🔐 Testing filesystem permissions...")
        try:
            # Test with a known path
            test_path = "/mnt"
            response = await client.post("/filesystem/stat", json={"path": test_path})
            if response.status_code == 200:
                stat_info = response.json()
                print(f"✅ Filesystem stat endpoint working")
                print(f"   Path: {test_path}")
                print(f"   Mode: {stat_info.get('mode', 'N/A')}")
                print(f"   User: {stat_info.get('user', 'N/A')}")
                print(f"   Group: {stat_info.get('group', 'N/A')}")
            else:
                print("⚠️  Filesystem stat endpoint returned non-200 status")
        except Exception as e:
            print(f"❌ Failed to test filesystem permissions: {e}")
        
        # Test NFS sharing endpoint
        print("\n🌐 Testing NFS sharing...")
        try:
            response = await client.get("/sharing/nfs")
            response.raise_for_status()
            nfs_shares = response.json()
            print(f"✅ Found {len(nfs_shares)} NFS shares")
            
            if nfs_shares:
                print("\n📋 NFS shares:")
                for share in nfs_shares[:3]:  # Show first 3
                    print(f"   - Path: {share.get('path')}")
                    print(f"     Networks: {share.get('networks', [])}")
        except Exception as e:
            print(f"❌ Failed to test NFS sharing: {e}")
        
        # Test iSCSI endpoints
        print("\n💾 Testing iSCSI configuration...")
        try:
            # Test targets
            response = await client.get("/iscsi/target")
            response.raise_for_status()
            targets = response.json()
            print(f"✅ Found {len(targets)} iSCSI targets")
            
            # Test extents
            response = await client.get("/iscsi/extent")
            response.raise_for_status()
            extents = response.json()
            print(f"✅ Found {len(extents)} iSCSI extents")
            
            # Test portals
            response = await client.get("/iscsi/portal")
            response.raise_for_status()
            portals = response.json()
            print(f"✅ Found {len(portals)} iSCSI portals")
        except Exception as e:
            print(f"❌ Failed to test iSCSI: {e}")
        
        # Test snapshot tasks endpoint
        print("\n📸 Testing snapshot automation...")
        try:
            response = await client.get("/pool/snapshottask")
            response.raise_for_status()
            tasks = response.json()
            print(f"✅ Found {len(tasks)} snapshot tasks")
            
            if tasks:
                print("\n📋 Snapshot tasks:")
                for task in tasks[:3]:  # Show first 3
                    print(f"   - Dataset: {task.get('dataset')}")
                    print(f"     Schedule: {task.get('schedule', {})}")
                    print(f"     Enabled: {task.get('enabled', False)}")
        except Exception as e:
            print(f"❌ Failed to test snapshot tasks: {e}")
        
        print("\n✨ Phase 2 feature test complete!")

def print_phase2_capabilities():
    """Print Phase 2 capabilities summary"""
    print("\n🚀 Phase 2 Capabilities Summary")
    print("=" * 50)
    print("\n📦 New Features Available:")
    print("\n1️⃣  Permission Management:")
    print("   • Modify dataset permissions (chmod/chown)")
    print("   • Update ACLs for fine-grained control")
    print("   • View current permissions and ACL info")
    
    print("\n2️⃣  Dataset Properties:")
    print("   • Modify ZFS properties (compression, quota, etc.)")
    print("   • Get comprehensive property information")
    
    print("\n3️⃣  Kubernetes Integration:")
    print("   • Create NFS exports for persistent volumes")
    print("   • Create iSCSI targets for block storage")
    print("   • Generate K8s YAML manifests automatically")
    
    print("\n4️⃣  Automation:")
    print("   • Create snapshot policies with schedules")
    print("   • Configure retention settings")
    print("   • Recursive operations support")
    
    print("\n💡 Example Commands:")
    print('   • "Change permissions on tank/data to 755"')
    print('   • "Enable zstd compression on tank/backups"')
    print('   • "Create NFS export for Kubernetes on tank/k8s"')
    print('   • "Set up daily snapshots with 30-day retention"')

if __name__ == "__main__":
    print("🧪 TrueNAS Core MCP Server - Phase 2 Feature Test")
    print("=" * 50)
    asyncio.run(test_phase2_features())
    print_phase2_capabilities()
