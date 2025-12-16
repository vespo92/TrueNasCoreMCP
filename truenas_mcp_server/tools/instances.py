"""
TrueNAS Incus Instance management tools

Provides tools for managing Incus VMs and Containers on TrueNAS SCALE.
Uses the /api/v2.0/virt/instance endpoints.

API Quirks (IMPORTANT!):
- POST /virt/instance/start expects a plain string body: "instance_name" (NOT an object!)
- POST /virt/instance/stop expects: {"id": "instance_name"} (an object)
- PUT /virt/instance/id/{id} expects: {"cpu": "2", "memory": 4294967296, ...}
- Instance operations are async and return job IDs
- Memory is specified in bytes (not MB!)
"""

import asyncio
from typing import Any, Dict, List, Optional

from .base import BaseTool, tool_handler


class InstanceTools(BaseTool):
    """Tools for managing TrueNAS Incus instances (VMs and Containers)"""

    # Timeout for instance operations
    INSTANCE_OPERATION_TIMEOUT = 120  # seconds
    POLL_INTERVAL = 5  # seconds

    def get_tool_definitions(self) -> list:
        """Get tool definitions for instance management"""
        return [
            ("list_instances", self.list_instances,
             "List all Incus instances (VMs and Containers)",
             {"instance_type": {"type": "string", "required": False,
                               "description": "Filter by type: 'VM' or 'CONTAINER' (optional)"},
              "limit": {"type": "integer", "required": False,
                       "description": "Max items to return (default: 100, max: 500)"},
              "offset": {"type": "integer", "required": False,
                        "description": "Items to skip for pagination"}}),
            ("get_instance", self.get_instance,
             "Get detailed information about a specific instance",
             {"instance_name": {"type": "string", "required": True,
                               "description": "Name of the instance"},
              "include_raw": {"type": "boolean", "required": False,
                             "description": "Include full API response for debugging (default: false)"}}),
            ("start_instance", self.start_instance, "Start an Incus instance",
             {"instance_name": {"type": "string", "required": True,
                               "description": "Name of the instance to start"}}),
            ("stop_instance", self.stop_instance, "Stop an Incus instance",
             {"instance_name": {"type": "string", "required": True,
                               "description": "Name of the instance to stop"},
              "force": {"type": "boolean", "required": False,
                       "description": "Force stop without graceful shutdown"},
              "timeout": {"type": "integer", "required": False,
                         "description": "Timeout in seconds for graceful shutdown"}}),
            ("restart_instance", self.restart_instance, "Restart an Incus instance",
             {"instance_name": {"type": "string", "required": True,
                               "description": "Name of the instance to restart"}}),
            ("update_instance", self.update_instance,
             "Update instance configuration (CPU, memory, autostart)",
             {"instance_name": {"type": "string", "required": True,
                               "description": "Name of the instance to update"},
              "cpu": {"type": "string", "required": False,
                     "description": "Number of CPU cores (as string, e.g., '4')"},
              "memory": {"type": "integer", "required": False,
                        "description": "Memory in bytes (e.g., 8589934592 for 8GB)"},
              "autostart": {"type": "boolean", "required": False,
                           "description": "Whether to start instance on boot"}}),
            ("list_instance_devices", self.list_instance_devices,
             "List devices attached to an instance",
             {"instance_name": {"type": "string", "required": True,
                               "description": "Name of the instance"}}),
        ]

    @tool_handler
    async def list_instances(
        self,
        instance_type: Optional[str] = None,
        limit: int = BaseTool.DEFAULT_LIMIT,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List all Incus instances (VMs and Containers)

        Args:
            instance_type: Optional filter by type ('VM' or 'CONTAINER')
            limit: Maximum number of items to return (default: 100, max: 500)
            offset: Number of items to skip for pagination

        Returns:
            Dictionary containing list of instances with status
        """
        await self.ensure_initialized()

        instances = await self.client.get("/virt/instance")

        instance_list = []
        for inst in instances:
            # Filter by type if specified
            inst_type = inst.get("type", "UNKNOWN")
            if instance_type and inst_type != instance_type.upper():
                continue

            # Convert memory to GB for readability
            memory_bytes = inst.get("memory", 0)
            memory_gb = round(memory_bytes / (1024**3), 2)

            instance_info = {
                "id": inst.get("id"),
                "name": inst.get("name") or inst.get("id"),
                "type": inst_type,
                "status": inst.get("status", "UNKNOWN"),
                "cpu": inst.get("cpu", "0"),
                "memory_gb": memory_gb,
                "memory_bytes": memory_bytes,
                "autostart": inst.get("autostart", False),
                "image": inst.get("image"),
            }
            instance_list.append(instance_info)

        # Count by type and status (before pagination)
        type_counts = {}
        status_counts = {}
        for inst in instance_list:
            inst_type = inst["type"]
            type_counts[inst_type] = type_counts.get(inst_type, 0) + 1

            status = inst["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        total_instances = len(instance_list)

        # Apply pagination
        paginated_instances, pagination = self.apply_pagination(instance_list, limit, offset)

        return {
            "success": True,
            "instances": paginated_instances,
            "metadata": {
                "total_instances": total_instances,
                "type_counts": type_counts,
                "status_counts": status_counts,
            },
            "pagination": pagination
        }

    @tool_handler
    async def get_instance(
        self,
        instance_name: str,
        include_raw: bool = False
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific instance

        Args:
            instance_name: Name of the instance
            include_raw: Include full API response for debugging (default: false)

        Returns:
            Dictionary containing instance details
        """
        await self.ensure_initialized()

        # Query with id filter
        instances = await self.client.get(f"/virt/instance?id={instance_name}")

        if not instances:
            return {
                "success": False,
                "error": f"Instance '{instance_name}' not found"
            }

        inst = instances[0]
        memory_bytes = inst.get("memory", 0)
        memory_gb = round(memory_bytes / (1024**3), 2)

        result = {
            "success": True,
            "instance": {
                "id": inst.get("id"),
                "name": inst.get("name") or inst.get("id"),
                "type": inst.get("type"),
                "status": inst.get("status"),
                "cpu": inst.get("cpu"),
                "memory_gb": memory_gb,
                "memory_bytes": memory_bytes,
                "autostart": inst.get("autostart"),
                "image": inst.get("image"),
                "environment": inst.get("environment", {}),
            }
        }

        if include_raw:
            result["raw"] = inst

        return result

    @tool_handler
    async def start_instance(self, instance_name: str) -> Dict[str, Any]:
        """
        Start an Incus instance

        NOTE: The /virt/instance/start endpoint expects a plain string body!

        Args:
            instance_name: Name of the instance to start

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Check current state first
        instances = await self.client.get(f"/virt/instance?id={instance_name}")
        if not instances:
            return {
                "success": False,
                "error": f"Instance '{instance_name}' not found"
            }

        current_status = instances[0].get("status", "UNKNOWN")
        if current_status == "RUNNING":
            return {
                "success": True,
                "message": f"Instance '{instance_name}' is already running",
                "status": current_status
            }

        # Start the instance
        # NOTE: This endpoint expects a plain quoted string, not an object!
        result = await self.client.post_raw(
            "/virt/instance/start",
            f'"{instance_name}"'
        )

        # Poll for completion
        final_status = await self._wait_for_instance_status(
            instance_name, "RUNNING"
        )

        return {
            "success": final_status == "RUNNING",
            "instance_name": instance_name,
            "status": final_status,
            "message": (
                f"Instance '{instance_name}' started successfully"
                if final_status == "RUNNING"
                else f"Instance '{instance_name}' may still be starting "
                     f"(current status: {final_status})"
            )
        }

    @tool_handler
    async def stop_instance(
        self,
        instance_name: str,
        force: bool = False,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Stop an Incus instance

        Args:
            instance_name: Name of the instance to stop
            force: Force stop without graceful shutdown
            timeout: Timeout in seconds for graceful shutdown

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Check current state first
        instances = await self.client.get(f"/virt/instance?id={instance_name}")
        if not instances:
            return {
                "success": False,
                "error": f"Instance '{instance_name}' not found"
            }

        current_status = instances[0].get("status", "UNKNOWN")
        if current_status == "STOPPED":
            return {
                "success": True,
                "message": f"Instance '{instance_name}' is already stopped",
                "status": current_status
            }

        # Build request body
        body: Dict[str, Any] = {"id": instance_name}
        if force:
            body["force"] = True
        if timeout:
            body["timeout"] = timeout

        # Stop the instance
        result = await self.client.post("/virt/instance/stop", body)

        # Poll for completion
        final_status = await self._wait_for_instance_status(
            instance_name, "STOPPED"
        )

        return {
            "success": final_status == "STOPPED",
            "instance_name": instance_name,
            "status": final_status,
            "message": (
                f"Instance '{instance_name}' stopped successfully"
                if final_status == "STOPPED"
                else f"Instance '{instance_name}' may still be stopping "
                     f"(current status: {final_status})"
            )
        }

    @tool_handler
    async def restart_instance(self, instance_name: str) -> Dict[str, Any]:
        """
        Restart an Incus instance (stop then start)

        Args:
            instance_name: Name of the instance to restart

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Check if instance exists
        instances = await self.client.get(f"/virt/instance?id={instance_name}")
        if not instances:
            return {
                "success": False,
                "error": f"Instance '{instance_name}' not found"
            }

        initial_status = instances[0].get("status", "UNKNOWN")

        # Stop if running
        if initial_status == "RUNNING":
            await self.client.post("/virt/instance/stop", {"id": instance_name})
            await self._wait_for_instance_status(instance_name, "STOPPED")

        # Start the instance
        await self.client.post_raw("/virt/instance/start", f'"{instance_name}"')
        final_status = await self._wait_for_instance_status(
            instance_name, "RUNNING"
        )

        return {
            "success": final_status == "RUNNING",
            "instance_name": instance_name,
            "status": final_status,
            "message": (
                f"Instance '{instance_name}' restarted successfully"
                if final_status == "RUNNING"
                else f"Instance '{instance_name}' restart may still be in progress"
            )
        }

    @tool_handler
    async def update_instance(
        self,
        instance_name: str,
        cpu: Optional[str] = None,
        memory: Optional[int] = None,
        autostart: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update instance configuration

        NOTE: The instance should typically be stopped before updating.

        Args:
            instance_name: Name of the instance to update
            cpu: Number of CPU cores (as string, e.g., '4')
            memory: Memory in bytes (e.g., 8589934592 for 8GB)
            autostart: Whether to start instance on boot

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Check if instance exists
        instances = await self.client.get(f"/virt/instance?id={instance_name}")
        if not instances:
            return {
                "success": False,
                "error": f"Instance '{instance_name}' not found"
            }

        current = instances[0]
        was_running = current.get("status") == "RUNNING"

        # Build update body - only include provided fields
        update_body: Dict[str, Any] = {}
        if cpu is not None:
            update_body["cpu"] = cpu
        if memory is not None:
            update_body["memory"] = memory
        if autostart is not None:
            update_body["autostart"] = autostart

        if not update_body:
            return {
                "success": False,
                "error": "No update parameters provided"
            }

        # Update the instance
        result = await self.client.put(
            f"/virt/instance/id/{instance_name}",
            update_body
        )

        # Get updated state
        instances = await self.client.get(f"/virt/instance?id={instance_name}")
        updated = instances[0] if instances else {}

        return {
            "success": True,
            "instance_name": instance_name,
            "message": f"Instance '{instance_name}' configuration updated",
            "updated_values": update_body,
            "current_config": {
                "cpu": updated.get("cpu"),
                "memory": updated.get("memory"),
                "autostart": updated.get("autostart"),
            },
            "note": (
                "Instance may need restart for changes to take effect"
                if was_running else None
            )
        }

    @tool_handler
    async def list_instance_devices(self, instance_name: str) -> Dict[str, Any]:
        """
        List devices attached to an instance

        Args:
            instance_name: Name of the instance

        Returns:
            Dictionary containing list of attached devices
        """
        await self.ensure_initialized()

        # Get instance details
        instances = await self.client.get(f"/virt/instance?id={instance_name}")
        if not instances:
            return {
                "success": False,
                "error": f"Instance '{instance_name}' not found"
            }

        inst = instances[0]

        # Extract device information
        # TrueNAS returns devices in various formats depending on version
        devices = []

        # Try different device sources
        raw_devices = inst.get("devices", {})
        if isinstance(raw_devices, dict):
            for dev_name, dev_config in raw_devices.items():
                if isinstance(dev_config, dict):
                    devices.append({
                        "name": dev_name,
                        "type": dev_config.get("type", "UNKNOWN"),
                        "source": dev_config.get("source"),
                        "path": dev_config.get("path"),
                        "readonly": dev_config.get("readonly", False),
                        "config": dev_config
                    })
        elif isinstance(raw_devices, list):
            for dev in raw_devices:
                devices.append({
                    "name": dev.get("name", "unknown"),
                    "type": dev.get("type", "UNKNOWN"),
                    "source": dev.get("source"),
                    "path": dev.get("path"),
                    "readonly": dev.get("readonly", False),
                    "config": dev
                })

        return {
            "success": True,
            "instance_name": instance_name,
            "devices": devices,
            "metadata": {
                "device_count": len(devices)
            }
        }

    async def _wait_for_instance_status(
        self,
        instance_name: str,
        target_status: str,
        timeout: Optional[int] = None
    ) -> str:
        """
        Wait for an instance to reach a target status

        Args:
            instance_name: Name of the instance
            target_status: Status to wait for (e.g., "RUNNING", "STOPPED")
            timeout: Optional timeout in seconds

        Returns:
            Final status of the instance
        """
        timeout = timeout or self.INSTANCE_OPERATION_TIMEOUT
        max_attempts = timeout // self.POLL_INTERVAL

        for _ in range(max_attempts):
            try:
                instances = await self.client.get(
                    f"/virt/instance?id={instance_name}"
                )
                if instances:
                    current_status = instances[0].get("status", "UNKNOWN")

                    if current_status == target_status:
                        return current_status

                    # If we hit an error state, return immediately
                    if current_status == "ERROR":
                        return current_status

            except Exception as e:
                self.logger.warning(f"Error polling instance status: {e}")

            await asyncio.sleep(self.POLL_INTERVAL)

        # Return last known status
        try:
            instances = await self.client.get(
                f"/virt/instance?id={instance_name}"
            )
            if instances:
                return instances[0].get("status", "UNKNOWN")
        except Exception:
            pass

        return "UNKNOWN"
