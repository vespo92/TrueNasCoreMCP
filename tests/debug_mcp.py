#!/usr/bin/env python3
"""Debug MCP function to check environment variables"""

import os
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("TrueNAS Debug")

@mcp.tool()
async def debug_env() -> Dict[str, Any]:
    """Debug function to check environment variables"""
    return {
        "TRUENAS_URL": os.getenv("TRUENAS_URL", "NOT SET"),
        "TRUENAS_API_KEY": os.getenv("TRUENAS_API_KEY", "NOT SET")[:20] + "..." if os.getenv("TRUENAS_API_KEY") else "NOT SET",
        "TRUENAS_VERIFY_SSL": os.getenv("TRUENAS_VERIFY_SSL", "NOT SET"),
        "PATH": os.getenv("PATH", "NOT SET"),
        "PWD": os.getenv("PWD", "NOT SET"),
        "All ENV vars": list(os.environ.keys())
    }

if __name__ == "__main__":
    mcp.run()
