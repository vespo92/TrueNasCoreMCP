"""
TrueNAS MCP Server - Phase 2 Examples
Advanced usage examples for Phase 2 features
"""

import asyncio
from truenas_mcp_server import (
    modify_dataset_permissions,
    update_dataset_acl,
    get_dataset_permissions,
    modify_dataset_properties,
    get_dataset_properties,
    create_nfs_export,
    create_iscsi_target,
    create_snapshot_policy
)

async def permission_examples():
    """Examples of permission management"""
    
    print("=== Permission Management Examples ===\n")
    
    # Example 1: Change dataset permissions
    print("1. Changing permissions on a dataset:")
    result = await modify_dataset_permissions(
        dataset="tank/shared",
        mode="775",
        owner="vinnie",
        group="developers",
        recursive=True
    )
    print(f"Result: {result}\n")
    
    # Example 2: Set up ACLs for fine-grained control
    print("2. Setting up ACLs:")
    acl_entries = [
        {
            "tag": "group",
            "id": "developers",
            "type": "ALLOW",
            "perms": {"READ": True, "WRITE": True, "EXECUTE": True},
            "flags": {"INHERIT": True}
        },
        {
            "tag": "group", 
            "id": "guests",
            "type": "ALLOW",
            "perms": {"READ": True, "WRITE": False, "EXECUTE": True},
            "flags": {"INHERIT": True}
        }
    ]
    result = await update_dataset_acl(
        dataset="tank/projects",
        acl_entries=acl_entries,
        recursive=True
    )
    print(f"Result: {result}\n")
    
    # Example 3: Check current permissions
    print("3. Checking current permissions:")
    result = await get_dataset_permissions("tank/shared")
    print(f"Permissions: {result}\n")

async def property_examples():
    """Examples of dataset property management"""
    
    print("=== Dataset Property Examples ===\n")
    
    # Example 1: Enable compression and set quota
    print("1. Updating dataset properties:")
    result = await modify_dataset_properties(
        dataset="tank/backups",
        properties={
            "compression": "zstd",
            "dedup": "off",
            "quota": "500G",
            "recordsize": "128K"
        }
    )
    print(f"Result: {result}\n")
    
    # Example 2: Get all properties
    print("2. Getting dataset properties:")
    result = await get_dataset_properties("tank/backups")
    print(f"Properties: {result['properties']}\n")

async def kubernetes_storage_examples():
    """Examples for Kubernetes storage integration"""
    
    print("=== Kubernetes Storage Examples ===\n")
    
    # Example 1: Create NFS export for Kubernetes
    print("1. Creating NFS export for K8s persistent volumes:")
    result = await create_nfs_export(
        dataset="tank/k8s-nfs",
        allowed_networks=["10.0.0.0/24", "192.168.1.0/24"],
        read_only=False,
        maproot_user="root",
        maproot_group="wheel"
    )
    print(f"NFS Export created: {result['message']}")
    print(f"StorageClass YAML: {result['k8s_example']['storage_class']}\n")
    
    # Example 2: Create iSCSI target for block storage
    print("2. Creating iSCSI target for K8s block storage:")
    result = await create_iscsi_target(
        name="postgres-data",
        dataset="tank/iscsi",
        size="100G"
    )
    print(f"iSCSI Target created: {result['message']}")
    print(f"PersistentVolume YAML: {result['k8s_example']['pv_example']}\n")

async def automation_examples():
    """Examples of automation features"""
    
    print("=== Automation Examples ===\n")
    
    # Example 1: Daily snapshot policy with monthly retention
    print("1. Creating daily snapshot policy:")
    result = await create_snapshot_policy(
        dataset="tank/important",
        name="daily-backup",
        schedule={
            "minute": "0",
            "hour": "2",
            "dom": "*",
            "month": "*",
            "dow": "*"
        },
        retention={"daily": 30},
        recursive=True
    )
    print(f"Policy created: {result}\n")
    
    # Example 2: Hourly snapshots for databases
    print("2. Creating hourly snapshot policy for databases:")
    result = await create_snapshot_policy(
        dataset="tank/databases",
        name="hourly-snap",
        schedule={
            "minute": "0",
            "hour": "*",
            "dom": "*",
            "month": "*",
            "dow": "*"
        },
        retention={"hourly": 24},
        recursive=False
    )
    print(f"Policy created: {result}\n")

async def advanced_scenarios():
    """Advanced real-world scenarios"""
    
    print("=== Advanced Scenarios ===\n")
    
    # Scenario 1: Set up a development environment dataset
    print("Scenario 1: Development Environment Setup")
    
    # Create dataset
    print("- Creating development dataset...")
    # (Assuming dataset already exists)
    
    # Set properties
    await modify_dataset_properties(
        dataset="tank/development",
        properties={
            "compression": "lz4",
            "atime": "off",
            "quota": "200G"
        }
    )
    
    # Set permissions
    await modify_dataset_permissions(
        dataset="tank/development",
        mode="770",
        owner="devlead",
        group="developers",
        recursive=True
    )
    
    # Create NFS export
    await create_nfs_export(
        dataset="tank/development",
        allowed_networks=["10.10.0.0/24"],
        read_only=False
    )
    
    # Set up snapshots
    await create_snapshot_policy(
        dataset="tank/development",
        name="dev-snapshots",
        schedule={
            "minute": "0",
            "hour": "*/4",
            "dom": "*",
            "month": "*",
            "dow": "*"
        },
        retention={"hourly": 24, "daily": 7},
        recursive=True
    )
    
    print("Development environment setup complete!\n")

# Kubernetes PVC Example YAML
def print_kubernetes_examples():
    """Print example Kubernetes manifests"""
    
    print("\n=== Kubernetes Manifest Examples ===\n")
    
    print("Example PersistentVolumeClaim for NFS:")
    print("""
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-pvc
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: truenas-nfs-tank-k8s-nfs
  resources:
    requests:
      storage: 10Gi
""")
    
    print("\nExample PersistentVolumeClaim for iSCSI:")
    print("""
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: iscsi-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: truenas-iscsi-postgres-data
  resources:
    requests:
      storage: 50Gi
""")

if __name__ == "__main__":
    # Run all examples
    asyncio.run(permission_examples())
    asyncio.run(property_examples())
    asyncio.run(kubernetes_storage_examples())
    asyncio.run(automation_examples())
    asyncio.run(advanced_scenarios())
    print_kubernetes_examples()
