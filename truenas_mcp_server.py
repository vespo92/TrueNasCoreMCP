#!/usr/bin/env python3
"""
TrueNAS Core MCP Server
A Model Context Protocol server for interacting with TrueNAS Core systems
"""

import os
import httpx
from typing import Dict, List, Any, Optional
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

# Cleanup function
async def cleanup():
    """Cleanup the HTTP client"""
    global client
    if client:
        await client.aclose()
        client = None

if __name__ == "__main__":
    try:
        # Run the server
        mcp.run()
    finally:
        # Cleanup on exit
        asyncio.run(cleanup())
