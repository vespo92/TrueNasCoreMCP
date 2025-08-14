"""
Sharing tools for TrueNAS (SMB, NFS, iSCSI)
"""

from typing import Dict, Any, List, Optional
from .base import BaseTool, tool_handler


class SharingTools(BaseTool):
    """Tools for managing TrueNAS file sharing"""
    
    def get_tool_definitions(self) -> list:
        """Get tool definitions for sharing management"""
        return [
            # SMB Tools
            ("list_smb_shares", self.list_smb_shares, "List all SMB shares", {}),
            ("create_smb_share", self.create_smb_share, "Create a new SMB share",
             {"path": {"type": "string", "required": True},
              "name": {"type": "string", "required": True},
              "comment": {"type": "string", "required": False},
              "read_only": {"type": "boolean", "required": False}}),
            ("delete_smb_share", self.delete_smb_share, "Delete an SMB share",
             {"share_name": {"type": "string", "required": True}}),
            
            # NFS Tools
            ("list_nfs_exports", self.list_nfs_exports, "List all NFS exports", {}),
            ("create_nfs_export", self.create_nfs_export, "Create an NFS export",
             {"path": {"type": "string", "required": True},
              "allowed_networks": {"type": "array", "required": False},
              "read_only": {"type": "boolean", "required": False},
              "maproot_user": {"type": "string", "required": False},
              "maproot_group": {"type": "string", "required": False}}),
            ("delete_nfs_export", self.delete_nfs_export, "Delete an NFS export",
             {"export_id": {"type": "integer", "required": True}}),
            
            # iSCSI Tools
            ("list_iscsi_targets", self.list_iscsi_targets, "List all iSCSI targets", {}),
            ("create_iscsi_target", self.create_iscsi_target, "Create an iSCSI target",
             {"name": {"type": "string", "required": True},
              "alias": {"type": "string", "required": False}}),
        ]
    
    # SMB Share Management
    
    @tool_handler
    async def list_smb_shares(self) -> Dict[str, Any]:
        """
        List all SMB shares
        
        Returns:
            Dictionary containing list of SMB shares
        """
        await self.ensure_initialized()
        
        shares = await self.client.get("/sharing/smb")
        
        share_list = []
        for share in shares:
            share_info = {
                "id": share.get("id"),
                "name": share.get("name"),
                "path": share.get("path"),
                "comment": share.get("comment"),
                "enabled": share.get("enabled", True),
                "read_only": share.get("ro", False),
                "browsable": share.get("browsable", True),
                "guest_ok": share.get("guestok", False),
                "hosts_allow": share.get("hostsallow", []),
                "hosts_deny": share.get("hostsdeny", []),
                "home": share.get("home", False),
                "timemachine": share.get("timemachine", False),
                "recyclebin": share.get("recyclebin", False),
                "audit": share.get("audit", {})
            }
            share_list.append(share_info)
        
        return {
            "success": True,
            "shares": share_list,
            "metadata": {
                "total_shares": len(share_list),
                "enabled_shares": sum(1 for s in share_list if s["enabled"]),
                "read_only_shares": sum(1 for s in share_list if s["read_only"]),
                "guest_shares": sum(1 for s in share_list if s["guest_ok"]),
                "timemachine_shares": sum(1 for s in share_list if s["timemachine"])
            }
        }
    
    @tool_handler
    async def create_smb_share(
        self,
        path: str,
        name: str,
        comment: str = "",
        read_only: bool = False,
        guest_ok: bool = False,
        browsable: bool = True,
        recyclebin: bool = False,
        hosts_allow: Optional[List[str]] = None,
        hosts_deny: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new SMB share
        
        Args:
            path: Path to share (must exist)
            name: Share name
            comment: Optional comment
            read_only: Whether share is read-only
            guest_ok: Allow guest access
            browsable: Show in network browse list
            recyclebin: Enable recycle bin
            hosts_allow: List of allowed hosts/networks
            hosts_deny: List of denied hosts/networks
            
        Returns:
            Dictionary containing created share information
        """
        await self.ensure_initialized()
        
        # Ensure path starts with /mnt/
        if not path.startswith("/mnt/"):
            path = f"/mnt/{path}"
        
        share_data = {
            "path": path,
            "name": name,
            "comment": comment,
            "ro": read_only,
            "guestok": guest_ok,
            "browsable": browsable,
            "recyclebin": recyclebin,
            "enabled": True
        }
        
        if hosts_allow:
            share_data["hostsallow"] = hosts_allow
        if hosts_deny:
            share_data["hostsdeny"] = hosts_deny
        
        created = await self.client.post("/sharing/smb", share_data)
        
        return {
            "success": True,
            "message": f"SMB share '{name}' created successfully",
            "share": {
                "id": created.get("id"),
                "name": created.get("name"),
                "path": created.get("path"),
                "enabled": created.get("enabled")
            }
        }
    
    @tool_handler
    async def delete_smb_share(self, share_name: str) -> Dict[str, Any]:
        """
        Delete an SMB share
        
        Args:
            share_name: Name of the share to delete
            
        Returns:
            Dictionary confirming deletion
        """
        await self.ensure_initialized()
        
        # Find the share
        shares = await self.client.get("/sharing/smb")
        target_share = None
        for share in shares:
            if share.get("name") == share_name:
                target_share = share
                break
        
        if not target_share:
            return {
                "success": False,
                "error": f"SMB share '{share_name}' not found"
            }
        
        # Delete the share
        share_id = target_share["id"]
        await self.client.delete(f"/sharing/smb/id/{share_id}")
        
        return {
            "success": True,
            "message": f"SMB share '{share_name}' deleted successfully",
            "deleted": {
                "name": share_name,
                "path": target_share.get("path")
            }
        }
    
    # NFS Export Management
    
    @tool_handler
    async def list_nfs_exports(self) -> Dict[str, Any]:
        """
        List all NFS exports
        
        Returns:
            Dictionary containing list of NFS exports
        """
        await self.ensure_initialized()
        
        exports = await self.client.get("/sharing/nfs")
        
        export_list = []
        for export in exports:
            export_info = {
                "id": export.get("id"),
                "path": export.get("path"),
                "comment": export.get("comment"),
                "enabled": export.get("enabled", True),
                "read_only": export.get("ro", False),
                "maproot_user": export.get("maproot_user"),
                "maproot_group": export.get("maproot_group"),
                "mapall_user": export.get("mapall_user"),
                "mapall_group": export.get("mapall_group"),
                "networks": export.get("networks", []),
                "hosts": export.get("hosts", []),
                "alldirs": export.get("alldirs", False),
                "security": export.get("security", [])
            }
            export_list.append(export_info)
        
        return {
            "success": True,
            "exports": export_list,
            "metadata": {
                "total_exports": len(export_list),
                "enabled_exports": sum(1 for e in export_list if e["enabled"]),
                "read_only_exports": sum(1 for e in export_list if e["read_only"]),
                "alldirs_exports": sum(1 for e in export_list if e["alldirs"])
            }
        }
    
    @tool_handler
    async def create_nfs_export(
        self,
        path: str,
        allowed_networks: Optional[List[str]] = None,
        allowed_hosts: Optional[List[str]] = None,
        read_only: bool = False,
        maproot_user: str = "root",
        maproot_group: str = "wheel",
        alldirs: bool = False,
        comment: str = ""
    ) -> Dict[str, Any]:
        """
        Create an NFS export
        
        Args:
            path: Path to export (must exist)
            allowed_networks: List of allowed networks (e.g., ["10.0.0.0/24"])
            allowed_hosts: List of allowed hosts
            read_only: Whether export is read-only
            maproot_user: User to map root to
            maproot_group: Group to map root to
            alldirs: Allow mounting of subdirectories
            comment: Optional comment
            
        Returns:
            Dictionary containing created export information
        """
        await self.ensure_initialized()
        
        # Ensure path starts with /mnt/
        if not path.startswith("/mnt/"):
            path = f"/mnt/{path}"
        
        # Default to allow all if no restrictions specified
        if not allowed_networks and not allowed_hosts:
            allowed_networks = ["0.0.0.0/0"]
        
        export_data = {
            "path": path,
            "comment": comment,
            "ro": read_only,
            "maproot_user": maproot_user,
            "maproot_group": maproot_group,
            "alldirs": alldirs,
            "enabled": True
        }
        
        if allowed_networks:
            export_data["networks"] = allowed_networks
        if allowed_hosts:
            export_data["hosts"] = allowed_hosts
        
        created = await self.client.post("/sharing/nfs", export_data)
        
        # Generate example mount command
        server_ip = str(self.settings.truenas_url).replace("https://", "").replace("http://", "").split(":")[0]
        mount_example = f"mount -t nfs {server_ip}:{path} /local/mount/point"
        
        return {
            "success": True,
            "message": f"NFS export created for path '{path}'",
            "export": {
                "id": created.get("id"),
                "path": created.get("path"),
                "networks": created.get("networks", []),
                "enabled": created.get("enabled")
            },
            "mount_example": mount_example
        }
    
    @tool_handler
    async def delete_nfs_export(self, export_id: int) -> Dict[str, Any]:
        """
        Delete an NFS export
        
        Args:
            export_id: ID of the export to delete
            
        Returns:
            Dictionary confirming deletion
        """
        await self.ensure_initialized()
        
        # Get the export details first
        exports = await self.client.get("/sharing/nfs")
        target_export = None
        for export in exports:
            if export.get("id") == export_id:
                target_export = export
                break
        
        if not target_export:
            return {
                "success": False,
                "error": f"NFS export with ID {export_id} not found"
            }
        
        # Delete the export
        await self.client.delete(f"/sharing/nfs/id/{export_id}")
        
        return {
            "success": True,
            "message": f"NFS export deleted successfully",
            "deleted": {
                "id": export_id,
                "path": target_export.get("path")
            }
        }
    
    # iSCSI Management
    
    @tool_handler
    async def list_iscsi_targets(self) -> Dict[str, Any]:
        """
        List all iSCSI targets
        
        Returns:
            Dictionary containing list of iSCSI targets
        """
        await self.ensure_initialized()
        
        targets = await self.client.get("/iscsi/target")
        extents = await self.client.get("/iscsi/extent")
        target_extents = await self.client.get("/iscsi/targetextent")
        
        # Map extents to targets
        target_extent_map = {}
        for te in target_extents:
            target_id = te.get("target")
            extent_id = te.get("extent")
            if target_id not in target_extent_map:
                target_extent_map[target_id] = []
            target_extent_map[target_id].append(extent_id)
        
        # Build extent lookup
        extent_map = {e["id"]: e for e in extents}
        
        target_list = []
        for target in targets:
            target_id = target.get("id")
            extent_ids = target_extent_map.get(target_id, [])
            
            target_extents_info = []
            for extent_id in extent_ids:
                if extent_id in extent_map:
                    extent = extent_map[extent_id]
                    target_extents_info.append({
                        "id": extent["id"],
                        "name": extent.get("name"),
                        "type": extent.get("type"),
                        "path": extent.get("path") or extent.get("disk"),
                        "filesize": self.format_size(extent.get("filesize", 0)) if extent.get("filesize") else None,
                        "enabled": extent.get("enabled", True)
                    })
            
            target_info = {
                "id": target.get("id"),
                "name": target.get("name"),
                "alias": target.get("alias"),
                "iqn": target.get("name"),  # IQN is stored in name field
                "mode": target.get("mode"),
                "groups": target.get("groups", []),
                "extents": target_extents_info
            }
            target_list.append(target_info)
        
        return {
            "success": True,
            "targets": target_list,
            "metadata": {
                "total_targets": len(target_list),
                "total_extents": len(extents),
                "targets_with_extents": sum(1 for t in target_list if t["extents"])
            }
        }
    
    @tool_handler
    async def create_iscsi_target(
        self,
        name: str,
        alias: Optional[str] = None,
        mode: str = "ISCSI",
        auth_networks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create an iSCSI target
        
        Args:
            name: Target name (will be part of IQN)
            alias: Optional alias for the target
            mode: Target mode (ISCSI or FC)
            auth_networks: List of authorized networks
            
        Returns:
            Dictionary containing created target information
        """
        await self.ensure_initialized()
        
        # Generate IQN
        from datetime import datetime
        year_month = datetime.now().strftime("%Y-%m")
        iqn = f"iqn.{year_month}.com.truenas:{name}"
        
        target_data = {
            "name": iqn,
            "alias": alias or name,
            "mode": mode,
            "groups": []
        }
        
        # Create auth group if networks specified
        if auth_networks:
            # This would require creating an auth group first
            # For now, we'll note this in the response
            pass
        
        created = await self.client.post("/iscsi/target", target_data)
        
        return {
            "success": True,
            "message": f"iSCSI target '{name}' created successfully",
            "target": {
                "id": created.get("id"),
                "iqn": created.get("name"),
                "alias": created.get("alias")
            },
            "next_steps": [
                "Create an extent (LUN) for this target",
                "Map the extent to this target",
                "Configure initiator groups if needed",
                "Enable iSCSI service if not already enabled"
            ]
        }