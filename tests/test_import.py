"""
Basic import tests for TrueNAS MCP Server
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_import_main_package():
    """Test that the main package can be imported"""
    from truenas_mcp_server import TrueNASMCPServer, __version__
    assert TrueNASMCPServer is not None
    assert __version__ == "3.0.0"


def test_import_exceptions():
    """Test that exceptions can be imported"""
    from truenas_mcp_server.exceptions import (
        TrueNASError,
        TrueNASConnectionError,
        TrueNASAuthenticationError
    )
    assert TrueNASError is not None
    assert TrueNASConnectionError is not None
    assert TrueNASAuthenticationError is not None


def test_import_models():
    """Test that models can be imported"""
    from truenas_mcp_server.models import (
        BaseModel,
        User,
        Pool,
        Dataset
    )
    assert BaseModel is not None
    assert User is not None
    assert Pool is not None
    assert Dataset is not None


def test_import_tools():
    """Test that tools can be imported"""
    from truenas_mcp_server.tools import (
        BaseTool,
        UserTools,
        StorageTools,
        SharingTools
    )
    assert BaseTool is not None
    assert UserTools is not None
    assert StorageTools is not None
    assert SharingTools is not None


def test_import_config():
    """Test that config can be imported"""
    from truenas_mcp_server.config import Settings
    assert Settings is not None


if __name__ == "__main__":
    # Run basic import test
    test_import_main_package()
    print("✅ Basic import test passed")