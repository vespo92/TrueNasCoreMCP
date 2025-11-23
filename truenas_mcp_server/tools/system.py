"""
System management tools for TrueNAS
"""

from typing import Dict, Any, Optional, List
from .base import BaseTool, tool_handler


class SystemTools(BaseTool):
    """Tools for managing TrueNAS system operations"""

    def get_tool_definitions(self) -> list:
        """Get tool definitions for system management"""
        return [
            ("get_system_info", self.get_system_info,
             "Get comprehensive system information including version, hardware, and uptime", {}),
            ("get_system_version", self.get_system_version,
             "Get TrueNAS version information", {}),
            ("list_services", self.list_services,
             "List all system services with their status", {}),
            ("get_service_status", self.get_service_status,
             "Get status of a specific service",
             {"service_name": {"type": "string", "required": True}}),
            ("start_service", self.start_service,
             "Start a system service",
             {"service_name": {"type": "string", "required": True}}),
            ("stop_service", self.stop_service,
             "Stop a system service",
             {"service_name": {"type": "string", "required": True}}),
            ("restart_service", self.restart_service,
             "Restart a system service",
             {"service_name": {"type": "string", "required": True}}),
            ("list_alerts", self.list_alerts,
             "List all system alerts", {}),
            ("dismiss_alert", self.dismiss_alert,
             "Dismiss a system alert",
             {"alert_id": {"type": "string", "required": True}}),
            ("get_boot_info", self.get_boot_info,
             "Get boot pool and environment information", {}),
            ("get_update_status", self.get_update_status,
             "Check for available system updates", {}),
        ]

    @tool_handler
    async def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information

        Returns:
            Dictionary containing system information
        """
        await self.ensure_initialized()

        # Get system info from multiple endpoints
        try:
            system_info = await self.client.get("/system/info")
        except Exception:
            system_info = {}

        try:
            system_general = await self.client.get("/system/general")
        except Exception:
            system_general = {}

        try:
            version_info = await self.client.get("/system/version")
        except Exception:
            version_info = "Unknown"

        # Build comprehensive response
        return {
            "success": True,
            "system": {
                "hostname": system_general.get("hostname", system_info.get("hostname")),
                "version": version_info if isinstance(version_info, str) else system_info.get("version"),
                "buildtime": system_info.get("buildtime"),
                "uptime": system_info.get("uptime"),
                "uptime_seconds": system_info.get("uptime_seconds"),
                "timezone": system_general.get("timezone"),
                "language": system_general.get("language"),
                "model": system_info.get("system_product"),
                "manufacturer": system_info.get("system_manufacturer"),
                "serial": system_info.get("system_serial"),
                "cores": system_info.get("cores"),
                "physical_cores": system_info.get("physical_cores"),
                "loadavg": system_info.get("loadavg"),
                "memory": {
                    "physmem": self.format_size(system_info.get("physmem", 0)),
                    "physmem_bytes": system_info.get("physmem", 0),
                },
                "datetime": system_info.get("datetime"),
                "birthday": system_info.get("birthday"),
                "license": system_info.get("license"),
            }
        }

    @tool_handler
    async def get_system_version(self) -> Dict[str, Any]:
        """
        Get TrueNAS version information

        Returns:
            Dictionary containing version details
        """
        await self.ensure_initialized()

        version = await self.client.get("/system/version")
        version_short = await self.client.get("/system/version_short")

        try:
            system_info = await self.client.get("/system/info")
            build_time = system_info.get("buildtime")
        except Exception:
            build_time = None

        # Determine if it's TrueNAS Scale or Core
        is_scale = "SCALE" in str(version).upper() if version else False

        return {
            "success": True,
            "version": {
                "full": version,
                "short": version_short,
                "build_time": build_time,
                "product": "TrueNAS SCALE" if is_scale else "TrueNAS Core",
                "is_scale": is_scale
            }
        }

    @tool_handler
    async def list_services(self) -> Dict[str, Any]:
        """
        List all system services with their status

        Returns:
            Dictionary containing list of services
        """
        await self.ensure_initialized()

        services = await self.client.get("/service")

        service_list = []
        for svc in services:
            service_info = {
                "id": svc.get("id"),
                "service": svc.get("service"),
                "state": svc.get("state"),
                "enable": svc.get("enable"),
                "running": svc.get("state") == "RUNNING",
            }
            service_list.append(service_info)

        # Categorize services
        running_services = [s for s in service_list if s["running"]]
        enabled_services = [s for s in service_list if s["enable"]]

        return {
            "success": True,
            "services": service_list,
            "metadata": {
                "total_services": len(service_list),
                "running_services": len(running_services),
                "enabled_services": len(enabled_services),
                "stopped_services": len(service_list) - len(running_services)
            }
        }

    @tool_handler
    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get status of a specific service

        Args:
            service_name: Name of the service (e.g., "smb", "nfs", "ssh")

        Returns:
            Dictionary containing service status
        """
        await self.ensure_initialized()

        services = await self.client.get("/service")

        target_service = None
        for svc in services:
            if svc.get("service") == service_name:
                target_service = svc
                break

        if not target_service:
            return {
                "success": False,
                "error": f"Service '{service_name}' not found"
            }

        return {
            "success": True,
            "service": {
                "name": target_service.get("service"),
                "state": target_service.get("state"),
                "enable": target_service.get("enable"),
                "running": target_service.get("state") == "RUNNING",
                "id": target_service.get("id")
            }
        }

    @tool_handler
    async def start_service(self, service_name: str) -> Dict[str, Any]:
        """
        Start a system service

        Args:
            service_name: Name of the service to start

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        try:
            result = await self.client.post(f"/service/start", {"service": service_name})

            return {
                "success": True,
                "message": f"Service '{service_name}' started successfully",
                "service": service_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start service '{service_name}': {str(e)}"
            }

    @tool_handler
    async def stop_service(self, service_name: str) -> Dict[str, Any]:
        """
        Stop a system service

        Args:
            service_name: Name of the service to stop

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        try:
            result = await self.client.post(f"/service/stop", {"service": service_name})

            return {
                "success": True,
                "message": f"Service '{service_name}' stopped successfully",
                "service": service_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop service '{service_name}': {str(e)}"
            }

    @tool_handler
    async def restart_service(self, service_name: str) -> Dict[str, Any]:
        """
        Restart a system service

        Args:
            service_name: Name of the service to restart

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        try:
            result = await self.client.post(f"/service/restart", {"service": service_name})

            return {
                "success": True,
                "message": f"Service '{service_name}' restarted successfully",
                "service": service_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to restart service '{service_name}': {str(e)}"
            }

    @tool_handler
    async def list_alerts(self) -> Dict[str, Any]:
        """
        List all system alerts

        Returns:
            Dictionary containing list of alerts
        """
        await self.ensure_initialized()

        alerts = await self.client.get("/alert/list")

        alert_list = []
        for alert in alerts:
            alert_info = {
                "id": alert.get("id"),
                "uuid": alert.get("uuid"),
                "source": alert.get("source"),
                "klass": alert.get("klass"),
                "level": alert.get("level"),
                "formatted": alert.get("formatted"),
                "text": alert.get("text"),
                "dismissed": alert.get("dismissed", False),
                "datetime": alert.get("datetime"),
                "one_shot": alert.get("one_shot", False)
            }
            alert_list.append(alert_info)

        # Categorize by level
        critical = [a for a in alert_list if a["level"] == "CRITICAL"]
        warnings = [a for a in alert_list if a["level"] == "WARNING"]
        info = [a for a in alert_list if a["level"] == "INFO"]
        active = [a for a in alert_list if not a["dismissed"]]

        return {
            "success": True,
            "alerts": alert_list,
            "metadata": {
                "total_alerts": len(alert_list),
                "active_alerts": len(active),
                "critical": len(critical),
                "warnings": len(warnings),
                "info": len(info),
                "dismissed": len(alert_list) - len(active)
            }
        }

    @tool_handler
    async def dismiss_alert(self, alert_id: str) -> Dict[str, Any]:
        """
        Dismiss a system alert

        Args:
            alert_id: ID of the alert to dismiss

        Returns:
            Dictionary confirming dismissal
        """
        await self.ensure_initialized()

        try:
            await self.client.post(f"/alert/dismiss", alert_id)

            return {
                "success": True,
                "message": f"Alert '{alert_id}' dismissed successfully",
                "alert_id": alert_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to dismiss alert: {str(e)}"
            }

    @tool_handler
    async def get_boot_info(self) -> Dict[str, Any]:
        """
        Get boot pool and environment information

        Returns:
            Dictionary containing boot information
        """
        await self.ensure_initialized()

        try:
            boot_state = await self.client.get("/boot/get_state")
        except Exception:
            boot_state = {}

        try:
            boot_envs = await self.client.get("/bootenv")
        except Exception:
            boot_envs = []

        # Process boot environments
        env_list = []
        for env in boot_envs:
            env_info = {
                "id": env.get("id"),
                "name": env.get("name"),
                "active": env.get("active"),
                "activated": env.get("activated"),
                "can_activate": env.get("can_activate"),
                "created": env.get("created"),
                "used": self.format_size(env.get("used_bytes", 0)) if env.get("used_bytes") else env.get("used"),
                "keep": env.get("keep", False)
            }
            env_list.append(env_info)

        return {
            "success": True,
            "boot": {
                "state": boot_state,
                "environments": env_list,
                "current_environment": next(
                    (e["name"] for e in env_list if e.get("active") == "NR" or e.get("activated")),
                    None
                )
            },
            "metadata": {
                "total_environments": len(env_list),
                "active_environment": next(
                    (e["name"] for e in env_list if "N" in str(e.get("active", ""))),
                    None
                )
            }
        }

    @tool_handler
    async def get_update_status(self) -> Dict[str, Any]:
        """
        Check for available system updates

        Returns:
            Dictionary containing update status
        """
        await self.ensure_initialized()

        try:
            update_check = await self.client.post("/update/check_available")
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to check for updates: {str(e)}"
            }

        return {
            "success": True,
            "updates": {
                "available": update_check.get("status") == "AVAILABLE" if isinstance(update_check, dict) else False,
                "status": update_check.get("status") if isinstance(update_check, dict) else str(update_check),
                "changes": update_check.get("changes", []) if isinstance(update_check, dict) else [],
                "changelog": update_check.get("changelog") if isinstance(update_check, dict) else None,
                "version": update_check.get("version") if isinstance(update_check, dict) else None
            }
        }
