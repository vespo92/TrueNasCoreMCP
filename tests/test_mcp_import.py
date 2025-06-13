#!/usr/bin/env python3
"""
Quick test script to verify MCP installation
"""

import sys
print(f"Python version: {sys.version}")

try:
    import mcp
    print(f"✅ MCP package imported successfully")
    print(f"   MCP version info available in package")
    
    from mcp.server.fastmcp import FastMCP
    print(f"✅ FastMCP imported successfully")
    
    # Try creating a simple server instance
    test_server = FastMCP("Test Server")
    print(f"✅ FastMCP server instance created successfully")
    
    print("\n🎉 All imports successful! MCP is properly installed.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nTroubleshooting steps:")
    print("1. Ensure you have Python 3.10 or higher")
    print("2. Try: pip install --upgrade pip")
    print("3. Try: pip install 'mcp>=1.1.0'")
    print("4. If that fails, try: pip install 'mcp[cli]>=1.1.0'")
    sys.exit(1)
