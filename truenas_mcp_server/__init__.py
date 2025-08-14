"""
TrueNAS MCP Server - A Model Context Protocol server for TrueNAS Core systems

This package provides a comprehensive MCP server implementation for managing
TrueNAS Core systems through natural language interfaces.
"""

__version__ = "3.0.0"
__author__ = "Vinnie Espo"
__email__ = "vespo21@gmail.com"

from .server import TrueNASMCPServer, create_server, main

__all__ = ["TrueNASMCPServer", "create_server", "main", "__version__"]