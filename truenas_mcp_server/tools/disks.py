"""
Disk management tools for TrueNAS
"""

from typing import Dict, Any, Optional, List
from .base import BaseTool, tool_handler


class DiskTools(BaseTool):
    """Tools for managing TrueNAS disks and SMART monitoring"""

    def get_tool_definitions(self) -> list:
        """Get tool definitions for disk management"""
        return [
            ("list_disks", self.list_disks,
             "List all disks in the system", {}),
            ("get_disk", self.get_disk,
             "Get detailed information about a specific disk",
             {"disk_name": {"type": "string", "required": True}}),
            ("get_disk_smart", self.get_disk_smart,
             "Get SMART data for a disk",
             {"disk_name": {"type": "string", "required": True}}),
            ("run_smart_test", self.run_smart_test,
             "Run a SMART test on a disk",
             {"disk_name": {"type": "string", "required": True},
              "test_type": {"type": "string", "required": False}}),
            ("get_smart_test_results", self.get_smart_test_results,
             "Get SMART test results for a disk",
             {"disk_name": {"type": "string", "required": True}}),
            ("list_unused_disks", self.list_unused_disks,
             "List disks not assigned to any pool", {}),
            ("get_disk_temperatures", self.get_disk_temperatures,
             "Get temperature readings for all disks", {}),
            ("wipe_disk", self.wipe_disk,
             "Wipe a disk (destructive)",
             {"disk_name": {"type": "string", "required": True},
              "method": {"type": "string", "required": False}}),
        ]

    @tool_handler
    async def list_disks(self) -> Dict[str, Any]:
        """
        List all disks in the system

        Returns:
            Dictionary containing list of disks
        """
        await self.ensure_initialized()

        disks = await self.client.get("/disk")

        disk_list = []
        for disk in disks:
            disk_info = {
                "name": disk.get("name"),
                "devname": disk.get("devname"),
                "serial": disk.get("serial"),
                "model": disk.get("model"),
                "size": self.format_size(disk.get("size", 0)),
                "size_bytes": disk.get("size", 0),
                "type": disk.get("type"),
                "rotationrate": disk.get("rotationrate"),
                "is_ssd": disk.get("rotationrate") == 0 or disk.get("type") == "SSD",
                "hddstandby": disk.get("hddstandby"),
                "advpowermgmt": disk.get("advpowermgmt"),
                "togglesmart": disk.get("togglesmart"),
                "smartoptions": disk.get("smartoptions"),
                "description": disk.get("description"),
                "transfermode": disk.get("transfermode"),
                "pool": disk.get("pool"),
                "enclosure": disk.get("enclosure"),
                "expiretime": disk.get("expiretime"),
                "passwd": "***" if disk.get("passwd") else None,
                "supports_smart": disk.get("supports_smart", True),
            }
            disk_list.append(disk_info)

        # Calculate statistics
        total_capacity = sum(d.get("size_bytes", 0) for d in disk_list)
        ssd_count = sum(1 for d in disk_list if d["is_ssd"])
        hdd_count = len(disk_list) - ssd_count

        return {
            "success": True,
            "disks": disk_list,
            "metadata": {
                "total_disks": len(disk_list),
                "ssd_count": ssd_count,
                "hdd_count": hdd_count,
                "total_capacity": self.format_size(total_capacity),
                "total_capacity_bytes": total_capacity,
                "smart_enabled": sum(1 for d in disk_list if d.get("togglesmart"))
            }
        }

    @tool_handler
    async def get_disk(self, disk_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific disk

        Args:
            disk_name: Name of the disk (e.g., "sda", "da0")

        Returns:
            Dictionary containing disk details
        """
        await self.ensure_initialized()

        disks = await self.client.get("/disk")

        target_disk = None
        for disk in disks:
            if disk.get("name") == disk_name or disk.get("devname") == disk_name:
                target_disk = disk
                break

        if not target_disk:
            return {
                "success": False,
                "error": f"Disk '{disk_name}' not found"
            }

        return {
            "success": True,
            "disk": {
                "name": target_disk.get("name"),
                "devname": target_disk.get("devname"),
                "identifier": target_disk.get("identifier"),
                "serial": target_disk.get("serial"),
                "lunid": target_disk.get("lunid"),
                "model": target_disk.get("model"),
                "subsystem": target_disk.get("subsystem"),
                "number": target_disk.get("number"),
                "size": self.format_size(target_disk.get("size", 0)),
                "size_bytes": target_disk.get("size", 0),
                "type": target_disk.get("type"),
                "rotationrate": target_disk.get("rotationrate"),
                "is_ssd": target_disk.get("rotationrate") == 0,
                "hddstandby": target_disk.get("hddstandby"),
                "advpowermgmt": target_disk.get("advpowermgmt"),
                "togglesmart": target_disk.get("togglesmart"),
                "smartoptions": target_disk.get("smartoptions"),
                "description": target_disk.get("description"),
                "transfermode": target_disk.get("transfermode"),
                "pool": target_disk.get("pool"),
                "enclosure": target_disk.get("enclosure"),
                "supports_smart": target_disk.get("supports_smart", True),
                "zfs_guid": target_disk.get("zfs_guid"),
                "bus": target_disk.get("bus"),
            }
        }

    @tool_handler
    async def get_disk_smart(self, disk_name: str) -> Dict[str, Any]:
        """
        Get SMART data for a disk

        Args:
            disk_name: Name of the disk

        Returns:
            Dictionary containing SMART data
        """
        await self.ensure_initialized()

        try:
            smart_data = await self.client.post("/smart/test/results", {"disk": disk_name})
        except Exception:
            smart_data = []

        try:
            # Get disk temperature
            temps = await self.client.get("/disk/temperatures")
            temperature = temps.get(disk_name) if isinstance(temps, dict) else None
        except Exception:
            temperature = None

        # Try to get current SMART attributes
        try:
            disk_query = await self.client.post(
                "/disk/smart_attributes",
                [disk_name]
            )
            smart_attrs = disk_query.get(disk_name, {}) if isinstance(disk_query, dict) else {}
        except Exception:
            smart_attrs = {}

        return {
            "success": True,
            "disk": disk_name,
            "smart": {
                "temperature": temperature,
                "attributes": smart_attrs,
                "test_results": smart_data if isinstance(smart_data, list) else []
            }
        }

    @tool_handler
    async def run_smart_test(
        self,
        disk_name: str,
        test_type: str = "SHORT"
    ) -> Dict[str, Any]:
        """
        Run a SMART test on a disk

        Args:
            disk_name: Name of the disk
            test_type: Type of test (SHORT, LONG, CONVEYANCE, OFFLINE)

        Returns:
            Dictionary containing test initiation result
        """
        await self.ensure_initialized()

        # Validate test type
        valid_types = ["SHORT", "LONG", "CONVEYANCE", "OFFLINE"]
        test_type = test_type.upper()
        if test_type not in valid_types:
            return {
                "success": False,
                "error": f"Invalid test type. Must be one of: {', '.join(valid_types)}"
            }

        try:
            result = await self.client.post(
                "/smart/test",
                {"disks": [disk_name], "type": test_type}
            )

            return {
                "success": True,
                "message": f"SMART {test_type} test started on disk '{disk_name}'",
                "disk": disk_name,
                "test_type": test_type,
                "note": "Test running in background. Use get_smart_test_results to check progress."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start SMART test: {str(e)}"
            }

    @tool_handler
    async def get_smart_test_results(self, disk_name: str) -> Dict[str, Any]:
        """
        Get SMART test results for a disk

        Args:
            disk_name: Name of the disk

        Returns:
            Dictionary containing test results
        """
        await self.ensure_initialized()

        try:
            results = await self.client.post(
                "/smart/test/results",
                {"disk": disk_name}
            )

            return {
                "success": True,
                "disk": disk_name,
                "test_results": results if isinstance(results, list) else []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get SMART test results: {str(e)}"
            }

    @tool_handler
    async def list_unused_disks(self) -> Dict[str, Any]:
        """
        List disks not assigned to any pool

        Returns:
            Dictionary containing list of unused disks
        """
        await self.ensure_initialized()

        try:
            unused = await self.client.post("/disk/get_unused")
        except Exception:
            # Fallback: get all disks and filter
            disks = await self.client.get("/disk")
            unused = [d for d in disks if not d.get("pool")]

        disk_list = []
        for disk in unused:
            disk_info = {
                "name": disk.get("name"),
                "devname": disk.get("devname"),
                "serial": disk.get("serial"),
                "model": disk.get("model"),
                "size": self.format_size(disk.get("size", 0)),
                "size_bytes": disk.get("size", 0),
                "type": disk.get("type"),
                "is_ssd": disk.get("rotationrate") == 0,
            }
            disk_list.append(disk_info)

        total_capacity = sum(d.get("size_bytes", 0) for d in disk_list)

        return {
            "success": True,
            "unused_disks": disk_list,
            "metadata": {
                "count": len(disk_list),
                "total_capacity": self.format_size(total_capacity),
                "total_capacity_bytes": total_capacity
            }
        }

    @tool_handler
    async def get_disk_temperatures(self) -> Dict[str, Any]:
        """
        Get temperature readings for all disks

        Returns:
            Dictionary containing disk temperatures
        """
        await self.ensure_initialized()

        try:
            temps = await self.client.get("/disk/temperatures")
        except Exception:
            temps = {}

        # Get disk info for context
        disks = await self.client.get("/disk")
        disk_map = {d.get("name"): d for d in disks}

        temp_list = []
        for disk_name, temp in temps.items() if isinstance(temps, dict) else []:
            disk_info = disk_map.get(disk_name, {})
            temp_info = {
                "disk": disk_name,
                "temperature_c": temp,
                "temperature_f": round(temp * 9/5 + 32, 1) if temp else None,
                "model": disk_info.get("model"),
                "serial": disk_info.get("serial"),
                "status": self._get_temp_status(temp)
            }
            temp_list.append(temp_info)

        # Sort by temperature (highest first)
        temp_list.sort(key=lambda x: x.get("temperature_c") or 0, reverse=True)

        return {
            "success": True,
            "temperatures": temp_list,
            "metadata": {
                "disk_count": len(temp_list),
                "max_temp": max((t.get("temperature_c") or 0) for t in temp_list) if temp_list else None,
                "min_temp": min((t.get("temperature_c") or 999) for t in temp_list if t.get("temperature_c")) if temp_list else None,
                "avg_temp": round(sum(t.get("temperature_c") or 0 for t in temp_list) / len(temp_list), 1) if temp_list else None,
                "overheating_disks": sum(1 for t in temp_list if t.get("status") == "CRITICAL")
            }
        }

    def _get_temp_status(self, temp: Optional[int]) -> str:
        """Get temperature status based on value"""
        if temp is None:
            return "UNKNOWN"
        if temp < 35:
            return "COOL"
        elif temp < 45:
            return "NORMAL"
        elif temp < 55:
            return "WARM"
        elif temp < 65:
            return "HOT"
        else:
            return "CRITICAL"

    @tool_handler
    async def wipe_disk(
        self,
        disk_name: str,
        method: str = "QUICK",
        sync_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Wipe a disk (destructive operation)

        Args:
            disk_name: Name of the disk to wipe
            method: Wipe method (QUICK, FULL, FULL_RANDOM)
            sync_mode: Whether to wait for completion

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        # Check if destructive operations are allowed
        if not self.settings.enable_destructive_operations:
            return {
                "success": False,
                "error": "Destructive operations are disabled. Enable TRUENAS_ENABLE_DESTRUCTIVE_OPS to allow disk wiping."
            }

        # Verify disk exists and is not in a pool
        disks = await self.client.get("/disk")
        target_disk = None
        for disk in disks:
            if disk.get("name") == disk_name or disk.get("devname") == disk_name:
                target_disk = disk
                break

        if not target_disk:
            return {
                "success": False,
                "error": f"Disk '{disk_name}' not found"
            }

        if target_disk.get("pool"):
            return {
                "success": False,
                "error": f"Cannot wipe disk '{disk_name}' - it is part of pool '{target_disk.get('pool')}'"
            }

        # Validate method
        valid_methods = ["QUICK", "FULL", "FULL_RANDOM"]
        method = method.upper()
        if method not in valid_methods:
            return {
                "success": False,
                "error": f"Invalid wipe method. Must be one of: {', '.join(valid_methods)}"
            }

        try:
            result = await self.client.post(
                "/disk/wipe",
                {"dev": disk_name, "mode": method}
            )

            return {
                "success": True,
                "message": f"Disk '{disk_name}' wipe initiated with method '{method}'",
                "disk": disk_name,
                "method": method,
                "note": "Wipe operation may take significant time for FULL methods."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to wipe disk: {str(e)}"
            }
