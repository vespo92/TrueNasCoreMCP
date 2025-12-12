"""
MCP Tools for TrueNAS operations
"""

from .base import BaseTool, tool_handler
from .debug import DebugTools
from .users import UserTools
from .storage import StorageTools
from .sharing import SharingTools
from .snapshots import SnapshotTools
from .apps import AppTools
from .instances import InstanceTools
from .vms import LegacyVMTools

__all__ = [
    "BaseTool",
    "tool_handler",
    "DebugTools",
    "UserTools",
    "StorageTools",
    "SharingTools",
    "SnapshotTools",
    # Virtualization tools
    "AppTools",
    "InstanceTools",
    "LegacyVMTools",
]