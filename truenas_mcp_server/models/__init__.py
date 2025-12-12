"""
Data models for TrueNAS MCP Server
"""

from .base import BaseModel, ResponseModel
from .user import User, UserCreate, UserUpdate
from .storage import Pool, Dataset, DatasetCreate, Snapshot
from .sharing import SMBShare, NFSExport, ISCSITarget
from .app import App, AppConfig, AppState, AppSummary
from .instance import (
    IncusInstance,
    InstanceType,
    InstanceStatus,
    InstanceSummary,
    InstanceDevice,
    InstanceUpdateRequest
)
from .vm import LegacyVM, VMStatus, LegacyVMSummary, LegacyVMUpdateRequest

__all__ = [
    "BaseModel",
    "ResponseModel",
    "User",
    "UserCreate",
    "UserUpdate",
    "Pool",
    "Dataset",
    "DatasetCreate",
    "Snapshot",
    "SMBShare",
    "NFSExport",
    "ISCSITarget",
    # App models
    "App",
    "AppConfig",
    "AppState",
    "AppSummary",
    # Instance models (Incus)
    "IncusInstance",
    "InstanceType",
    "InstanceStatus",
    "InstanceSummary",
    "InstanceDevice",
    "InstanceUpdateRequest",
    # Legacy VM models
    "LegacyVM",
    "VMStatus",
    "LegacyVMSummary",
    "LegacyVMUpdateRequest",
]