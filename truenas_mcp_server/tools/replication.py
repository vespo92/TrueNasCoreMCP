"""
Replication management tools for TrueNAS
"""

from typing import Dict, Any, Optional, List
from .base import BaseTool, tool_handler


class ReplicationTools(BaseTool):
    """Tools for managing TrueNAS replication tasks"""

    def get_tool_definitions(self) -> list:
        """Get tool definitions for replication management"""
        return [
            ("list_replication_tasks", self.list_replication_tasks,
             "List all replication tasks", {}),
            ("get_replication_task", self.get_replication_task,
             "Get detailed information about a replication task",
             {"task_id": {"type": "integer", "required": True}}),
            ("run_replication_task", self.run_replication_task,
             "Manually run a replication task",
             {"task_id": {"type": "integer", "required": True}}),
            ("create_replication_task", self.create_replication_task,
             "Create a new replication task",
             {"name": {"type": "string", "required": True},
              "source_datasets": {"type": "array", "required": True},
              "target_dataset": {"type": "string", "required": True},
              "direction": {"type": "string", "required": False},
              "transport": {"type": "string", "required": False},
              "ssh_credentials": {"type": "integer", "required": False}}),
            ("delete_replication_task", self.delete_replication_task,
             "Delete a replication task",
             {"task_id": {"type": "integer", "required": True}}),
            ("list_ssh_connections", self.list_ssh_connections,
             "List SSH connections for replication", {}),
            ("list_ssh_keypairs", self.list_ssh_keypairs,
             "List SSH keypairs for replication", {}),
            ("get_replication_history", self.get_replication_history,
             "Get history of replication task runs",
             {"task_id": {"type": "integer", "required": True}}),
            ("list_cloud_sync_tasks", self.list_cloud_sync_tasks,
             "List all cloud sync tasks", {}),
            ("list_rsync_tasks", self.list_rsync_tasks,
             "List all rsync tasks", {}),
        ]

    @tool_handler
    async def list_replication_tasks(self) -> Dict[str, Any]:
        """
        List all replication tasks

        Returns:
            Dictionary containing list of replication tasks
        """
        await self.ensure_initialized()

        tasks = await self.client.get("/replication")

        task_list = []
        for task in tasks:
            task_info = {
                "id": task.get("id"),
                "name": task.get("name"),
                "direction": task.get("direction"),
                "transport": task.get("transport"),
                "source_datasets": task.get("source_datasets", []),
                "target_dataset": task.get("target_dataset"),
                "recursive": task.get("recursive", False),
                "auto": task.get("auto", True),
                "enabled": task.get("enabled", True),
                "retention_policy": task.get("retention_policy"),
                "lifetime_value": task.get("lifetime_value"),
                "lifetime_unit": task.get("lifetime_unit"),
                "compression": task.get("compression"),
                "speed_limit": task.get("speed_limit"),
                "schedule": task.get("schedule"),
                "restrict_schedule": task.get("restrict_schedule"),
                "only_matching_schedule": task.get("only_matching_schedule"),
                "state": task.get("state", {}),
                "job": task.get("job"),
                "last_snapshot": task.get("state", {}).get("last_snapshot") if task.get("state") else None,
            }
            task_list.append(task_info)

        return {
            "success": True,
            "replication_tasks": task_list,
            "metadata": {
                "total_tasks": len(task_list),
                "enabled_tasks": sum(1 for t in task_list if t["enabled"]),
                "push_tasks": sum(1 for t in task_list if t["direction"] == "PUSH"),
                "pull_tasks": sum(1 for t in task_list if t["direction"] == "PULL"),
                "local_tasks": sum(1 for t in task_list if t["transport"] == "LOCAL")
            }
        }

    @tool_handler
    async def get_replication_task(self, task_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a replication task

        Args:
            task_id: ID of the replication task

        Returns:
            Dictionary containing task details
        """
        await self.ensure_initialized()

        try:
            task = await self.client.get(f"/replication/id/{task_id}")
        except Exception:
            return {
                "success": False,
                "error": f"Replication task with ID {task_id} not found"
            }

        return {
            "success": True,
            "task": {
                "id": task.get("id"),
                "name": task.get("name"),
                "direction": task.get("direction"),
                "transport": task.get("transport"),
                "ssh_credentials": task.get("ssh_credentials"),
                "netcat_active_side": task.get("netcat_active_side"),
                "netcat_active_side_listen_address": task.get("netcat_active_side_listen_address"),
                "netcat_active_side_port_min": task.get("netcat_active_side_port_min"),
                "netcat_active_side_port_max": task.get("netcat_active_side_port_max"),
                "netcat_passive_side_connect_address": task.get("netcat_passive_side_connect_address"),
                "source_datasets": task.get("source_datasets", []),
                "target_dataset": task.get("target_dataset"),
                "recursive": task.get("recursive"),
                "exclude": task.get("exclude", []),
                "properties": task.get("properties"),
                "properties_exclude": task.get("properties_exclude", []),
                "properties_override": task.get("properties_override", {}),
                "replicate": task.get("replicate"),
                "encryption": task.get("encryption"),
                "encryption_inherit": task.get("encryption_inherit"),
                "encryption_key": "***" if task.get("encryption_key") else None,
                "encryption_key_format": task.get("encryption_key_format"),
                "encryption_key_location": task.get("encryption_key_location"),
                "periodic_snapshot_tasks": task.get("periodic_snapshot_tasks", []),
                "naming_schema": task.get("naming_schema", []),
                "also_include_naming_schema": task.get("also_include_naming_schema", []),
                "name_regex": task.get("name_regex"),
                "auto": task.get("auto"),
                "schedule": task.get("schedule"),
                "restrict_schedule": task.get("restrict_schedule"),
                "only_matching_schedule": task.get("only_matching_schedule"),
                "allow_from_scratch": task.get("allow_from_scratch"),
                "readonly": task.get("readonly"),
                "hold_pending_snapshots": task.get("hold_pending_snapshots"),
                "retention_policy": task.get("retention_policy"),
                "lifetime_value": task.get("lifetime_value"),
                "lifetime_unit": task.get("lifetime_unit"),
                "lifetimes": task.get("lifetimes", []),
                "compression": task.get("compression"),
                "speed_limit": task.get("speed_limit"),
                "large_block": task.get("large_block"),
                "embed": task.get("embed"),
                "compressed": task.get("compressed"),
                "retries": task.get("retries"),
                "logging_level": task.get("logging_level"),
                "enabled": task.get("enabled"),
                "state": task.get("state", {}),
                "job": task.get("job"),
            }
        }

    @tool_handler
    async def run_replication_task(self, task_id: int) -> Dict[str, Any]:
        """
        Manually run a replication task

        Args:
            task_id: ID of the replication task to run

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        try:
            result = await self.client.post(f"/replication/id/{task_id}/run")
            return {
                "success": True,
                "message": f"Replication task {task_id} started",
                "task_id": task_id,
                "job_id": result if isinstance(result, int) else result.get("id") if isinstance(result, dict) else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to run replication task: {str(e)}"
            }

    @tool_handler
    async def create_replication_task(
        self,
        name: str,
        source_datasets: List[str],
        target_dataset: str,
        direction: str = "PUSH",
        transport: str = "LOCAL",
        ssh_credentials: Optional[int] = None,
        recursive: bool = True,
        auto: bool = True,
        retention_policy: str = "SOURCE",
        replicate: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new replication task

        Args:
            name: Name for the replication task
            source_datasets: List of source dataset paths
            target_dataset: Target dataset path
            direction: PUSH or PULL
            transport: LOCAL, SSH, or NETCAT
            ssh_credentials: SSH credential ID for remote replication
            recursive: Include child datasets
            auto: Enable automatic scheduling
            retention_policy: SOURCE, CUSTOM, or NONE
            replicate: Replicate properties

        Returns:
            Dictionary containing created task
        """
        await self.ensure_initialized()

        # Validate direction
        if direction.upper() not in ["PUSH", "PULL"]:
            return {
                "success": False,
                "error": "Direction must be PUSH or PULL"
            }

        # Validate transport
        if transport.upper() not in ["LOCAL", "SSH", "NETCAT"]:
            return {
                "success": False,
                "error": "Transport must be LOCAL, SSH, or NETCAT"
            }

        # SSH credentials required for remote replication
        if transport.upper() != "LOCAL" and not ssh_credentials:
            return {
                "success": False,
                "error": "SSH credentials required for remote replication"
            }

        task_data = {
            "name": name,
            "source_datasets": source_datasets,
            "target_dataset": target_dataset,
            "direction": direction.upper(),
            "transport": transport.upper(),
            "recursive": recursive,
            "auto": auto,
            "retention_policy": retention_policy.upper(),
            "replicate": replicate,
            "enabled": True
        }

        if ssh_credentials:
            task_data["ssh_credentials"] = ssh_credentials

        try:
            created = await self.client.post("/replication", task_data)
            return {
                "success": True,
                "message": f"Replication task '{name}' created successfully",
                "task": {
                    "id": created.get("id"),
                    "name": created.get("name"),
                    "direction": created.get("direction"),
                    "transport": created.get("transport"),
                    "source_datasets": created.get("source_datasets"),
                    "target_dataset": created.get("target_dataset")
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create replication task: {str(e)}"
            }

    @tool_handler
    async def delete_replication_task(self, task_id: int) -> Dict[str, Any]:
        """
        Delete a replication task

        Args:
            task_id: ID of the replication task to delete

        Returns:
            Dictionary confirming deletion
        """
        await self.ensure_initialized()

        # Check if destructive operations are allowed
        if not self.settings.enable_destructive_operations:
            return {
                "success": False,
                "error": "Destructive operations are disabled. Enable TRUENAS_ENABLE_DESTRUCTIVE_OPS to allow task deletion."
            }

        try:
            # Get task details first
            task = await self.client.get(f"/replication/id/{task_id}")
            task_name = task.get("name", f"ID {task_id}")

            await self.client.delete(f"/replication/id/{task_id}")
            return {
                "success": True,
                "message": f"Replication task '{task_name}' deleted successfully",
                "deleted_id": task_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete replication task: {str(e)}"
            }

    @tool_handler
    async def list_ssh_connections(self) -> Dict[str, Any]:
        """
        List SSH connections for replication

        Returns:
            Dictionary containing list of SSH connections
        """
        await self.ensure_initialized()

        try:
            connections = await self.client.get("/keychaincredential")
        except Exception:
            connections = []

        ssh_list = []
        for conn in connections:
            if conn.get("type") == "SSH_CREDENTIALS":
                conn_info = {
                    "id": conn.get("id"),
                    "name": conn.get("name"),
                    "type": conn.get("type"),
                    "attributes": {
                        "host": conn.get("attributes", {}).get("host"),
                        "port": conn.get("attributes", {}).get("port"),
                        "username": conn.get("attributes", {}).get("username"),
                        "connect_timeout": conn.get("attributes", {}).get("connect_timeout"),
                    }
                }
                ssh_list.append(conn_info)

        return {
            "success": True,
            "ssh_connections": ssh_list,
            "metadata": {
                "total_connections": len(ssh_list)
            }
        }

    @tool_handler
    async def list_ssh_keypairs(self) -> Dict[str, Any]:
        """
        List SSH keypairs for replication

        Returns:
            Dictionary containing list of SSH keypairs
        """
        await self.ensure_initialized()

        try:
            keypairs = await self.client.get("/keychaincredential")
        except Exception:
            keypairs = []

        keypair_list = []
        for kp in keypairs:
            if kp.get("type") == "SSH_KEY_PAIR":
                kp_info = {
                    "id": kp.get("id"),
                    "name": kp.get("name"),
                    "type": kp.get("type"),
                    "has_private_key": bool(kp.get("attributes", {}).get("private_key")),
                    "public_key_preview": kp.get("attributes", {}).get("public_key", "")[:50] + "..." if kp.get("attributes", {}).get("public_key") else None
                }
                keypair_list.append(kp_info)

        return {
            "success": True,
            "ssh_keypairs": keypair_list,
            "metadata": {
                "total_keypairs": len(keypair_list)
            }
        }

    @tool_handler
    async def get_replication_history(self, task_id: int) -> Dict[str, Any]:
        """
        Get history of replication task runs

        Args:
            task_id: ID of the replication task

        Returns:
            Dictionary containing task history
        """
        await self.ensure_initialized()

        try:
            # Get task state
            task = await self.client.get(f"/replication/id/{task_id}")
            state = task.get("state", {})

            return {
                "success": True,
                "task_id": task_id,
                "task_name": task.get("name"),
                "history": {
                    "state": state.get("state"),
                    "datetime": state.get("datetime"),
                    "last_snapshot": state.get("last_snapshot"),
                    "progress": state.get("progress", {}),
                    "error": state.get("error"),
                    "warnings": state.get("warnings", [])
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get replication history: {str(e)}"
            }

    @tool_handler
    async def list_cloud_sync_tasks(self) -> Dict[str, Any]:
        """
        List all cloud sync tasks

        Returns:
            Dictionary containing list of cloud sync tasks
        """
        await self.ensure_initialized()

        try:
            tasks = await self.client.get("/cloudsync")
        except Exception:
            tasks = []

        task_list = []
        for task in tasks:
            task_info = {
                "id": task.get("id"),
                "description": task.get("description"),
                "direction": task.get("direction"),
                "transfer_mode": task.get("transfer_mode"),
                "path": task.get("path"),
                "credentials": task.get("credentials"),
                "schedule": task.get("schedule"),
                "enabled": task.get("enabled", True),
                "bwlimit": task.get("bwlimit", []),
                "exclude": task.get("exclude", []),
                "include": task.get("include", []),
                "pre_script": bool(task.get("pre_script")),
                "post_script": bool(task.get("post_script")),
                "snapshot": task.get("snapshot"),
                "state": task.get("state", {}),
                "job": task.get("job")
            }
            task_list.append(task_info)

        return {
            "success": True,
            "cloud_sync_tasks": task_list,
            "metadata": {
                "total_tasks": len(task_list),
                "enabled_tasks": sum(1 for t in task_list if t["enabled"]),
                "push_tasks": sum(1 for t in task_list if t["direction"] == "PUSH"),
                "pull_tasks": sum(1 for t in task_list if t["direction"] == "PULL")
            }
        }

    @tool_handler
    async def list_rsync_tasks(self) -> Dict[str, Any]:
        """
        List all rsync tasks

        Returns:
            Dictionary containing list of rsync tasks
        """
        await self.ensure_initialized()

        try:
            tasks = await self.client.get("/rsynctask")
        except Exception:
            tasks = []

        task_list = []
        for task in tasks:
            task_info = {
                "id": task.get("id"),
                "path": task.get("path"),
                "remotehost": task.get("remotehost"),
                "remoteport": task.get("remoteport"),
                "remotemodule": task.get("remotemodule"),
                "remotepath": task.get("remotepath"),
                "direction": task.get("direction"),
                "mode": task.get("mode"),
                "desc": task.get("desc"),
                "user": task.get("user"),
                "schedule": task.get("schedule"),
                "recursive": task.get("recursive", True),
                "times": task.get("times", True),
                "compress": task.get("compress", True),
                "archive": task.get("archive", False),
                "delete": task.get("delete", False),
                "quiet": task.get("quiet", False),
                "preserveperm": task.get("preserveperm", False),
                "preserveattr": task.get("preserveattr", False),
                "delayupdates": task.get("delayupdates", True),
                "extra": task.get("extra", []),
                "enabled": task.get("enabled", True),
                "job": task.get("job")
            }
            task_list.append(task_info)

        return {
            "success": True,
            "rsync_tasks": task_list,
            "metadata": {
                "total_tasks": len(task_list),
                "enabled_tasks": sum(1 for t in task_list if t["enabled"]),
                "push_tasks": sum(1 for t in task_list if t["direction"] == "PUSH"),
                "pull_tasks": sum(1 for t in task_list if t["direction"] == "PULL")
            }
        }
