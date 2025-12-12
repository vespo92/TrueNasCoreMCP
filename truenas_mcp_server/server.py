"""
Main TrueNAS MCP Server implementation

Supports both TrueNAS Core and TrueNAS SCALE with automatic variant detection.
SCALE-specific features (Apps, Incus, VMs) are only registered when connected
to a SCALE system.
"""

import sys
import logging
import asyncio
from typing import Optional, List, Type
from mcp.server.fastmcp import FastMCP

from .config import get_settings
from .client import get_client, close_client, TrueNASVariant
from .tools import (
    BaseTool,
    DebugTools,
    UserTools,
    StorageTools,
    SharingTools,
    SnapshotTools,
    AppTools,
    InstanceTools,
    LegacyVMTools,
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

    Manages the MCP server instance and registers all available tools.
    Automatically detects TrueNAS variant (Core vs SCALE) and registers
    appropriate tools.
    """

    # Tools that work on both TrueNAS Core and SCALE
    UNIVERSAL_TOOLS: List[Type[BaseTool]] = [
        UserTools,
        StorageTools,
        SharingTools,
        SnapshotTools,
    ]

    # Tools that only work on TrueNAS SCALE
    SCALE_ONLY_TOOLS: List[Type[BaseTool]] = [
        AppTools,       # Docker Compose apps (SCALE 24.04+)
        InstanceTools,  # Incus VMs/containers (SCALE 25.04+)
        LegacyVMTools,  # bhyve VMs (SCALE, differs from Core)
    ]

    def __init__(self, name: str = "TrueNAS MCP Server"):
        """
        Initialize the TrueNAS MCP Server

        Args:
            name: Server name for MCP
        """
        self.name = name
        self.settings = get_settings()
        self.mcp = FastMCP(name)
        self.tools: List[BaseTool] = []
        self.variant: TrueNASVariant = TrueNASVariant.UNKNOWN
        self._setup_logging()
        # Note: Tools are registered during initialize() after variant detection
    
    def _setup_logging(self):
        """Configure logging based on settings"""
        log_level = getattr(logging, self.settings.log_level)
        logging.getLogger().setLevel(log_level)
        
        # Set httpx logging to WARNING unless in DEBUG mode
        if self.settings.log_level != "DEBUG":
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    def _register_tools(self, variant: TrueNASVariant):
        """
        Register tools with the MCP server based on TrueNAS variant

        Args:
            variant: Detected TrueNAS variant (Core, SCALE, or Unknown)
        """
        logger.info(f"Registering MCP tools for TrueNAS {variant.value}...")

        # Start with universal tools that work on both Core and SCALE
        tool_classes: List[Type[BaseTool]] = list(self.UNIVERSAL_TOOLS)

        # Add SCALE-only tools if connected to SCALE
        if variant == TrueNASVariant.SCALE:
            tool_classes.extend(self.SCALE_ONLY_TOOLS)
            logger.info("Including SCALE-specific tools (Apps, Instances, VMs)")
        elif variant == TrueNASVariant.CORE:
            logger.info("Skipping SCALE-only tools (Apps, Instances, VMs) - Core detected")
        else:
            # Unknown variant - include all tools but warn
            tool_classes.extend(self.SCALE_ONLY_TOOLS)
            logger.warning(
                "TrueNAS variant unknown - registering all tools. "
                "SCALE-only tools may fail on TrueNAS Core."
            )

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
        """Initialize the server, detect variant, and register tools"""
        logger.info(f"Initializing {self.name}...")

        try:
            # Initialize the client
            client = await get_client()

            # Detect TrueNAS variant (Core vs SCALE)
            self.variant = await client.detect_variant()
            logger.info(
                f"Connected to TrueNAS {self.variant.value.upper()} "
                f"version {client.version or 'unknown'}"
            )

            # Register tools based on detected variant
            self._register_tools(self.variant)

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