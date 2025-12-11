"""
TrueNAS Legacy VM management tools (bhyve-based)

Provides tools for managing legacy bhyve VMs on TrueNAS SCALE.
Uses the /api/v2.0/vm endpoints.

NOTE: For new deployments, consider using Incus VMs (/api/v2.0/virt/instance)
instead. Legacy VMs are maintained for backward compatibility.
"""

import asyncio
from typing import Any, Dict, List, Optional

from .base import BaseTool, tool_handler


class LegacyVMTools(BaseTool):
    """Tools for managing TrueNAS legacy bhyve VMs"""

    # Timeout for VM operations
    VM_OPERATION_TIMEOUT = 120  # seconds
    POLL_INTERVAL = 5  # seconds

    def get_tool_definitions(self) -> list:
        """Get tool definitions for legacy VM management"""
        return [
            ("list_legacy_vms", self.list_legacy_vms,
             "List all legacy bhyve VMs", {}),
            ("get_legacy_vm", self.get_legacy_vm,
             "Get detailed information about a legacy VM",
             {"vm_id": {"type": "integer", "required": True,
                       "description": "Numeric ID of the VM"}}),
            ("start_legacy_vm", self.start_legacy_vm,
             "Start a legacy VM",
             {"vm_id": {"type": "integer", "required": True,
                       "description": "Numeric ID of the VM to start"}}),
            ("stop_legacy_vm", self.stop_legacy_vm,
             "Stop a legacy VM",
             {"vm_id": {"type": "integer", "required": True,
                       "description": "Numeric ID of the VM to stop"},
              "force": {"type": "boolean", "required": False,
                       "description": "Force stop (poweroff) without graceful shutdown"}}),
            ("restart_legacy_vm", self.restart_legacy_vm,
             "Restart a legacy VM",
             {"vm_id": {"type": "integer", "required": True,
                       "description": "Numeric ID of the VM to restart"}}),
            ("update_legacy_vm", self.update_legacy_vm,
             "Update legacy VM configuration",
             {"vm_id": {"type": "integer", "required": True,
                       "description": "Numeric ID of the VM to update"},
              "name": {"type": "string", "required": False,
                      "description": "New VM name"},
              "vcpus": {"type": "integer", "required": False,
                       "description": "Number of virtual CPUs"},
              "memory": {"type": "integer", "required": False,
                        "description": "Memory in MB"},
              "autostart": {"type": "boolean", "required": False,
                           "description": "Start on boot"}}),
            ("get_legacy_vm_status", self.get_legacy_vm_status,
             "Get the runtime status of a legacy VM",
             {"vm_id": {"type": "integer", "required": True,
                       "description": "Numeric ID of the VM"}}),
        ]

    @tool_handler
    async def list_legacy_vms(self) -> Dict[str, Any]:
        """
        List all legacy bhyve VMs

        Returns:
            Dictionary containing list of VMs with their status
        """
        await self.ensure_initialized()

        vms = await self.client.get("/vm")

        vm_list = []
        for vm in vms:
            # Get status for each VM
            vm_id = vm.get("id")
            status = await self._get_vm_status(vm_id)

            vm_info = {
                "id": vm_id,
                "name": vm.get("name"),
                "description": vm.get("description"),
                "vcpus": vm.get("vcpus", 1),
                "memory_mb": vm.get("memory", 0),
                "autostart": vm.get("autostart", False),
                "status": status,
                "bootloader": vm.get("bootloader"),
            }
            vm_list.append(vm_info)

        # Count by status
        status_counts = {}
        for vm in vm_list:
            status = vm["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "success": True,
            "vms": vm_list,
            "metadata": {
                "total_vms": len(vm_list),
                "status_counts": status_counts,
            }
        }

    @tool_handler
    async def get_legacy_vm(self, vm_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a legacy VM

        Args:
            vm_id: Numeric ID of the VM

        Returns:
            Dictionary containing VM details
        """
        await self.ensure_initialized()

        try:
            vm = await self.client.get(f"/vm/id/{vm_id}")
        except Exception:
            return {
                "success": False,
                "error": f"VM with ID {vm_id} not found"
            }

        # Get runtime status
        status = await self._get_vm_status(vm_id)

        # Parse device information
        devices = []
        for device in vm.get("devices", []):
            devices.append({
                "id": device.get("id"),
                "type": device.get("dtype"),
                "order": device.get("order", 1000),
                "attributes": device.get("attributes", {}),
            })

        return {
            "success": True,
            "vm": {
                "id": vm.get("id"),
                "name": vm.get("name"),
                "description": vm.get("description"),
                "vcpus": vm.get("vcpus"),
                "memory_mb": vm.get("memory"),
                "min_memory": vm.get("min_memory"),
                "autostart": vm.get("autostart"),
                "bootloader": vm.get("bootloader"),
                "time": vm.get("time"),
                "shutdown_timeout": vm.get("shutdown_timeout"),
                "cpu_mode": vm.get("cpu_mode"),
                "cpu_model": vm.get("cpu_model"),
                "status": status,
                "devices": devices,
            },
            "raw": vm  # Include full response for debugging
        }

    @tool_handler
    async def start_legacy_vm(self, vm_id: int) -> Dict[str, Any]:
        """
        Start a legacy VM

        Args:
            vm_id: Numeric ID of the VM to start

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Check current status
        status = await self._get_vm_status(vm_id)
        if status == "RUNNING":
            return {
                "success": True,
                "message": f"VM {vm_id} is already running",
                "status": status
            }

        # Start the VM
        try:
            result = await self.client.post(f"/vm/id/{vm_id}/start")
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start VM {vm_id}: {str(e)}"
            }

        # Poll for running state
        final_status = await self._wait_for_vm_status(vm_id, "RUNNING")

        return {
            "success": final_status == "RUNNING",
            "vm_id": vm_id,
            "status": final_status,
            "message": (
                f"VM {vm_id} started successfully"
                if final_status == "RUNNING"
                else f"VM {vm_id} may still be starting (current status: {final_status})"
            )
        }

    @tool_handler
    async def stop_legacy_vm(
        self,
        vm_id: int,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Stop a legacy VM

        Args:
            vm_id: Numeric ID of the VM to stop
            force: Force stop (poweroff) without graceful shutdown

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Check current status
        status = await self._get_vm_status(vm_id)
        if status == "STOPPED":
            return {
                "success": True,
                "message": f"VM {vm_id} is already stopped",
                "status": status
            }

        # Stop the VM
        endpoint = f"/vm/id/{vm_id}/stop"
        body = {}
        if force:
            body["force"] = True

        try:
            result = await self.client.post(endpoint, body if body else None)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop VM {vm_id}: {str(e)}"
            }

        # Poll for stopped state
        final_status = await self._wait_for_vm_status(vm_id, "STOPPED")

        return {
            "success": final_status == "STOPPED",
            "vm_id": vm_id,
            "status": final_status,
            "message": (
                f"VM {vm_id} stopped successfully"
                if final_status == "STOPPED"
                else f"VM {vm_id} may still be stopping (current status: {final_status})"
            )
        }

    @tool_handler
    async def restart_legacy_vm(self, vm_id: int) -> Dict[str, Any]:
        """
        Restart a legacy VM

        Args:
            vm_id: Numeric ID of the VM to restart

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Check if VM exists
        try:
            vm = await self.client.get(f"/vm/id/{vm_id}")
        except Exception:
            return {
                "success": False,
                "error": f"VM with ID {vm_id} not found"
            }

        initial_status = await self._get_vm_status(vm_id)

        # Stop if running
        if initial_status == "RUNNING":
            try:
                await self.client.post(f"/vm/id/{vm_id}/stop")
                await self._wait_for_vm_status(vm_id, "STOPPED")
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to stop VM {vm_id}: {str(e)}"
                }

        # Start the VM
        try:
            await self.client.post(f"/vm/id/{vm_id}/start")
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start VM {vm_id}: {str(e)}"
            }

        final_status = await self._wait_for_vm_status(vm_id, "RUNNING")

        return {
            "success": final_status == "RUNNING",
            "vm_id": vm_id,
            "status": final_status,
            "message": (
                f"VM {vm_id} restarted successfully"
                if final_status == "RUNNING"
                else f"VM {vm_id} restart may still be in progress"
            )
        }

    @tool_handler
    async def update_legacy_vm(
        self,
        vm_id: int,
        name: Optional[str] = None,
        vcpus: Optional[int] = None,
        memory: Optional[int] = None,
        autostart: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update legacy VM configuration

        NOTE: Some changes may require the VM to be stopped first.

        Args:
            vm_id: Numeric ID of the VM to update
            name: New VM name
            vcpus: Number of virtual CPUs
            memory: Memory in MB
            autostart: Start on boot

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Check if VM exists
        try:
            vm = await self.client.get(f"/vm/id/{vm_id}")
        except Exception:
            return {
                "success": False,
                "error": f"VM with ID {vm_id} not found"
            }

        was_running = await self._get_vm_status(vm_id) == "RUNNING"

        # Build update body - only include provided fields
        update_body: Dict[str, Any] = {}
        if name is not None:
            update_body["name"] = name
        if vcpus is not None:
            update_body["vcpus"] = vcpus
        if memory is not None:
            update_body["memory"] = memory
        if autostart is not None:
            update_body["autostart"] = autostart

        if not update_body:
            return {
                "success": False,
                "error": "No update parameters provided"
            }

        # Update the VM
        try:
            result = await self.client.put(f"/vm/id/{vm_id}", update_body)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update VM {vm_id}: {str(e)}"
            }

        # Get updated VM info
        try:
            updated_vm = await self.client.get(f"/vm/id/{vm_id}")
        except Exception:
            updated_vm = {}

        return {
            "success": True,
            "vm_id": vm_id,
            "message": f"VM {vm_id} configuration updated",
            "updated_values": update_body,
            "current_config": {
                "name": updated_vm.get("name"),
                "vcpus": updated_vm.get("vcpus"),
                "memory_mb": updated_vm.get("memory"),
                "autostart": updated_vm.get("autostart"),
            },
            "note": (
                "VM may need restart for CPU/memory changes to take effect"
                if was_running and (vcpus or memory) else None
            )
        }

    @tool_handler
    async def get_legacy_vm_status(self, vm_id: int) -> Dict[str, Any]:
        """
        Get the runtime status of a legacy VM

        Args:
            vm_id: Numeric ID of the VM

        Returns:
            Dictionary containing VM status
        """
        await self.ensure_initialized()

        status = await self._get_vm_status(vm_id)

        return {
            "success": True,
            "vm_id": vm_id,
            "status": status
        }

    async def _get_vm_status(self, vm_id: int) -> str:
        """
        Get the status of a VM

        Args:
            vm_id: Numeric ID of the VM

        Returns:
            Status string (RUNNING, STOPPED, etc.)
        """
        try:
            result = await self.client.get(f"/vm/id/{vm_id}/status")
            if isinstance(result, dict):
                return result.get("state", "UNKNOWN")
            return str(result) if result else "UNKNOWN"
        except Exception as e:
            self.logger.warning(f"Failed to get VM {vm_id} status: {e}")
            return "UNKNOWN"

    async def _wait_for_vm_status(
        self,
        vm_id: int,
        target_status: str,
        timeout: Optional[int] = None
    ) -> str:
        """
        Wait for a VM to reach a target status

        Args:
            vm_id: Numeric ID of the VM
            target_status: Status to wait for (e.g., "RUNNING", "STOPPED")
            timeout: Optional timeout in seconds

        Returns:
            Final status of the VM
        """
        timeout = timeout or self.VM_OPERATION_TIMEOUT
        max_attempts = timeout // self.POLL_INTERVAL

        for _ in range(max_attempts):
            status = await self._get_vm_status(vm_id)

            if status == target_status:
                return status

            # If we hit an error, return immediately
            if status == "ERROR":
                return status

            await asyncio.sleep(self.POLL_INTERVAL)

        # Return last known status
        return await self._get_vm_status(vm_id)
