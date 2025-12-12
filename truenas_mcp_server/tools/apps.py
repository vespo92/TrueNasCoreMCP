"""
TrueNAS App management tools

Provides tools for managing Docker Compose-based applications on TrueNAS SCALE.
Uses the /api/v2.0/app endpoints.

API Quirks:
- POST /app/config expects a plain string body: "app_name" (not an object!)
- POST /app/start expects: {"app_name": "name"} (an object)
- POST /app/stop expects: {"app_name": "name"} (an object)
- App operations are async and return job IDs
"""

import asyncio
from typing import Any, Dict, List, Optional

from .base import BaseTool, tool_handler


class AppTools(BaseTool):
    """Tools for managing TrueNAS apps (Docker Compose applications)"""

    # Timeout for app operations (start/stop can take time)
    APP_OPERATION_TIMEOUT = 120  # seconds
    POLL_INTERVAL = 5  # seconds

    def get_tool_definitions(self) -> list:
        """Get tool definitions for app management"""
        return [
            ("list_apps", self.list_apps, "List all TrueNAS apps with status", {}),
            ("get_app", self.get_app, "Get detailed information about a specific app",
             {"app_name": {"type": "string", "required": True,
                         "description": "Name of the app"}}),
            ("get_app_config", self.get_app_config,
             "Get the full configuration of an app",
             {"app_name": {"type": "string", "required": True,
                         "description": "Name of the app"}}),
            ("start_app", self.start_app, "Start an app",
             {"app_name": {"type": "string", "required": True,
                         "description": "Name of the app to start"}}),
            ("stop_app", self.stop_app, "Stop an app",
             {"app_name": {"type": "string", "required": True,
                         "description": "Name of the app to stop"},
              "force": {"type": "boolean", "required": False,
                       "description": "Force stop without waiting (default: false)"}}),
            ("restart_app", self.restart_app, "Restart an app (stop then start)",
             {"app_name": {"type": "string", "required": True,
                         "description": "Name of the app to restart"}}),
            ("redeploy_app", self.redeploy_app,
             "Redeploy an app after configuration changes",
             {"app_name": {"type": "string", "required": True,
                         "description": "Name of the app to redeploy"}}),
            ("update_app_config", self.update_app_config,
             "Update app configuration (resource limits only in hostvars mode)",
             {"app_name": {"type": "string", "required": True,
                         "description": "Name of the app to update"},
              "values": {"type": "object", "required": True,
                        "description": "Configuration values to update"}}),
        ]

    @tool_handler
    async def list_apps(self) -> Dict[str, Any]:
        """
        List all TrueNAS apps with their status

        Returns:
            Dictionary containing list of apps with status and metadata
        """
        await self.ensure_initialized()

        apps = await self.client.get("/app")

        app_list = []
        for app in apps:
            # Extract portal URL if available
            portal_url = None
            portal = app.get("portal", {})
            if portal and isinstance(portal, dict):
                # Get first portal entry
                for portal_info in portal.values():
                    if isinstance(portal_info, str):
                        portal_url = portal_info
                        break
                    elif isinstance(portal_info, dict):
                        portal_url = portal_info.get("url")
                        break

            app_info = {
                "name": app.get("id") or app.get("name"),
                "state": app.get("state", "UNKNOWN"),
                "version": app.get("version"),
                "human_version": app.get("human_version"),
                "upgrade_available": app.get("upgrade_available", False),
                "portal_url": portal_url,
            }
            app_list.append(app_info)

        # Count by state
        state_counts = {}
        for app in app_list:
            state = app["state"]
            state_counts[state] = state_counts.get(state, 0) + 1

        return {
            "success": True,
            "apps": app_list,
            "metadata": {
                "total_apps": len(app_list),
                "state_counts": state_counts,
            }
        }

    @tool_handler
    async def get_app(self, app_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific app

        Args:
            app_name: Name of the app

        Returns:
            Dictionary containing app details
        """
        await self.ensure_initialized()

        try:
            app = await self.client.get(f"/app/id/{app_name}")
        except Exception:
            # Try getting all apps and finding by name
            apps = await self.client.get("/app")
            app = None
            for a in apps:
                if a.get("id") == app_name or a.get("name") == app_name:
                    app = a
                    break

            if not app:
                return {
                    "success": False,
                    "error": f"App '{app_name}' not found"
                }

        return {
            "success": True,
            "app": {
                "name": app.get("id") or app.get("name"),
                "state": app.get("state"),
                "version": app.get("version"),
                "human_version": app.get("human_version"),
                "upgrade_available": app.get("upgrade_available", False),
                "portal": app.get("portal"),
                "metadata": app.get("metadata", {}),
            },
            "raw": app  # Include full response for debugging
        }

    @tool_handler
    async def get_app_config(self, app_name: str) -> Dict[str, Any]:
        """
        Get the full configuration of an app

        NOTE: The /app/config endpoint expects a plain string body!

        Args:
            app_name: Name of the app

        Returns:
            Dictionary containing the full app configuration
        """
        await self.ensure_initialized()

        # NOTE: This endpoint expects a plain quoted string, not an object!
        config = await self.client.post_raw("/app/config", f'"{app_name}"')

        return {
            "success": True,
            "app_name": app_name,
            "config": config
        }

    @tool_handler
    async def start_app(self, app_name: str) -> Dict[str, Any]:
        """
        Start an app

        Args:
            app_name: Name of the app to start

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Check current state first
        try:
            app = await self.client.get(f"/app/id/{app_name}")
            current_state = app.get("state", "UNKNOWN")

            if current_state == "RUNNING":
                return {
                    "success": True,
                    "message": f"App '{app_name}' is already running",
                    "state": current_state
                }
        except Exception:
            pass  # Continue with start attempt

        # Start the app
        result = await self.client.post("/app/start", {"app_name": app_name})

        # Poll for completion
        final_state = await self._wait_for_app_state(app_name, "RUNNING")

        return {
            "success": final_state == "RUNNING",
            "app_name": app_name,
            "state": final_state,
            "message": f"App '{app_name}' started successfully" if final_state == "RUNNING"
                      else f"App '{app_name}' may still be starting (current state: {final_state})"
        }

    @tool_handler
    async def stop_app(
        self,
        app_name: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Stop an app

        Args:
            app_name: Name of the app to stop
            force: Force stop without waiting

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Check current state first
        try:
            app = await self.client.get(f"/app/id/{app_name}")
            current_state = app.get("state", "UNKNOWN")

            if current_state == "STOPPED":
                return {
                    "success": True,
                    "message": f"App '{app_name}' is already stopped",
                    "state": current_state
                }
        except Exception:
            pass

        # Stop the app
        body = {"app_name": app_name}
        if force:
            body["force"] = True

        result = await self.client.post("/app/stop", body)

        if force:
            return {
                "success": True,
                "app_name": app_name,
                "message": f"Force stop initiated for app '{app_name}'"
            }

        # Poll for completion
        final_state = await self._wait_for_app_state(app_name, "STOPPED")

        return {
            "success": final_state == "STOPPED",
            "app_name": app_name,
            "state": final_state,
            "message": f"App '{app_name}' stopped successfully" if final_state == "STOPPED"
                      else f"App '{app_name}' may still be stopping (current state: {final_state})"
        }

    @tool_handler
    async def restart_app(self, app_name: str) -> Dict[str, Any]:
        """
        Restart an app (stop then start)

        Args:
            app_name: Name of the app to restart

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Stop the app first
        stop_result = await self.client.post("/app/stop", {"app_name": app_name})
        await self._wait_for_app_state(app_name, "STOPPED")

        # Start the app
        start_result = await self.client.post("/app/start", {"app_name": app_name})
        final_state = await self._wait_for_app_state(app_name, "RUNNING")

        return {
            "success": final_state == "RUNNING",
            "app_name": app_name,
            "state": final_state,
            "message": f"App '{app_name}' restarted successfully" if final_state == "RUNNING"
                      else f"App '{app_name}' restart may still be in progress"
        }

    @tool_handler
    async def redeploy_app(self, app_name: str) -> Dict[str, Any]:
        """
        Redeploy an app after configuration changes

        This pulls the latest container images and recreates containers.

        Args:
            app_name: Name of the app to redeploy

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Redeploy endpoint
        result = await self.client.post("/app/redeploy", {"app_name": app_name})

        # Poll for running state
        final_state = await self._wait_for_app_state(app_name, "RUNNING")

        return {
            "success": final_state == "RUNNING",
            "app_name": app_name,
            "state": final_state,
            "message": f"App '{app_name}' redeployed successfully" if final_state == "RUNNING"
                      else f"App '{app_name}' redeploy may still be in progress"
        }

    @tool_handler
    async def update_app_config(
        self,
        app_name: str,
        values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update app configuration

        Args:
            app_name: Name of the app to update
            values: Configuration values to update (e.g., {"resources": {"limits": {"cpus": 2, "memory": 4096}}})

        Returns:
            Dictionary containing operation result
        """
        await self.ensure_initialized()

        # Update the app configuration
        result = await self.client.put(
            f"/app/id/{app_name}",
            {"values": values}
        )

        return {
            "success": True,
            "app_name": app_name,
            "message": f"App '{app_name}' configuration updated",
            "updated_values": values
        }

    async def _wait_for_app_state(
        self,
        app_name: str,
        target_state: str,
        timeout: Optional[int] = None
    ) -> str:
        """
        Wait for an app to reach a target state

        Args:
            app_name: Name of the app
            target_state: State to wait for (e.g., "RUNNING", "STOPPED")
            timeout: Optional timeout in seconds (default: APP_OPERATION_TIMEOUT)

        Returns:
            Final state of the app
        """
        timeout = timeout or self.APP_OPERATION_TIMEOUT
        max_attempts = timeout // self.POLL_INTERVAL

        for _ in range(max_attempts):
            try:
                app = await self.client.get(f"/app/id/{app_name}")
                current_state = app.get("state", "UNKNOWN")

                if current_state == target_state:
                    return current_state

                # If we're in an error state, return immediately
                if current_state in ("CRASHED", "ERROR"):
                    return current_state

            except Exception as e:
                self.logger.warning(f"Error polling app state: {e}")

            await asyncio.sleep(self.POLL_INTERVAL)

        # Return last known state
        try:
            app = await self.client.get(f"/app/id/{app_name}")
            return app.get("state", "UNKNOWN")
        except Exception:
            return "UNKNOWN"
