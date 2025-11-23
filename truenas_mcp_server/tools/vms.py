"""
Virtual Machine management tools for TrueNAS
"""

from typing import Dict, Any, Optional, List
from .base import BaseTool, tool_handler


class VMTools(BaseTool):
    """Tools for managing TrueNAS Virtual Machines"""

    def get_tool_definitions(self) -> list:
        """Get tool definitions for VM management"""
        return [
            ("list_vms", self.list_vms,
             "List all virtual machines", {}),
            ("get_vm", self.get_vm,
             "Get detailed information about a virtual machine",
             {"vm_id": {"type": "integer", "required": True}}),
            ("start_vm", self.start_vm,
             "Start a virtual machine",
             {"vm_id": {"type": "integer", "required": True}}),
            ("stop_vm", self.stop_vm,
             "Stop a virtual machine",
             {"vm_id": {"type": "integer", "required": True},
              "force": {"type": "boolean", "required": False}}),
            ("restart_vm", self.restart_vm,
             "Restart a virtual machine",
             {"vm_id": {"type": "integer", "required": True}}),
            ("create_vm", self.create_vm,
             "Create a new virtual machine",
             {"name": {"type": "string", "required": True},
              "vcpus": {"type": "integer", "required": False},
              "memory": {"type": "integer", "required": False},
              "bootloader": {"type": "string", "required": False}}),
            ("delete_vm", self.delete_vm,
             "Delete a virtual machine",
             {"vm_id": {"type": "integer", "required": True},
              "force": {"type": "boolean", "required": False}}),
            ("clone_vm", self.clone_vm,
             "Clone a virtual machine",
             {"vm_id": {"type": "integer", "required": True},
              "name": {"type": "string", "required": True}}),
            ("get_vm_status", self.get_vm_status,
             "Get status of a virtual machine",
             {"vm_id": {"type": "integer", "required": True}}),
            ("list_vm_devices", self.list_vm_devices,
             "List devices attached to a VM",
             {"vm_id": {"type": "integer", "required": True}}),
            ("get_vm_console", self.get_vm_console,
             "Get VM console information",
             {"vm_id": {"type": "integer", "required": True}}),
            ("get_virtualization_status", self.get_virtualization_status,
             "Get virtualization support status", {}),
        ]

    @tool_handler
    async def list_vms(self) -> Dict[str, Any]:
        """
        List all virtual machines

        Returns:
            Dictionary containing list of VMs
        """
        await self.ensure_initialized()

        try:
            vms = await self.client.get("/vm")
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list VMs: {str(e)}"
            }

        vm_list = []
        for vm in vms:
            vm_info = {
                "id": vm.get("id"),
                "name": vm.get("name"),
                "description": vm.get("description"),
                "vcpus": vm.get("vcpus"),
                "memory": vm.get("memory"),
                "memory_formatted": self.format_size(vm.get("memory", 0) * 1024 * 1024),
                "autostart": vm.get("autostart"),
                "time": vm.get("time"),
                "bootloader": vm.get("bootloader"),
                "cores": vm.get("cores"),
                "threads": vm.get("threads"),
                "shutdown_timeout": vm.get("shutdown_timeout"),
                "cpu_mode": vm.get("cpu_mode"),
                "cpu_model": vm.get("cpu_model"),
                "machine_type": vm.get("machine_type"),
                "status": vm.get("status", {}).get("state") if isinstance(vm.get("status"), dict) else vm.get("status"),
                "com_port": vm.get("status", {}).get("com_port") if isinstance(vm.get("status"), dict) else None,
                "display": vm.get("display_available", False),
            }
            vm_list.append(vm_info)

        # Categorize by status
        running = [v for v in vm_list if v.get("status") in ["RUNNING", "running"]]
        stopped = [v for v in vm_list if v.get("status") in ["STOPPED", "stopped", None]]

        return {
            "success": True,
            "vms": vm_list,
            "metadata": {
                "total_vms": len(vm_list),
                "running_vms": len(running),
                "stopped_vms": len(stopped),
                "total_vcpus": sum(v.get("vcpus", 0) for v in running),
                "total_memory_mb": sum(v.get("memory", 0) for v in running),
            }
        }

    @tool_handler
    async def get_vm(self, vm_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a virtual machine

        Args:
            vm_id: ID of the virtual machine

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

        # Get devices
        devices = vm.get("devices", [])
        device_summary = {
            "disks": [],
            "nics": [],
            "cdrom": [],
            "display": [],
            "raw": [],
            "pci": [],
            "usb": []
        }

        for device in devices:
            dtype = device.get("dtype", "").lower()
            device_info = {
                "id": device.get("id"),
                "order": device.get("order"),
                "attributes": device.get("attributes", {})
            }

            if dtype == "disk":
                device_summary["disks"].append({
                    **device_info,
                    "path": device.get("attributes", {}).get("path"),
                    "type": device.get("attributes", {}).get("type"),
                    "logical_sectorsize": device.get("attributes", {}).get("logical_sectorsize"),
                    "physical_sectorsize": device.get("attributes", {}).get("physical_sectorsize"),
                })
            elif dtype == "nic":
                device_summary["nics"].append({
                    **device_info,
                    "mac": device.get("attributes", {}).get("mac"),
                    "type": device.get("attributes", {}).get("type"),
                    "nic_attach": device.get("attributes", {}).get("nic_attach"),
                })
            elif dtype == "cdrom":
                device_summary["cdrom"].append({
                    **device_info,
                    "path": device.get("attributes", {}).get("path"),
                })
            elif dtype == "display":
                device_summary["display"].append({
                    **device_info,
                    "type": device.get("attributes", {}).get("type"),
                    "port": device.get("attributes", {}).get("port"),
                    "resolution": device.get("attributes", {}).get("resolution"),
                    "web": device.get("attributes", {}).get("web"),
                })
            elif dtype == "raw":
                device_summary["raw"].append(device_info)
            elif dtype == "pci":
                device_summary["pci"].append(device_info)
            elif dtype == "usb":
                device_summary["usb"].append(device_info)

        return {
            "success": True,
            "vm": {
                "id": vm.get("id"),
                "name": vm.get("name"),
                "description": vm.get("description"),
                "vcpus": vm.get("vcpus"),
                "cores": vm.get("cores"),
                "threads": vm.get("threads"),
                "memory": vm.get("memory"),
                "memory_formatted": self.format_size(vm.get("memory", 0) * 1024 * 1024),
                "min_memory": vm.get("min_memory"),
                "autostart": vm.get("autostart"),
                "time": vm.get("time"),
                "bootloader": vm.get("bootloader"),
                "shutdown_timeout": vm.get("shutdown_timeout"),
                "cpu_mode": vm.get("cpu_mode"),
                "cpu_model": vm.get("cpu_model"),
                "machine_type": vm.get("machine_type"),
                "arch_type": vm.get("arch_type"),
                "uuid": vm.get("uuid"),
                "hide_from_msr": vm.get("hide_from_msr"),
                "ensure_display_device": vm.get("ensure_display_device"),
                "status": vm.get("status"),
                "devices": device_summary,
            }
        }

    @tool_handler
    async def start_vm(self, vm_id: int, overcommit: bool = False) -> Dict[str, Any]:
        """
        Start a virtual machine

        Args:
            vm_id: ID of the VM to start
            overcommit: Allow memory overcommit

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        try:
            result = await self.client.post(f"/vm/id/{vm_id}/start",
                                           {"overcommit": overcommit})
            return {
                "success": True,
                "message": f"VM {vm_id} started successfully",
                "vm_id": vm_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start VM: {str(e)}"
            }

    @tool_handler
    async def stop_vm(self, vm_id: int, force: bool = False) -> Dict[str, Any]:
        """
        Stop a virtual machine

        Args:
            vm_id: ID of the VM to stop
            force: Force stop (power off) the VM

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        try:
            if force:
                result = await self.client.post(f"/vm/id/{vm_id}/poweroff")
            else:
                result = await self.client.post(f"/vm/id/{vm_id}/stop")
            return {
                "success": True,
                "message": f"VM {vm_id} {'powered off' if force else 'stopped'}",
                "vm_id": vm_id,
                "force": force
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop VM: {str(e)}"
            }

    @tool_handler
    async def restart_vm(self, vm_id: int) -> Dict[str, Any]:
        """
        Restart a virtual machine

        Args:
            vm_id: ID of the VM to restart

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        try:
            result = await self.client.post(f"/vm/id/{vm_id}/restart")
            return {
                "success": True,
                "message": f"VM {vm_id} restarted",
                "vm_id": vm_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to restart VM: {str(e)}"
            }

    @tool_handler
    async def create_vm(
        self,
        name: str,
        vcpus: int = 1,
        memory: int = 1024,
        bootloader: str = "UEFI",
        autostart: bool = False,
        description: str = "",
        cpu_mode: str = "CUSTOM",
        machine_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new virtual machine

        Args:
            name: Name of the VM
            vcpus: Number of virtual CPUs
            memory: Memory in MB
            bootloader: Bootloader type (UEFI, UEFI_CSM, or GRUB)
            autostart: Start VM on system boot
            description: VM description
            cpu_mode: CPU mode (CUSTOM, HOST_MODEL, HOST_PASSTHROUGH)
            machine_type: Machine type (pc-q35-* or pc-i440fx-*)

        Returns:
            Dictionary containing created VM
        """
        await self.ensure_initialized()

        vm_data = {
            "name": name,
            "vcpus": vcpus,
            "memory": memory,
            "bootloader": bootloader,
            "autostart": autostart,
            "description": description,
            "cpu_mode": cpu_mode,
        }

        if machine_type:
            vm_data["machine_type"] = machine_type

        try:
            created = await self.client.post("/vm", vm_data)
            return {
                "success": True,
                "message": f"VM '{name}' created successfully",
                "vm": {
                    "id": created.get("id"),
                    "name": created.get("name"),
                    "vcpus": created.get("vcpus"),
                    "memory": created.get("memory"),
                    "bootloader": created.get("bootloader"),
                },
                "next_steps": [
                    "Add a disk device to the VM",
                    "Add a network interface (NIC)",
                    "Optionally add a CDROM for installation media",
                    "Add a display device for console access",
                    "Start the VM"
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create VM: {str(e)}"
            }

    @tool_handler
    async def delete_vm(self, vm_id: int, force: bool = False) -> Dict[str, Any]:
        """
        Delete a virtual machine

        Args:
            vm_id: ID of the VM to delete
            force: Force deletion even if VM is running

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        # Check if destructive operations are allowed
        if not self.settings.enable_destructive_operations:
            return {
                "success": False,
                "error": "Destructive operations are disabled. Enable TRUENAS_ENABLE_DESTRUCTIVE_OPS to allow VM deletion."
            }

        try:
            # Get VM info first
            vm = await self.client.get(f"/vm/id/{vm_id}")
            vm_name = vm.get("name", f"ID {vm_id}")

            # Stop VM if running and force is True
            status = vm.get("status", {})
            if isinstance(status, dict) and status.get("state") == "RUNNING":
                if force:
                    await self.client.post(f"/vm/id/{vm_id}/poweroff")
                else:
                    return {
                        "success": False,
                        "error": f"VM '{vm_name}' is running. Stop it first or use force=True"
                    }

            await self.client.delete(f"/vm/id/{vm_id}")
            return {
                "success": True,
                "message": f"VM '{vm_name}' deleted successfully",
                "vm_id": vm_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete VM: {str(e)}"
            }

    @tool_handler
    async def clone_vm(self, vm_id: int, name: str) -> Dict[str, Any]:
        """
        Clone a virtual machine

        Args:
            vm_id: ID of the VM to clone
            name: Name for the cloned VM

        Returns:
            Dictionary containing cloned VM info
        """
        await self.ensure_initialized()

        try:
            cloned = await self.client.post(f"/vm/id/{vm_id}/clone",
                                           {"name": name})
            return {
                "success": True,
                "message": f"VM cloned to '{name}'",
                "original_vm_id": vm_id,
                "cloned_vm": {
                    "id": cloned.get("id") if isinstance(cloned, dict) else cloned,
                    "name": name
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to clone VM: {str(e)}"
            }

    @tool_handler
    async def get_vm_status(self, vm_id: int) -> Dict[str, Any]:
        """
        Get status of a virtual machine

        Args:
            vm_id: ID of the VM

        Returns:
            Dictionary containing VM status
        """
        await self.ensure_initialized()

        try:
            status = await self.client.post(f"/vm/id/{vm_id}/status")

            return {
                "success": True,
                "vm_id": vm_id,
                "status": {
                    "state": status.get("state"),
                    "pid": status.get("pid"),
                    "domain_state": status.get("domain_state"),
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get VM status: {str(e)}"
            }

    @tool_handler
    async def list_vm_devices(self, vm_id: int) -> Dict[str, Any]:
        """
        List devices attached to a VM

        Args:
            vm_id: ID of the VM

        Returns:
            Dictionary containing VM devices
        """
        await self.ensure_initialized()

        try:
            # Get VM details which include devices
            vm = await self.client.get(f"/vm/id/{vm_id}")
            devices = vm.get("devices", [])

            device_list = []
            for device in devices:
                device_info = {
                    "id": device.get("id"),
                    "dtype": device.get("dtype"),
                    "order": device.get("order"),
                    "vm": device.get("vm"),
                    "attributes": device.get("attributes", {})
                }
                device_list.append(device_info)

            # Group by type
            by_type = {}
            for device in device_list:
                dtype = device.get("dtype", "unknown")
                if dtype not in by_type:
                    by_type[dtype] = []
                by_type[dtype].append(device)

            return {
                "success": True,
                "vm_id": vm_id,
                "devices": device_list,
                "by_type": by_type,
                "metadata": {
                    "total_devices": len(device_list),
                    "device_types": list(by_type.keys())
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list VM devices: {str(e)}"
            }

    @tool_handler
    async def get_vm_console(self, vm_id: int) -> Dict[str, Any]:
        """
        Get VM console information

        Args:
            vm_id: ID of the VM

        Returns:
            Dictionary containing console info
        """
        await self.ensure_initialized()

        try:
            # Get VM details for display devices
            vm = await self.client.get(f"/vm/id/{vm_id}")
            status = vm.get("status", {})

            # Find display devices
            displays = []
            for device in vm.get("devices", []):
                if device.get("dtype") == "DISPLAY":
                    attrs = device.get("attributes", {})
                    displays.append({
                        "id": device.get("id"),
                        "type": attrs.get("type"),
                        "port": attrs.get("port"),
                        "resolution": attrs.get("resolution"),
                        "web": attrs.get("web"),
                        "web_port": attrs.get("web_port"),
                        "wait": attrs.get("wait"),
                        "password": "***" if attrs.get("password") else None
                    })

            # Get serial port info
            com_port = status.get("com_port") if isinstance(status, dict) else None

            return {
                "success": True,
                "vm_id": vm_id,
                "console": {
                    "displays": displays,
                    "serial_port": com_port,
                    "state": status.get("state") if isinstance(status, dict) else status,
                },
                "access_info": {
                    "vnc_port": displays[0].get("port") if displays else None,
                    "web_vnc": displays[0].get("web") if displays else None,
                    "serial": f"Serial console available on port {com_port}" if com_port else None
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get VM console info: {str(e)}"
            }

    @tool_handler
    async def get_virtualization_status(self) -> Dict[str, Any]:
        """
        Get virtualization support status

        Returns:
            Dictionary containing virtualization info
        """
        await self.ensure_initialized()

        try:
            # Check VM capability
            vm_flags = await self.client.get("/vm/flags")
        except Exception:
            vm_flags = {}

        try:
            # Get general system info for virtualization support
            system_info = await self.client.get("/system/info")
            cpu_flags = system_info.get("cpu_flags", []) if system_info else []
        except Exception:
            cpu_flags = []

        # Check for virtualization support
        has_vmx = "vmx" in [f.lower() for f in cpu_flags]
        has_svm = "svm" in [f.lower() for f in cpu_flags]

        return {
            "success": True,
            "virtualization": {
                "supported": has_vmx or has_svm or bool(vm_flags),
                "type": "Intel VT-x" if has_vmx else ("AMD-V" if has_svm else "Unknown"),
                "intel_vtx": has_vmx,
                "amd_v": has_svm,
                "flags": vm_flags,
                "cpu_features": cpu_flags[:20] if cpu_flags else []  # Limit output
            }
        }
