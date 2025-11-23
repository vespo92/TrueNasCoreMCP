"""
Application/Container management tools for TrueNAS Scale
"""

from typing import Dict, Any, Optional, List
from .base import BaseTool, tool_handler


class AppTools(BaseTool):
    """Tools for managing TrueNAS Scale applications (Docker/Kubernetes)"""

    def get_tool_definitions(self) -> list:
        """Get tool definitions for app management"""
        return [
            ("list_apps", self.list_apps,
             "List all installed applications", {}),
            ("get_app", self.get_app,
             "Get detailed information about an installed application",
             {"app_name": {"type": "string", "required": True}}),
            ("start_app", self.start_app,
             "Start an application",
             {"app_name": {"type": "string", "required": True}}),
            ("stop_app", self.stop_app,
             "Stop an application",
             {"app_name": {"type": "string", "required": True}}),
            ("restart_app", self.restart_app,
             "Restart an application",
             {"app_name": {"type": "string", "required": True}}),
            ("delete_app", self.delete_app,
             "Delete an application",
             {"app_name": {"type": "string", "required": True}}),
            ("list_app_catalog", self.list_app_catalog,
             "List available applications from catalog", {}),
            ("search_app_catalog", self.search_app_catalog,
             "Search for applications in catalog",
             {"query": {"type": "string", "required": True}}),
            ("get_app_logs", self.get_app_logs,
             "Get logs from an application",
             {"app_name": {"type": "string", "required": True},
              "container_name": {"type": "string", "required": False},
              "tail_lines": {"type": "integer", "required": False}}),
            ("list_docker_images", self.list_docker_images,
             "List all Docker images", {}),
            ("pull_docker_image", self.pull_docker_image,
             "Pull a Docker image",
             {"image": {"type": "string", "required": True}}),
            ("get_kubernetes_status", self.get_kubernetes_status,
             "Get Kubernetes/container runtime status", {}),
        ]

    @tool_handler
    async def list_apps(self) -> Dict[str, Any]:
        """
        List all installed applications

        Returns:
            Dictionary containing list of installed apps
        """
        await self.ensure_initialized()

        try:
            apps = await self.client.get("/app")
        except Exception:
            # Try legacy chart/release endpoint for older versions
            try:
                apps = await self.client.get("/chart/release")
            except Exception:
                return {
                    "success": False,
                    "error": "Apps not available. This feature requires TrueNAS Scale."
                }

        app_list = []
        for app in apps:
            app_info = {
                "id": app.get("id"),
                "name": app.get("name"),
                "state": app.get("state") or app.get("status"),
                "version": app.get("version") or app.get("chart_metadata", {}).get("version"),
                "app_version": app.get("app_version") or app.get("chart_metadata", {}).get("appVersion"),
                "catalog": app.get("catalog"),
                "catalog_train": app.get("catalog_train"),
                "path": app.get("path"),
                "human_version": app.get("human_version"),
                "update_available": app.get("update_available", False),
                "container_images_update_available": app.get("container_images_update_available", False),
                "portals": app.get("portals", {}),
                "notes": app.get("notes"),
            }
            app_list.append(app_info)

        # Categorize by state
        running = [a for a in app_list if a.get("state") in ["RUNNING", "ACTIVE", "DEPLOYING"]]
        stopped = [a for a in app_list if a.get("state") in ["STOPPED", "CRASHED"]]

        return {
            "success": True,
            "apps": app_list,
            "metadata": {
                "total_apps": len(app_list),
                "running_apps": len(running),
                "stopped_apps": len(stopped),
                "apps_with_updates": sum(1 for a in app_list if a.get("update_available"))
            }
        }

    @tool_handler
    async def get_app(self, app_name: str) -> Dict[str, Any]:
        """
        Get detailed information about an installed application

        Args:
            app_name: Name of the application

        Returns:
            Dictionary containing app details
        """
        await self.ensure_initialized()

        try:
            app = await self.client.get(f"/app/id/{app_name}")
        except Exception:
            try:
                app = await self.client.get(f"/chart/release/id/{app_name}")
            except Exception:
                return {
                    "success": False,
                    "error": f"Application '{app_name}' not found"
                }

        return {
            "success": True,
            "app": {
                "id": app.get("id"),
                "name": app.get("name"),
                "state": app.get("state") or app.get("status"),
                "version": app.get("version"),
                "app_version": app.get("app_version"),
                "catalog": app.get("catalog"),
                "catalog_train": app.get("catalog_train"),
                "path": app.get("path"),
                "dataset": app.get("dataset"),
                "human_version": app.get("human_version"),
                "update_available": app.get("update_available", False),
                "config": app.get("config", {}),
                "history": app.get("history", {}),
                "portals": app.get("portals", {}),
                "notes": app.get("notes"),
                "used_ports": app.get("used_ports", []),
                "active_workloads": app.get("active_workloads", {}),
                "resources": app.get("resources", {}),
            }
        }

    @tool_handler
    async def start_app(self, app_name: str) -> Dict[str, Any]:
        """
        Start an application

        Args:
            app_name: Name of the application to start

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        try:
            result = await self.client.post(f"/app/id/{app_name}/start")
        except Exception:
            try:
                result = await self.client.post(f"/chart/release/id/{app_name}/scale",
                                               {"replica_count": 1})
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to start application: {str(e)}"
                }

        return {
            "success": True,
            "message": f"Application '{app_name}' started",
            "app_name": app_name
        }

    @tool_handler
    async def stop_app(self, app_name: str) -> Dict[str, Any]:
        """
        Stop an application

        Args:
            app_name: Name of the application to stop

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        try:
            result = await self.client.post(f"/app/id/{app_name}/stop")
        except Exception:
            try:
                result = await self.client.post(f"/chart/release/id/{app_name}/scale",
                                               {"replica_count": 0})
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to stop application: {str(e)}"
                }

        return {
            "success": True,
            "message": f"Application '{app_name}' stopped",
            "app_name": app_name
        }

    @tool_handler
    async def restart_app(self, app_name: str) -> Dict[str, Any]:
        """
        Restart an application

        Args:
            app_name: Name of the application to restart

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        try:
            # Try direct restart
            result = await self.client.post(f"/app/id/{app_name}/restart")
        except Exception:
            try:
                # Scale down then up
                await self.client.post(f"/chart/release/id/{app_name}/scale",
                                       {"replica_count": 0})
                result = await self.client.post(f"/chart/release/id/{app_name}/scale",
                                               {"replica_count": 1})
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to restart application: {str(e)}"
                }

        return {
            "success": True,
            "message": f"Application '{app_name}' restarted",
            "app_name": app_name
        }

    @tool_handler
    async def delete_app(self, app_name: str, delete_unused_images: bool = True) -> Dict[str, Any]:
        """
        Delete an application

        Args:
            app_name: Name of the application to delete
            delete_unused_images: Whether to delete unused container images

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        # Check if destructive operations are allowed
        if not self.settings.enable_destructive_operations:
            return {
                "success": False,
                "error": "Destructive operations are disabled. Enable TRUENAS_ENABLE_DESTRUCTIVE_OPS to allow app deletion."
            }

        try:
            result = await self.client.delete(f"/app/id/{app_name}",
                                             {"delete_unused_images": delete_unused_images})
        except Exception:
            try:
                result = await self.client.delete(f"/chart/release/id/{app_name}",
                                                 {"delete_unused_images": delete_unused_images})
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to delete application: {str(e)}"
                }

        return {
            "success": True,
            "message": f"Application '{app_name}' deleted",
            "app_name": app_name,
            "deleted_unused_images": delete_unused_images
        }

    @tool_handler
    async def list_app_catalog(self) -> Dict[str, Any]:
        """
        List available applications from catalog

        Returns:
            Dictionary containing available apps
        """
        await self.ensure_initialized()

        try:
            catalogs = await self.client.get("/catalog")
        except Exception:
            return {
                "success": False,
                "error": "App catalog not available. This feature requires TrueNAS Scale."
            }

        catalog_list = []
        for catalog in catalogs:
            catalog_info = {
                "id": catalog.get("id"),
                "label": catalog.get("label"),
                "repository": catalog.get("repository"),
                "branch": catalog.get("branch"),
                "builtin": catalog.get("builtin", False),
                "preferred_trains": catalog.get("preferred_trains", []),
            }
            catalog_list.append(catalog_info)

        return {
            "success": True,
            "catalogs": catalog_list,
            "metadata": {
                "total_catalogs": len(catalog_list)
            }
        }

    @tool_handler
    async def search_app_catalog(self, query: str) -> Dict[str, Any]:
        """
        Search for applications in catalog

        Args:
            query: Search query

        Returns:
            Dictionary containing search results
        """
        await self.ensure_initialized()

        try:
            # Try the app search endpoint
            results = await self.client.post("/app/available",
                                            {"catalog_query": {"query": query}})
        except Exception:
            try:
                results = await self.client.get("/catalog/items")
                # Filter locally if needed
                if isinstance(results, dict):
                    filtered = {}
                    for train, apps in results.items():
                        for app_name, app_data in apps.items() if isinstance(apps, dict) else []:
                            if query.lower() in app_name.lower():
                                if train not in filtered:
                                    filtered[train] = {}
                                filtered[train][app_name] = app_data
                    results = filtered
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to search catalog: {str(e)}"
                }

        if isinstance(results, list):
            app_list = []
            for app in results[:50]:  # Limit to 50 results
                app_info = {
                    "name": app.get("name"),
                    "title": app.get("title"),
                    "description": app.get("description"),
                    "version": app.get("latest_version") or app.get("version"),
                    "app_version": app.get("latest_app_version"),
                    "catalog": app.get("catalog"),
                    "train": app.get("train"),
                    "icon_url": app.get("icon_url"),
                    "categories": app.get("categories", []),
                }
                app_list.append(app_info)

            return {
                "success": True,
                "query": query,
                "results": app_list,
                "metadata": {
                    "total_results": len(app_list)
                }
            }

        return {
            "success": True,
            "query": query,
            "results": results,
        }

    @tool_handler
    async def get_app_logs(
        self,
        app_name: str,
        container_name: Optional[str] = None,
        tail_lines: int = 100
    ) -> Dict[str, Any]:
        """
        Get logs from an application

        Args:
            app_name: Name of the application
            container_name: Specific container name (optional)
            tail_lines: Number of lines to return

        Returns:
            Dictionary containing logs
        """
        await self.ensure_initialized()

        try:
            # Get pod logs
            log_params = {
                "limit_bytes": 500000,
                "tail_lines": tail_lines
            }
            if container_name:
                log_params["container_id"] = container_name

            logs = await self.client.post(f"/app/id/{app_name}/logs", log_params)
        except Exception:
            try:
                logs = await self.client.post(f"/chart/release/id/{app_name}/pod_logs", log_params)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to get application logs: {str(e)}"
                }

        return {
            "success": True,
            "app_name": app_name,
            "container": container_name,
            "logs": logs if isinstance(logs, str) else str(logs),
            "tail_lines": tail_lines
        }

    @tool_handler
    async def list_docker_images(self) -> Dict[str, Any]:
        """
        List all Docker images

        Returns:
            Dictionary containing list of Docker images
        """
        await self.ensure_initialized()

        try:
            images = await self.client.get("/container/image")
        except Exception:
            try:
                images = await self.client.get("/docker/images")
            except Exception:
                return {
                    "success": False,
                    "error": "Docker images not available. This feature requires TrueNAS Scale."
                }

        image_list = []
        for image in images:
            image_info = {
                "id": image.get("id"),
                "repo_tags": image.get("repo_tags", []),
                "repo_digests": image.get("repo_digests", []),
                "size": self.format_size(image.get("size", 0)),
                "size_bytes": image.get("size", 0),
                "created": image.get("created"),
                "dangling": image.get("dangling", False),
                "update_available": image.get("update_available", False),
                "system_image": image.get("system_image", False),
            }
            image_list.append(image_info)

        total_size = sum(img.get("size_bytes", 0) for img in image_list)

        return {
            "success": True,
            "images": image_list,
            "metadata": {
                "total_images": len(image_list),
                "total_size": self.format_size(total_size),
                "dangling_images": sum(1 for img in image_list if img.get("dangling")),
                "images_with_updates": sum(1 for img in image_list if img.get("update_available"))
            }
        }

    @tool_handler
    async def pull_docker_image(self, image: str) -> Dict[str, Any]:
        """
        Pull a Docker image

        Args:
            image: Image name with optional tag (e.g., "nginx:latest")

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        try:
            result = await self.client.post("/container/image/pull",
                                           {"image": image})
        except Exception:
            try:
                result = await self.client.post("/docker/images/pull",
                                               {"image": image})
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to pull image: {str(e)}"
                }

        return {
            "success": True,
            "message": f"Image '{image}' pull initiated",
            "image": image,
            "note": "Image pull running in background"
        }

    @tool_handler
    async def get_kubernetes_status(self) -> Dict[str, Any]:
        """
        Get Kubernetes/container runtime status

        Returns:
            Dictionary containing K8s/container status
        """
        await self.ensure_initialized()

        try:
            # Try getting Kubernetes status
            k8s_status = await self.client.get("/kubernetes/status")
        except Exception:
            k8s_status = None

        try:
            # Try getting container config
            container_config = await self.client.get("/kubernetes/config")
        except Exception:
            try:
                container_config = await self.client.get("/container/config")
            except Exception:
                container_config = None

        if not k8s_status and not container_config:
            return {
                "success": False,
                "error": "Container runtime not available. This feature requires TrueNAS Scale."
            }

        return {
            "success": True,
            "kubernetes": {
                "status": k8s_status,
                "config": {
                    "pool": container_config.get("pool") if container_config else None,
                    "node_ip": container_config.get("node_ip") if container_config else None,
                    "cluster_cidr": container_config.get("cluster_cidr") if container_config else None,
                    "service_cidr": container_config.get("service_cidr") if container_config else None,
                    "cluster_dns_ip": container_config.get("cluster_dns_ip") if container_config else None,
                    "route_v4_interface": container_config.get("route_v4_interface") if container_config else None,
                    "route_v4_gateway": container_config.get("route_v4_gateway") if container_config else None,
                } if container_config else None
            }
        }
