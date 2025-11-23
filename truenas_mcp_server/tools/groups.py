"""
Group management tools for TrueNAS
"""

from typing import Dict, Any, Optional, List
from .base import BaseTool, tool_handler


class GroupTools(BaseTool):
    """Tools for managing TrueNAS groups"""

    def get_tool_definitions(self) -> list:
        """Get tool definitions for group management"""
        return [
            ("list_groups", self.list_groups,
             "List all groups in TrueNAS", {}),
            ("get_group", self.get_group,
             "Get detailed information about a specific group",
             {"group_name": {"type": "string", "required": True}}),
            ("create_group", self.create_group,
             "Create a new group",
             {"name": {"type": "string", "required": True},
              "gid": {"type": "integer", "required": False},
              "sudo": {"type": "boolean", "required": False},
              "allow_duplicate_gid": {"type": "boolean", "required": False}}),
            ("update_group", self.update_group,
             "Update an existing group",
             {"group_name": {"type": "string", "required": True},
              "updates": {"type": "object", "required": True}}),
            ("delete_group", self.delete_group,
             "Delete a group",
             {"group_name": {"type": "string", "required": True}}),
            ("add_user_to_group", self.add_user_to_group,
             "Add a user to a group",
             {"group_name": {"type": "string", "required": True},
              "username": {"type": "string", "required": True}}),
            ("remove_user_from_group", self.remove_user_from_group,
             "Remove a user from a group",
             {"group_name": {"type": "string", "required": True},
              "username": {"type": "string", "required": True}}),
        ]

    @tool_handler
    async def list_groups(self) -> Dict[str, Any]:
        """
        List all groups in TrueNAS

        Returns:
            Dictionary containing list of groups and metadata
        """
        await self.ensure_initialized()

        groups = await self.client.get("/group")

        group_list = []
        for group in groups:
            group_info = {
                "id": group.get("id"),
                "gid": group.get("gid"),
                "name": group.get("group") or group.get("name"),
                "builtin": group.get("builtin", False),
                "sudo_commands": group.get("sudo_commands", []),
                "sudo_commands_nopasswd": group.get("sudo_commands_nopasswd", []),
                "smb": group.get("smb", True),
                "users": group.get("users", [])
            }
            group_list.append(group_info)

        # Categorize groups
        system_groups = [g for g in group_list if g["builtin"]]
        regular_groups = [g for g in group_list if not g["builtin"]]

        return {
            "success": True,
            "groups": group_list,
            "metadata": {
                "total_count": len(group_list),
                "system_groups": len(system_groups),
                "regular_groups": len(regular_groups),
                "smb_groups": sum(1 for g in group_list if g["smb"])
            }
        }

    @tool_handler
    async def get_group(self, group_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific group

        Args:
            group_name: Name of the group

        Returns:
            Dictionary containing group details
        """
        await self.ensure_initialized()

        groups = await self.client.get("/group")

        target_group = None
        for group in groups:
            name = group.get("group") or group.get("name")
            if name == group_name:
                target_group = group
                break

        if not target_group:
            return {
                "success": False,
                "error": f"Group '{group_name}' not found"
            }

        # Get group members details
        members = []
        user_ids = target_group.get("users", [])
        if user_ids:
            users = await self.client.get("/user")
            for user in users:
                if user.get("id") in user_ids:
                    members.append({
                        "id": user.get("id"),
                        "username": user.get("username"),
                        "uid": user.get("uid")
                    })

        return {
            "success": True,
            "group": {
                "id": target_group.get("id"),
                "gid": target_group.get("gid"),
                "name": target_group.get("group") or target_group.get("name"),
                "builtin": target_group.get("builtin", False),
                "sudo_commands": target_group.get("sudo_commands", []),
                "sudo_commands_nopasswd": target_group.get("sudo_commands_nopasswd", []),
                "smb": target_group.get("smb", True),
                "users": target_group.get("users", []),
                "members": members
            }
        }

    @tool_handler
    async def create_group(
        self,
        name: str,
        gid: Optional[int] = None,
        sudo: bool = False,
        smb: bool = True,
        allow_duplicate_gid: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new group

        Args:
            name: Group name
            gid: Optional group ID (auto-assigned if not specified)
            sudo: Whether to grant sudo privileges
            smb: Whether this is an SMB group
            allow_duplicate_gid: Allow duplicate GID

        Returns:
            Dictionary containing created group information
        """
        await self.ensure_initialized()

        group_data = {
            "name": name,
            "smb": smb,
            "allow_duplicate_gid": allow_duplicate_gid
        }

        if gid is not None:
            group_data["gid"] = gid

        if sudo:
            group_data["sudo_commands"] = ["ALL"]

        created_group = await self.client.post("/group", group_data)

        return {
            "success": True,
            "message": f"Group '{name}' created successfully",
            "group": {
                "id": created_group.get("id"),
                "gid": created_group.get("gid"),
                "name": created_group.get("group") or created_group.get("name"),
                "smb": created_group.get("smb")
            }
        }

    @tool_handler
    async def update_group(self, group_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing group

        Args:
            group_name: Name of the group to update
            updates: Dictionary of fields to update

        Returns:
            Dictionary containing updated group information
        """
        await self.ensure_initialized()

        # Find the group
        groups = await self.client.get("/group")
        target_group = None
        for group in groups:
            name = group.get("group") or group.get("name")
            if name == group_name:
                target_group = group
                break

        if not target_group:
            return {
                "success": False,
                "error": f"Group '{group_name}' not found"
            }

        # Validate and filter updates
        allowed_updates = {"name", "sudo_commands", "sudo_commands_nopasswd", "smb", "users"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_updates}

        if not filtered_updates:
            return {
                "success": False,
                "error": "No valid fields to update"
            }

        # Update the group
        group_id = target_group["id"]
        updated_group = await self.client.put(f"/group/id/{group_id}", filtered_updates)

        return {
            "success": True,
            "message": f"Group '{group_name}' updated successfully",
            "updated_fields": list(filtered_updates.keys()),
            "group": {
                "id": updated_group.get("id"),
                "name": updated_group.get("group") or updated_group.get("name"),
                "gid": updated_group.get("gid")
            }
        }

    @tool_handler
    async def delete_group(self, group_name: str, delete_users: bool = False) -> Dict[str, Any]:
        """
        Delete a group

        Args:
            group_name: Name of the group to delete
            delete_users: Whether to delete users that have this as primary group

        Returns:
            Dictionary confirming deletion
        """
        await self.ensure_initialized()

        # Check if destructive operations are allowed
        if not self.settings.enable_destructive_operations:
            return {
                "success": False,
                "error": "Destructive operations are disabled. Enable TRUENAS_ENABLE_DESTRUCTIVE_OPS to allow group deletion."
            }

        # Find the group
        groups = await self.client.get("/group")
        target_group = None
        for group in groups:
            name = group.get("group") or group.get("name")
            if name == group_name:
                target_group = group
                break

        if not target_group:
            return {
                "success": False,
                "error": f"Group '{group_name}' not found"
            }

        # Check if it's a system group
        if target_group.get("builtin"):
            return {
                "success": False,
                "error": f"Cannot delete built-in system group '{group_name}'"
            }

        # Delete the group
        group_id = target_group["id"]
        delete_options = {"delete_users": delete_users}

        await self.client.delete(f"/group/id/{group_id}", delete_options)

        return {
            "success": True,
            "message": f"Group '{group_name}' deleted successfully",
            "deleted": {
                "name": group_name,
                "gid": target_group.get("gid"),
                "users_deleted": delete_users
            }
        }

    @tool_handler
    async def add_user_to_group(self, group_name: str, username: str) -> Dict[str, Any]:
        """
        Add a user to a group

        Args:
            group_name: Name of the group
            username: Username to add

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        # Find the group
        groups = await self.client.get("/group")
        target_group = None
        for group in groups:
            name = group.get("group") or group.get("name")
            if name == group_name:
                target_group = group
                break

        if not target_group:
            return {
                "success": False,
                "error": f"Group '{group_name}' not found"
            }

        # Find the user
        users = await self.client.get("/user")
        target_user = None
        for user in users:
            if user.get("username") == username:
                target_user = user
                break

        if not target_user:
            return {
                "success": False,
                "error": f"User '{username}' not found"
            }

        # Check if user is already in group
        current_users = target_group.get("users", [])
        if target_user["id"] in current_users:
            return {
                "success": False,
                "error": f"User '{username}' is already a member of group '{group_name}'"
            }

        # Add user to group
        new_users = current_users + [target_user["id"]]
        group_id = target_group["id"]
        await self.client.put(f"/group/id/{group_id}", {"users": new_users})

        return {
            "success": True,
            "message": f"User '{username}' added to group '{group_name}'",
            "group": group_name,
            "user": username
        }

    @tool_handler
    async def remove_user_from_group(self, group_name: str, username: str) -> Dict[str, Any]:
        """
        Remove a user from a group

        Args:
            group_name: Name of the group
            username: Username to remove

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        # Find the group
        groups = await self.client.get("/group")
        target_group = None
        for group in groups:
            name = group.get("group") or group.get("name")
            if name == group_name:
                target_group = group
                break

        if not target_group:
            return {
                "success": False,
                "error": f"Group '{group_name}' not found"
            }

        # Find the user
        users = await self.client.get("/user")
        target_user = None
        for user in users:
            if user.get("username") == username:
                target_user = user
                break

        if not target_user:
            return {
                "success": False,
                "error": f"User '{username}' not found"
            }

        # Check if user is in group
        current_users = target_group.get("users", [])
        if target_user["id"] not in current_users:
            return {
                "success": False,
                "error": f"User '{username}' is not a member of group '{group_name}'"
            }

        # Remove user from group
        new_users = [uid for uid in current_users if uid != target_user["id"]]
        group_id = target_group["id"]
        await self.client.put(f"/group/id/{group_id}", {"users": new_users})

        return {
            "success": True,
            "message": f"User '{username}' removed from group '{group_name}'",
            "group": group_name,
            "user": username
        }
