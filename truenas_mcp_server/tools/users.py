"""
User management tools for TrueNAS
"""

from typing import Dict, Any, List, Optional
from .base import BaseTool, tool_handler


class UserTools(BaseTool):
    """Tools for managing TrueNAS users"""
    
    def get_tool_definitions(self) -> list:
        """Get tool definitions for user management"""
        return [
            ("list_users", self.list_users, "List all users in TrueNAS", {}),
            ("get_user", self.get_user, "Get detailed information about a specific user", 
             {"username": {"type": "string", "required": True}}),
            ("create_user", self.create_user, "Create a new user",
             {"username": {"type": "string", "required": True},
              "full_name": {"type": "string", "required": False},
              "email": {"type": "string", "required": False},
              "password": {"type": "string", "required": True},
              "shell": {"type": "string", "required": False},
              "home": {"type": "string", "required": False},
              "groups": {"type": "array", "required": False}}),
            ("update_user", self.update_user, "Update an existing user",
             {"username": {"type": "string", "required": True},
              "updates": {"type": "object", "required": True}}),
            ("delete_user", self.delete_user, "Delete a user",
             {"username": {"type": "string", "required": True}}),
        ]
    
    @tool_handler
    async def list_users(self) -> Dict[str, Any]:
        """
        List all users in TrueNAS
        
        Returns:
            Dictionary containing list of users and metadata
        """
        await self.ensure_initialized()
        
        users = await self.client.get("/user")
        
        # Filter and format user data
        user_list = []
        for user in users:
            user_info = {
                "id": user.get("id"),
                "username": user.get("username"),
                "full_name": user.get("full_name"),
                "email": user.get("email"),
                "uid": user.get("uid"),
                "groups": user.get("groups", []),
                "shell": user.get("shell"),
                "home": user.get("home"),
                "locked": user.get("locked", False),
                "sudo": user.get("sudo", False),
                "builtin": user.get("builtin", False)
            }
            user_list.append(user_info)
        
        # Categorize users
        system_users = [u for u in user_list if u["builtin"]]
        regular_users = [u for u in user_list if not u["builtin"]]
        
        return {
            "success": True,
            "users": user_list,
            "metadata": {
                "total_count": len(user_list),
                "system_users": len(system_users),
                "regular_users": len(regular_users),
                "locked_users": sum(1 for u in user_list if u["locked"])
            }
        }
    
    @tool_handler
    async def get_user(self, username: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific user
        
        Args:
            username: Username to look up
            
        Returns:
            Dictionary containing user details
        """
        await self.ensure_initialized()
        
        # Get all users and find the specific one
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
        
        # Get additional user details if available
        user_details = {
            "id": target_user.get("id"),
            "username": target_user.get("username"),
            "full_name": target_user.get("full_name"),
            "email": target_user.get("email"),
            "uid": target_user.get("uid"),
            "gid": target_user.get("group", {}).get("gid") if isinstance(target_user.get("group"), dict) else None,
            "groups": target_user.get("groups", []),
            "shell": target_user.get("shell"),
            "home": target_user.get("home"),
            "locked": target_user.get("locked", False),
            "sudo": target_user.get("sudo", False),
            "builtin": target_user.get("builtin", False),
            "microsoft_account": target_user.get("microsoft_account", False),
            "attributes": target_user.get("attributes", {}),
            "sshpubkey": target_user.get("sshpubkey"),
            "created": target_user.get("created"),
            "modified": target_user.get("modified")
        }
        
        return {
            "success": True,
            "user": user_details
        }
    
    @tool_handler
    async def create_user(
        self,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        shell: Optional[str] = "/bin/bash",
        home: Optional[str] = None,
        groups: Optional[List[str]] = None,
        sudo: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new user
        
        Args:
            username: Username for the new user
            password: Password for the new user
            full_name: Full name of the user
            email: Email address
            shell: User shell (default: /bin/bash)
            home: Home directory (auto-generated if not specified)
            groups: List of group names to add user to
            sudo: Whether to grant sudo privileges
            
        Returns:
            Dictionary containing created user information
        """
        await self.ensure_initialized()
        
        # Prepare user data
        user_data = {
            "username": username,
            "password": password,
            "full_name": full_name or username,
            "email": email,
            "shell": shell,
            "sudo": sudo
        }
        
        # Set home directory
        if home:
            user_data["home"] = home
        else:
            user_data["home"] = f"/home/{username}"
        
        # Add groups if specified
        if groups:
            # Get all groups to validate
            all_groups = await self.client.get("/group")
            valid_groups = [g["id"] for g in all_groups if g["name"] in groups]
            if valid_groups:
                user_data["groups"] = valid_groups
        
        # Create the user
        created_user = await self.client.post("/user", user_data)
        
        return {
            "success": True,
            "message": f"User '{username}' created successfully",
            "user": {
                "id": created_user.get("id"),
                "username": created_user.get("username"),
                "uid": created_user.get("uid"),
                "home": created_user.get("home"),
                "shell": created_user.get("shell")
            }
        }
    
    @tool_handler
    async def update_user(self, username: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing user
        
        Args:
            username: Username to update
            updates: Dictionary of fields to update
            
        Returns:
            Dictionary containing updated user information
        """
        await self.ensure_initialized()
        
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
        
        # Validate and prepare updates
        allowed_updates = {
            "full_name", "email", "shell", "home", "locked",
            "sudo", "password", "groups", "sshpubkey"
        }
        
        filtered_updates = {
            k: v for k, v in updates.items()
            if k in allowed_updates
        }
        
        if not filtered_updates:
            return {
                "success": False,
                "error": "No valid fields to update"
            }
        
        # Update the user
        user_id = target_user["id"]
        updated_user = await self.client.put(f"/user/id/{user_id}", filtered_updates)
        
        return {
            "success": True,
            "message": f"User '{username}' updated successfully",
            "updated_fields": list(filtered_updates.keys()),
            "user": {
                "id": updated_user.get("id"),
                "username": updated_user.get("username"),
                "full_name": updated_user.get("full_name"),
                "email": updated_user.get("email")
            }
        }
    
    @tool_handler
    async def delete_user(self, username: str, delete_home: bool = False) -> Dict[str, Any]:
        """
        Delete a user
        
        Args:
            username: Username to delete
            delete_home: Whether to delete the user's home directory
            
        Returns:
            Dictionary confirming deletion
        """
        await self.ensure_initialized()
        
        # Check if destructive operations are allowed
        if not self.settings.enable_destructive_operations:
            return {
                "success": False,
                "error": "Destructive operations are disabled. Enable TRUENAS_ENABLE_DESTRUCTIVE_OPS to allow user deletion."
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
        
        # Check if it's a system user
        if target_user.get("builtin"):
            return {
                "success": False,
                "error": f"Cannot delete built-in system user '{username}'"
            }
        
        # Delete the user
        user_id = target_user["id"]
        delete_options = {"delete_group": True}
        
        if delete_home:
            delete_options["delete_home"] = True
        
        await self.client.delete(f"/user/id/{user_id}", delete_options)
        
        return {
            "success": True,
            "message": f"User '{username}' deleted successfully",
            "deleted": {
                "username": username,
                "uid": target_user.get("uid"),
                "home_deleted": delete_home
            }
        }