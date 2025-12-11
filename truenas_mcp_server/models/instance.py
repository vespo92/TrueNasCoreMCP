"""
TrueNAS Incus Instance models for VMs and Containers

TrueNAS SCALE 25.04+ uses Incus for virtualization via /api/v2.0/virt/instance.
This replaces the older bhyve-based /api/v2.0/vm API for new deployments.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseModel


class InstanceType(str, Enum):
    """Incus instance types"""
    VM = "VM"
    CONTAINER = "CONTAINER"


class InstanceStatus(str, Enum):
    """Instance runtime states"""
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    STOPPING = "STOPPING"
    ERROR = "ERROR"


class DeviceType(str, Enum):
    """Types of devices that can be attached to instances"""
    DISK = "DISK"
    NIC = "NIC"
    GPU = "GPU"
    USB = "USB"
    TPM = "TPM"
    PROXY = "PROXY"


class InstanceDevice(BaseModel):
    """
    Device attached to an Incus instance
    """
    name: str = Field(..., description="Device name")
    type: DeviceType = Field(..., description="Device type")
    source: Optional[str] = Field(None, description="Source path or identifier")
    destination: Optional[str] = Field(None, description="Destination path in instance")
    readonly: bool = Field(default=False, description="Read-only mount")
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional device-specific configuration"
    )


class InstanceNIC(BaseModel):
    """
    Network interface configuration for an instance
    """
    name: str = Field(..., description="Interface name")
    type: str = Field(default="bridged", description="NIC type")
    parent: Optional[str] = Field(None, description="Parent bridge/network")
    hwaddr: Optional[str] = Field(None, description="MAC address")


class IncusInstance(BaseModel):
    """
    Incus Instance model (VM or Container)

    Represents a virtualization instance managed by Incus on TrueNAS.
    """
    id: str = Field(..., description="Instance identifier (same as name)")
    name: str = Field(..., description="Instance name")
    type: InstanceType = Field(..., description="Instance type (VM or CONTAINER)")
    status: InstanceStatus = Field(..., description="Current runtime status")
    cpu: str = Field(default="2", description="Number of CPU cores as string")
    memory: int = Field(
        default=4294967296,
        description="Memory in bytes (default 4GB)"
    )
    autostart: bool = Field(default=True, description="Start on boot")
    image: Optional[str] = Field(None, description="Base image used")
    environment: Dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables"
    )
    devices: List[InstanceDevice] = Field(
        default_factory=list,
        description="Attached devices"
    )
    nics: List[InstanceNIC] = Field(
        default_factory=list,
        description="Network interfaces"
    )
    raw: Optional[Dict[str, Any]] = Field(
        None,
        description="Raw API response for additional fields"
    )


class InstanceSummary(BaseModel):
    """
    Summary information about an instance for list operations
    """
    id: str = Field(..., description="Instance ID")
    name: str = Field(..., description="Instance name")
    type: str = Field(..., description="Instance type (VM/CONTAINER)")
    status: str = Field(..., description="Current status")
    cpu: str = Field(..., description="CPU allocation")
    memory_gb: float = Field(..., description="Memory in GB")
    autostart: bool = Field(..., description="Autostart enabled")


class InstanceUpdateRequest(BaseModel):
    """
    Request model for updating instance configuration

    Only the fields provided will be updated.
    """
    cpu: Optional[str] = Field(None, description="Number of CPU cores")
    memory: Optional[int] = Field(None, description="Memory in bytes")
    autostart: Optional[bool] = Field(None, description="Start on boot")
    environment: Optional[Dict[str, str]] = Field(
        None,
        description="Environment variables"
    )
