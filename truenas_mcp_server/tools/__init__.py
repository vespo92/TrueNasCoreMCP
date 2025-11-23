"""
MCP Tools for TrueNAS operations
"""

from .base import BaseTool, tool_handler
from .debug import DebugTools
from .users import UserTools
from .groups import GroupTools
from .storage import StorageTools
from .sharing import SharingTools
from .snapshots import SnapshotTools
from .system import SystemTools
from .disks import DiskTools
from .network import NetworkTools
from .replication import ReplicationTools
from .apps import AppTools
from .vms import VMTools

__all__ = [
    "BaseTool",
    "tool_handler",
    "DebugTools",
    "UserTools",
    "GroupTools",
    "StorageTools",
    "SharingTools",
    "SnapshotTools",
    "SystemTools",
    "DiskTools",
    "NetworkTools",
    "ReplicationTools",
    "AppTools",
    "VMTools",
]