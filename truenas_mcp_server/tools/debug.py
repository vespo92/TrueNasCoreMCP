"""
Debug tools for TrueNAS MCP Server
"""

import os
from typing import Dict, Any
from .base import BaseTool, tool_handler


class DebugTools(BaseTool):
    """Debug and diagnostic tools"""
    
    def get_tool_definitions(self) -> list:
        """Get tool definitions for debug tools"""
        return [
            ("debug_connection", self.debug_connection, "Debug connection settings and environment variables", {}),
            ("test_connection", self.test_connection, "Test the connection to TrueNAS API", {}),
            ("get_server_stats", self.get_server_stats, "Get MCP server statistics", {}),
        ]
    
    @tool_handler
    async def debug_connection(self) -> Dict[str, Any]:
        """
        Debug connection settings and environment variables
        
        Returns:
            Dictionary containing debug information
        """
        await self.ensure_initialized()
        
        # Mask sensitive data
        api_key = self.settings.truenas_api_key.get_secret_value()
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        
        return {
            "success": True,
            "environment": {
                "TRUENAS_URL": str(self.settings.truenas_url),
                "TRUENAS_API_KEY": masked_key,
                "TRUENAS_VERIFY_SSL": self.settings.truenas_verify_ssl,
                "TRUENAS_ENV": self.settings.environment,
                "TRUENAS_LOG_LEVEL": self.settings.log_level
            },
            "client": {
                "connected": self.client._client is not None if self.client else False,
                "base_url": self.settings.api_base_url,
                "timeout": self.settings.http_timeout,
                "max_retries": self.settings.http_max_retries
            },
            "features": {
                "debug_tools": self.settings.enable_debug_tools,
                "destructive_operations": self.settings.enable_destructive_operations,
                "rate_limiting": self.settings.rate_limit_enabled
            }
        }
    
    @tool_handler
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to TrueNAS API
        
        Returns:
            Dictionary containing connection test results
        """
        await self.ensure_initialized()
        
        try:
            # Try to get system info as a test
            system_info = await self.client.get("/system/info")
            
            return {
                "success": True,
                "message": "Connection successful",
                "system": {
                    "hostname": system_info.get("hostname"),
                    "version": system_info.get("version"),
                    "system": system_info.get("system_product"),
                    "uptime": system_info.get("uptime_seconds")
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Connection failed"
            }
    
    @tool_handler
    async def get_server_stats(self) -> Dict[str, Any]:
        """
        Get MCP server statistics
        
        Returns:
            Dictionary containing server statistics
        """
        await self.ensure_initialized()
        
        # Get client stats
        client_stats = self.client.get_stats() if self.client else {}
        
        return {
            "success": True,
            "stats": {
                "version": self.settings.get_version(),
                "environment": self.settings.environment,
                "client": client_stats,
                "configuration": {
                    "http_timeout": self.settings.http_timeout,
                    "http_max_retries": self.settings.http_max_retries,
                    "pool_connections": self.settings.http_pool_connections,
                    "pool_maxsize": self.settings.http_pool_maxsize
                }
            }
        }