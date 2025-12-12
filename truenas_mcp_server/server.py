"""
Main TrueNAS MCP Server implementation
"""

import sys
import logging
import asyncio
from typing import Optional
from mcp.server.fastmcp import FastMCP

from .config import get_settings
from .client import get_client, close_client
from .tools import (
    DebugTools,
    UserTools,
    StorageTools,
    SharingTools,
    SnapshotTools
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrueNASMCPServer:
    """
    Main TrueNAS MCP Server class
    
    Manages the MCP server instance and registers all available tools
    """
    
    def __init__(self, name: str = "TrueNAS MCP Server"):
        """
        Initialize the TrueNAS MCP Server
        
        Args:
            name: Server name for MCP
        """
        self.name = name
        self.settings = get_settings()
        self.mcp = FastMCP(name)
        self.tools = []
        self._setup_logging()
        self._register_tools()
    
    def _setup_logging(self):
        """Configure logging based on settings"""
        log_level = getattr(logging, self.settings.log_level)
        logging.getLogger().setLevel(log_level)
        
        # Set httpx logging to WARNING unless in DEBUG mode
        if self.settings.log_level != "DEBUG":
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    def _register_tools(self):
        """Register all available tools with the MCP server"""
        logger.info("Registering MCP tools...")
        
        # Initialize tool instances
        tool_classes = [
            UserTools,
            StorageTools,
            SharingTools,
            SnapshotTools
        ]
        
        # Add debug tools if enabled
        if self.settings.enable_debug_tools or self.settings.is_development():
            tool_classes.insert(0, DebugTools)
        
        # Register each tool class
        for tool_class in tool_classes:
            tool_instance = tool_class()
            self.tools.append(tool_instance)
            self._register_tool_methods(tool_instance)
        
        logger.info(f"Registered {len(self.tools)} tool categories")
    
    def _register_tool_methods(self, tool_instance):
        """Register individual tool methods from a tool instance"""
        # Get all methods that should be exposed as MCP tools
        tool_methods = tool_instance.get_tool_definitions()
        
        for method_name, method_func, method_description, method_params in tool_methods:
            # Register with MCP
            self.mcp.tool(name=method_name, description=method_description)(method_func)
            logger.debug(f"Registered tool: {method_name}")
    
    async def initialize(self):
        """Initialize the server and all tools"""
        logger.info(f"Initializing {self.name}...")
        
        try:
            # Initialize the client
            client = await get_client()
            
            # Initialize all tools
            for tool in self.tools:
                tool.client = client
                tool.settings = self.settings
                await tool.initialize()
            
            logger.info(f"{self.name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources...")
        
        try:
            # Close the client
            await close_client()
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def run(self):
        """Run the MCP server"""
        logger.info(f"Starting {self.name}...")
        
        try:
            # Run initialization
            asyncio.run(self.initialize())
            
            # Run the MCP server
            self.mcp.run()
            
        except KeyboardInterrupt:
            logger.info(f"\n{self.name} shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            # Cleanup
            asyncio.run(self.cleanup())


def create_server(name: Optional[str] = None) -> TrueNASMCPServer:
    """
    Factory function to create a TrueNAS MCP Server instance
    
    Args:
        name: Optional server name
        
    Returns:
        TrueNASMCPServer instance
    """
    return TrueNASMCPServer(name or "TrueNAS MCP Server")


def main():
    """Main entry point for the TrueNAS MCP server"""
    try:
        # Validate configuration
        settings = get_settings()
        
        # Create and run the server
        server = create_server()
        server.run()
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())