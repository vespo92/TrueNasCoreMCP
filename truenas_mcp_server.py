#!/usr/bin/env python3
"""
TrueNAS Core MCP Server
A Model Context Protocol server for interacting with TrueNAS Core systems
"""

import os
import httpx
from typing import Dict, List, Any, Optional, Union
from mcp.server.fastmcp import FastMCP
import asyncio

# Initialize the MCP server
mcp = FastMCP("TrueNAS Core MCP Server")

# Global client instance
client = None

def get_client():
    """Get or create the HTTP client"""
    global client
    if client is None:
        base_url = os.getenv("TRUENAS_URL", "https://truenas.local")
        api_key = os.getenv("TRUENAS_API_KEY", "")
        verify_ssl = os.getenv("TRUENAS_VERIFY_SSL", "true").lower() == "true"
        
        if not api_key:
            raise ValueError("TRUENAS_API_KEY environment variable is required")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        client = httpx.AsyncClient(
            base_url=f"{base_url}/api/v2.0",
            headers=headers,
            verify=verify_ssl,
            timeout=30.0
        )
    return client

# Debug Tools

@mcp.tool()
async def debug_connection() -> Dict[str, Any]:
    """Debug connection settings and environment variables"""
    return {
        "environment": {
            "TRUENAS_URL": os.getenv("TRUENAS_URL", "NOT SET"),
            "TRUENAS_API_KEY": os.getenv("TRUENAS_API_KEY", "NOT SET")[:20] + "..." if os.getenv("TRUENAS_API_KEY") else "NOT SET",
            "TRUENAS_VERIFY_SSL": os.getenv("TRUENAS_VERIFY_SSL", "NOT SET")
        },
        "client_status": "initialized" if client else "not initialized",
        "client_base_url": client.base_url if client else "N/A"
    }

@mcp.tool()
async def reset_connection() -> Dict[str, Any]:
    """Reset the HTTP client to force re-initialization"""
    global client
    if client:
        await client.aclose()
    client = None
    return {"success": True, "message": "Connection reset. Next API call will create new client."}

# User Management Tools

@mcp.tool()
async def list_users() -> Dict[str, Any]:
    """List all users in TrueNAS"""
    try:
        http_client = get_client()
        response = await http_client.get("/user")
        response.raise_for_status()
        users = response.json()
        
        # Return simplified user info
        user_list = [{
            "id": user.get("id"),
            "username": user.get("username"),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "groups": user.get("groups", []),
            "shell": user.get("shell"),
            "home": user.get("home"),
            "locked": user.get("locked", False),
            "sudo": user.get("sudo", False),
            "builtin": user.get("builtin", False)
        } for user in users]
        
        return {"success": True, "users": user_list, "count": len(user_list)}
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to list users: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

@mcp.tool()
async def get_user(username: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific user
    
    Args:
        username: Username to look up
    """
    try:
        http_client = get_client()
        response = await http_client.get("/user")
        response.raise_for_status()
        users = response.json()
        
        # Find the user by username
        target_user = None
        for user in users:
            if user.get("username") == username:
                target_user = user
                break
        
        if not target_user:
            return {"success": False, "error": f"User '{username}' not found"}
        
        # Return detailed user information
        return {
            "success": True,
            "user": {
                "id": target_user.get("id"),
                "username": target_user.get("username"),
                "full_name": target_user.get("full_name"),
                "email": target_user.get("email"),
                "groups": target_user.get("groups", []),
                "shell": target_user.get("shell"),
                "home": target_user.get("home"),
                "locked": target_user.get("locked", False),
                "sudo": target_user.get("sudo", False),
                "builtin": target_user.get("builtin", False),
                "uid": target_user.get("uid")
            }
        }
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to get user info: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

# System Information Tools

@mcp.tool()
async def get_system_info() -> Dict[str, Any]:
    """Get TrueNAS system information"""
    try:
        http_client = get_client()
        response = await http_client.get("/system/info")
        response.raise_for_status()
        return {"success": True, "info": response.json()}
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to get system info: {str(e)}"}

# Storage Management Tools

@mcp.tool()
async def list_pools() -> Dict[str, Any]:
    """List all storage pools"""
    try:
        http_client = get_client()
        response = await http_client.get("/pool")
        response.raise_for_status()
        return {"success": True, "pools": response.json()}
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to list pools: {str(e)}"}

@mcp.tool()
async def list_datasets() -> Dict[str, Any]:
    """List all datasets"""
    try:
        http_client = get_client()
        response = await http_client.get("/pool/dataset")
        response.raise_for_status()
        return {"success": True, "datasets": response.json()}
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to list datasets: {str(e)}"}

@mcp.tool()
async def get_pool_status(pool_name: str) -> Dict[str, Any]:
    """
    Get detailed status of a specific pool
    
    Args:
        pool_name: Name of the pool
    """
    try:
        http_client = get_client()
        response = await http_client.get(f"/pool/id/{pool_name}")
        response.raise_for_status()
        pool_data = response.json()
        
        # Extract relevant status information
        return {
            "success": True,
            "pool": {
                "name": pool_data.get("name"),
                "status": pool_data.get("status"),
                "healthy": pool_data.get("healthy"),
                "size": pool_data.get("size"),
                "allocated": pool_data.get("allocated"),
                "free": pool_data.get("free"),
                "fragmentation": pool_data.get("fragmentation"),
                "topology": pool_data.get("topology", {})
            }
        }
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to get pool status: {str(e)}"}

@mcp.tool()
async def create_dataset(
    pool: str,
    name: str,
    compression: str = "lz4",
    quota: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a new dataset
    
    Args:
        pool: Pool name where dataset will be created
        name: Dataset name
        compression: Compression algorithm (default: lz4)
        quota: Optional quota in bytes
    """
    try:
        http_client = get_client()
        data = {
            "name": f"{pool}/{name}",
            "compression": compression
        }
        
        if quota:
            data["quota"] = quota
        
        response = await http_client.post("/pool/dataset", json=data)
        response.raise_for_status()
        return {"success": True, "dataset": response.json()}
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to create dataset: {str(e)}"}

# Sharing Tools

@mcp.tool()
async def list_smb_shares() -> Dict[str, Any]:
    """List all SMB shares"""
    try:
        http_client = get_client()
        response = await http_client.get("/sharing/smb")
        response.raise_for_status()
        return {"success": True, "shares": response.json()}
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to list SMB shares: {str(e)}"}

@mcp.tool()
async def create_smb_share(
    path: str,
    name: str,
    comment: str = "",
    read_only: bool = False
) -> Dict[str, Any]:
    """
    Create a new SMB share
    
    Args:
        path: Path to share
        name: Share name
        comment: Optional comment
        read_only: Whether share is read-only
    """
    try:
        http_client = get_client()
        data = {
            "path": path,
            "name": name,
            "comment": comment,
            "ro": read_only
        }
        
        response = await http_client.post("/sharing/smb", json=data)
        response.raise_for_status()
        return {"success": True, "share": response.json()}
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to create SMB share: {str(e)}"}

# Snapshot Tools

@mcp.tool()
async def create_snapshot(
    dataset: str,
    name: str,
    recursive: bool = False
) -> Dict[str, Any]:
    """
    Create a snapshot of a dataset
    
    Args:
        dataset: Dataset path (e.g., "tank/data")
        name: Snapshot name
        recursive: Whether to create recursive snapshots
    """
    try:
        http_client = get_client()
        data = {
            "dataset": dataset,
            "name": name,
            "recursive": recursive
        }
        
        response = await http_client.post("/zfs/snapshot", json=data)
        response.raise_for_status()
        return {"success": True, "snapshot": response.json()}
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to create snapshot: {str(e)}"}

# ============= PHASE 2 FEATURES =============

# Dataset Permission Management Tools

@mcp.tool()
async def modify_dataset_permissions(
    dataset: str,
    mode: Optional[str] = None,
    owner: Optional[str] = None,
    group: Optional[str] = None,
    recursive: bool = False
) -> Dict[str, Any]:
    """
    Modify dataset permissions (chmod/chown equivalent)
    
    Args:
        dataset: Dataset path (e.g., "tank/data")
        mode: Unix permission mode (e.g., "755", "644")
        owner: Owner username or UID
        group: Group name or GID
        recursive: Apply permissions recursively
    """
    try:
        http_client = get_client()
        
        # Build the permission update payload
        data = {
            "path": f"/mnt/{dataset}",
            "options": {}
        }
        
        if mode:
            data["mode"] = mode
        if owner:
            data["uid"] = owner if isinstance(owner, int) else None
            data["user"] = owner if isinstance(owner, str) else None
        if group:
            data["gid"] = group if isinstance(group, int) else None
            data["group"] = group if isinstance(group, str) else None
        
        if recursive:
            data["options"]["recursive"] = True
            data["options"]["traverse"] = True
        
        response = await http_client.post("/filesystem/setperm", json=data)
        response.raise_for_status()
        
        return {
            "success": True,
            "message": f"Permissions updated for dataset {dataset}",
            "details": {
                "dataset": dataset,
                "mode": mode,
                "owner": owner,
                "group": group,
                "recursive": recursive
            }
        }
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to modify permissions: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

@mcp.tool()
async def update_dataset_acl(
    dataset: str,
    acl_entries: List[Dict[str, Any]],
    recursive: bool = False,
    strip_acl: bool = False
) -> Dict[str, Any]:
    """
    Update dataset Access Control Lists (ACLs)
    
    Args:
        dataset: Dataset path (e.g., "tank/data")
        acl_entries: List of ACL entries with permissions
        recursive: Apply ACLs recursively
        strip_acl: Remove all ACLs and revert to Unix permissions
    """
    try:
        http_client = get_client()
        
        if strip_acl:
            # Strip ACLs and revert to Unix permissions
            data = {
                "path": f"/mnt/{dataset}",
                "options": {
                    "stripacl": True,
                    "recursive": recursive
                }
            }
        else:
            # Apply new ACL entries
            data = {
                "path": f"/mnt/{dataset}",
                "dacl": acl_entries,
                "options": {
                    "recursive": recursive,
                    "traverse": recursive
                }
            }
        
        response = await http_client.post("/filesystem/setacl", json=data)
        response.raise_for_status()
        
        return {
            "success": True,
            "message": f"ACL updated for dataset {dataset}",
            "details": {
                "dataset": dataset,
                "acl_entries": len(acl_entries) if not strip_acl else 0,
                "recursive": recursive,
                "stripped": strip_acl
            }
        }
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to update ACL: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

@mcp.tool()
async def get_dataset_permissions(dataset: str) -> Dict[str, Any]:
    """
    Get current permissions and ACL information for a dataset
    
    Args:
        dataset: Dataset path (e.g., "tank/data")
    """
    try:
        http_client = get_client()
        
        # Get file system permissions
        response = await http_client.post("/filesystem/stat", json={"path": f"/mnt/{dataset}"})
        response.raise_for_status()
        stat_info = response.json()
        
        # Get ACL information
        acl_response = await http_client.post("/filesystem/getacl", json={"path": f"/mnt/{dataset}"})
        acl_info = acl_response.json() if acl_response.status_code == 200 else None
        
        return {
            "success": True,
            "permissions": {
                "dataset": dataset,
                "mode": stat_info.get("mode"),
                "owner": stat_info.get("user"),
                "group": stat_info.get("group"),
                "uid": stat_info.get("uid"),
                "gid": stat_info.get("gid"),
                "acl": acl_info.get("acl", []) if acl_info else None,
                "acl_enabled": acl_info is not None and len(acl_info.get("acl", [])) > 0
            }
        }
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to get permissions: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

# Dataset Property Management

@mcp.tool()
async def modify_dataset_properties(
    dataset: str,
    properties: Dict[str, Union[str, int, bool]]
) -> Dict[str, Any]:
    """
    Modify ZFS dataset properties
    
    Args:
        dataset: Dataset path (e.g., "tank/data")
        properties: Dictionary of properties to update
                   Examples: {"compression": "lz4", "dedup": "on", "quota": "10G"}
    """
    try:
        http_client = get_client()
        
        # Convert human-readable sizes to bytes if needed
        converted_props = {}
        for key, value in properties.items():
            if key in ["quota", "refquota", "reservation", "refreservation"] and isinstance(value, str):
                # Convert sizes like "10G" to bytes
                converted_props[key] = _parse_size(value)
            else:
                converted_props[key] = value
        
        # Get dataset ID first
        datasets_response = await http_client.get("/pool/dataset")
        datasets_response.raise_for_status()
        datasets = datasets_response.json()
        
        dataset_id = None
        for ds in datasets:
            if ds.get("name") == dataset:
                dataset_id = ds.get("id")
                break
        
        if not dataset_id:
            return {"success": False, "error": f"Dataset '{dataset}' not found"}
        
        # Update dataset properties
        response = await http_client.put(f"/pool/dataset/id/{dataset_id}", json=converted_props)
        response.raise_for_status()
        
        return {
            "success": True,
            "message": f"Properties updated for dataset {dataset}",
            "updated_properties": list(properties.keys()),
            "dataset": response.json()
        }
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to modify properties: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

@mcp.tool()
async def get_dataset_properties(dataset: str) -> Dict[str, Any]:
    """
    Get all properties of a dataset
    
    Args:
        dataset: Dataset path (e.g., "tank/data")
    """
    try:
        http_client = get_client()
        
        # Get dataset information
        response = await http_client.get("/pool/dataset")
        response.raise_for_status()
        datasets = response.json()
        
        target_dataset = None
        for ds in datasets:
            if ds.get("name") == dataset:
                target_dataset = ds
                break
        
        if not target_dataset:
            return {"success": False, "error": f"Dataset '{dataset}' not found"}
        
        # Extract key properties
        properties = {
            "compression": target_dataset.get("compression", {}).get("value"),
            "deduplication": target_dataset.get("deduplication", {}).get("value"),
            "quota": target_dataset.get("quota", {}).get("value"),
            "refquota": target_dataset.get("refquota", {}).get("value"),
            "reservation": target_dataset.get("reservation", {}).get("value"),
            "refreservation": target_dataset.get("refreservation", {}).get("value"),
            "recordsize": target_dataset.get("recordsize", {}).get("value"),
            "atime": target_dataset.get("atime", {}).get("value"),
            "sync": target_dataset.get("sync", {}).get("value"),
            "snapdir": target_dataset.get("snapdir", {}).get("value"),
            "copies": target_dataset.get("copies", {}).get("value"),
            "readonly": target_dataset.get("readonly", {}).get("value"),
            "exec": target_dataset.get("exec", {}).get("value"),
            "used": target_dataset.get("used", {}).get("value"),
            "available": target_dataset.get("available", {}).get("value"),
            "referenced": target_dataset.get("referenced", {}).get("value"),
        }
        
        return {
            "success": True,
            "dataset": dataset,
            "properties": properties,
            "all_properties": target_dataset
        }
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to get properties: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

# Kubernetes Storage Integration

@mcp.tool()
async def create_nfs_export(
    dataset: str,
    allowed_networks: List[str] = None,
    read_only: bool = False,
    maproot_user: str = "root",
    maproot_group: str = "wheel"
) -> Dict[str, Any]:
    """
    Create an NFS export for Kubernetes persistent volumes
    
    Args:
        dataset: Dataset path to export (e.g., "tank/k8s-volumes")
        allowed_networks: List of allowed networks (e.g., ["10.0.0.0/24"])
        read_only: Whether the export is read-only
        maproot_user: User to map root to
        maproot_group: Group to map root to
    """
    try:
        http_client = get_client()
        
        # Default to allow all if no networks specified
        if not allowed_networks:
            allowed_networks = ["0.0.0.0/0"]
        
        data = {
            "path": f"/mnt/{dataset}",
            "comment": f"Kubernetes NFS export for {dataset}",
            "ro": read_only,
            "maproot_user": maproot_user,
            "maproot_group": maproot_group,
            "networks": allowed_networks,
            "hosts": [],
            "alldirs": True,
            "enabled": True
        }
        
        response = await http_client.post("/sharing/nfs", json=data)
        response.raise_for_status()
        
        return {
            "success": True,
            "message": f"NFS export created for dataset {dataset}",
            "export": response.json(),
            "k8s_example": {
                "storage_class": _generate_nfs_storageclass(dataset),
                "pv_example": _generate_nfs_pv_example(dataset)
            }
        }
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to create NFS export: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

@mcp.tool()
async def create_iscsi_target(
    name: str,
    dataset: str,
    size: str,
    portal_id: int = 1
) -> Dict[str, Any]:
    """
    Create an iSCSI target for Kubernetes block storage
    
    Args:
        name: Target name (e.g., "k8s-block-01")
        dataset: Dataset for storing the iSCSI extent
        size: Size of the iSCSI extent (e.g., "100G")
        portal_id: iSCSI portal ID to use
    """
    try:
        http_client = get_client()
        
        # First, create the extent (LUN)
        extent_data = {
            "name": f"{name}-extent",
            "type": "DISK",
            "disk": f"zvol/{dataset}/{name}",
            "filesize": _parse_size(size),
            "blocksize": 512,
            "rpm": "SSD",
            "enabled": True
        }
        
        extent_response = await http_client.post("/iscsi/extent", json=extent_data)
        extent_response.raise_for_status()
        extent = extent_response.json()
        
        # Create the target
        target_data = {
            "name": f"iqn.2025-01.com.truenas:{name}",
            "alias": name,
            "mode": "ISCSI",
            "groups": []
        }
        
        target_response = await http_client.post("/iscsi/target", json=target_data)
        target_response.raise_for_status()
        target = target_response.json()
        
        # Create target-extent mapping
        mapping_data = {
            "target": target["id"],
            "extent": extent["id"],
            "lunid": 0
        }
        
        mapping_response = await http_client.post("/iscsi/targetextent", json=mapping_data)
        mapping_response.raise_for_status()
        
        return {
            "success": True,
            "message": f"iSCSI target created: {name}",
            "target": target,
            "extent": extent,
            "k8s_example": {
                "storage_class": _generate_iscsi_storageclass(name),
                "pv_example": _generate_iscsi_pv_example(name, size)
            }
        }
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to create iSCSI target: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

# Snapshot Policy Management

@mcp.tool()
async def create_snapshot_policy(
    dataset: str,
    name: str,
    schedule: Dict[str, Any],
    retention: Dict[str, int],
    recursive: bool = True
) -> Dict[str, Any]:
    """
    Create an automated snapshot policy
    
    Args:
        dataset: Dataset to snapshot
        name: Policy name
        schedule: Schedule configuration (cron-like)
                 {"minute": "0", "hour": "*/4", "dom": "*", "month": "*", "dow": "*"}
        retention: Retention settings {"hourly": 24, "daily": 7, "weekly": 4, "monthly": 12}
        recursive: Include child datasets
    """
    try:
        http_client = get_client()
        
        # Create periodic snapshot task
        data = {
            "dataset": dataset,
            "recursive": recursive,
            "lifetime_value": retention.get("daily", 7),
            "lifetime_unit": "DAY",
            "naming_schema": f"{name}-%Y%m%d-%H%M%S",
            "schedule": schedule,
            "enabled": True
        }
        
        response = await http_client.post("/pool/snapshottask", json=data)
        response.raise_for_status()
        
        return {
            "success": True,
            "message": f"Snapshot policy created for {dataset}",
            "policy": response.json(),
            "schedule": schedule,
            "retention": retention
        }
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Failed to create snapshot policy: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

# Helper functions

def _parse_size(size_str: str) -> int:
    """Convert human-readable size to bytes"""
    units = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
    size_str = size_str.upper()
    
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            return int(float(size_str[:-1]) * multiplier)
    
    # If no unit, assume bytes
    return int(size_str)

def _generate_nfs_storageclass(dataset: str) -> dict:
    """Generate Kubernetes NFS StorageClass YAML"""
    truenas_ip = os.getenv("TRUENAS_URL", "https://truenas.local").replace("https://", "").replace("http://", "")
    
    return {
        "apiVersion": "storage.k8s.io/v1",
        "kind": "StorageClass",
        "metadata": {
            "name": f"truenas-nfs-{dataset.replace('/', '-')}"
        },
        "provisioner": "nfs.csi.k8s.io",
        "parameters": {
            "server": truenas_ip,
            "share": f"/mnt/{dataset}",
            "mountPermissions": "0"
        },
        "reclaimPolicy": "Retain",
        "volumeBindingMode": "Immediate"
    }

def _generate_nfs_pv_example(dataset: str) -> dict:
    """Generate example NFS PersistentVolume YAML"""
    truenas_ip = os.getenv("TRUENAS_URL", "https://truenas.local").replace("https://", "").replace("http://", "")
    
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolume",
        "metadata": {
            "name": f"pv-nfs-{dataset.replace('/', '-')}"
        },
        "spec": {
            "capacity": {
                "storage": "10Gi"
            },
            "accessModes": ["ReadWriteMany"],
            "nfs": {
                "server": truenas_ip,
                "path": f"/mnt/{dataset}"
            },
            "persistentVolumeReclaimPolicy": "Retain"
        }
    }

def _generate_iscsi_storageclass(name: str) -> dict:
    """Generate Kubernetes iSCSI StorageClass YAML"""
    truenas_ip = os.getenv("TRUENAS_URL", "https://truenas.local").replace("https://", "").replace("http://", "")
    
    return {
        "apiVersion": "storage.k8s.io/v1",
        "kind": "StorageClass",
        "metadata": {
            "name": f"truenas-iscsi-{name}"
        },
        "provisioner": "democratic-csi.freenas-iscsi.csi.local",
        "parameters": {
            "fsType": "ext4",
            "detachedVolumesFromSnapshots": "false",
            "detachedVolumesFromVolumes": "false"
        },
        "reclaimPolicy": "Delete",
        "volumeBindingMode": "Immediate",
        "allowVolumeExpansion": True
    }

def _generate_iscsi_pv_example(name: str, size: str) -> dict:
    """Generate example iSCSI PersistentVolume YAML"""
    truenas_ip = os.getenv("TRUENAS_URL", "https://truenas.local").replace("https://", "").replace("http://", "")
    
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolume",
        "metadata": {
            "name": f"pv-iscsi-{name}"
        },
        "spec": {
            "capacity": {
                "storage": size
            },
            "accessModes": ["ReadWriteOnce"],
            "iscsi": {
                "targetPortal": f"{truenas_ip}:3260",
                "iqn": f"iqn.2025-01.com.truenas:{name}",
                "lun": 0,
                "fsType": "ext4",
                "readOnly": False
            },
            "persistentVolumeReclaimPolicy": "Retain"
        }
    }

# Cleanup function
async def cleanup():
    """Cleanup the HTTP client"""
    global client
    if client:
        await client.aclose()
        client = None

def main():
    """Main entry point for the TrueNAS MCP server"""
    try:
        # Run the server
        mcp.run()
    except KeyboardInterrupt:
        print("\nShutting down TrueNAS MCP server...")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Cleanup
        import asyncio
        asyncio.run(cleanup())
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
