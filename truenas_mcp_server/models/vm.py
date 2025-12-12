"""
TrueNAS Legacy VM models for bhyve-based virtual machines

TrueNAS SCALE uses bhyve for legacy VMs via /api/v2.0/vm.
New deployments should use Incus VMs (/api/v2.0/virt/instance) instead.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseModel


class VMStatus(str, Enum):
    """Legacy VM runtime states"""
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    SUSPENDED = "SUSPENDED"


class VMBootloader(str, Enum):
    """VM bootloader types"""
    UEFI = "UEFI"
    UEFI_CSM = "UEFI_CSM"


class VMDeviceType(str, Enum):
    """Types of devices in legacy VMs"""
    DISK = "DISK"
    CDROM = "CDROM"
    NIC = "NIC"
    RAW = "RAW"
    DISPLAY = "DISPLAY"
    USB = "USB"


class VMDevice(BaseModel):
    """
    Device attached to a legacy VM
    """
    id: int = Field(..., description="Device ID")
    dtype: VMDeviceType = Field(..., description="Device type")
    order: int = Field(default=1000, description="Device order")
    vm: int = Field(..., description="Parent VM ID")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Device-specific attributes"
    )


class LegacyVM(BaseModel):
    """
    Legacy bhyve VM model

    Represents a virtual machine managed by bhyve on TrueNAS.
    Note: New deployments should use Incus VMs instead.
    """
    id: int = Field(..., description="VM numeric ID")
    name: str = Field(..., description="VM name")
    description: Optional[str] = Field(None, description="VM description")
    vcpus: int = Field(default=1, description="Number of virtual CPUs")
    memory: int = Field(
        default=512,
        description="Memory in MB"
    )
    min_memory: Optional[int] = Field(None, description="Minimum memory for ballooning")
    autostart: bool = Field(default=False, description="Start on boot")
    time: str = Field(default="LOCAL", description="Time sync (LOCAL/UTC)")
    bootloader: VMBootloader = Field(
        default=VMBootloader.UEFI,
        description="Bootloader type"
    )
    bootloader_ovmf: Optional[str] = Field(None, description="Custom OVMF path")
    shutdown_timeout: int = Field(
        default=90,
        description="Shutdown timeout in seconds"
    )
    cpu_mode: str = Field(default="CUSTOM", description="CPU emulation mode")
    cpu_model: Optional[str] = Field(None, description="CPU model to emulate")
    hide_from_msr: bool = Field(
        default=False,
        description="Hide hypervisor from guest"
    )
    hyperv_enlightenments: bool = Field(
        default=False,
        description="Enable Hyper-V enlightenments"
    )
    ensure_display_device: bool = Field(
        default=True,
        description="Ensure display device exists"
    )
    arch_type: Optional[str] = Field(None, description="Architecture type")
    machine_type: Optional[str] = Field(None, description="Machine type")
    uuid: Optional[str] = Field(None, description="VM UUID")
    status: Optional[VMStatus] = Field(None, description="Current status")
    devices: List[VMDevice] = Field(
        default_factory=list,
        description="Attached devices"
    )


class LegacyVMSummary(BaseModel):
    """
    Summary information about a legacy VM for list operations
    """
    id: int = Field(..., description="VM ID")
    name: str = Field(..., description="VM name")
    status: str = Field(..., description="Current status")
    vcpus: int = Field(..., description="Number of vCPUs")
    memory_mb: int = Field(..., description="Memory in MB")
    autostart: bool = Field(..., description="Autostart enabled")
    description: Optional[str] = Field(None, description="VM description")


class LegacyVMUpdateRequest(BaseModel):
    """
    Request model for updating legacy VM configuration

    Only the fields provided will be updated.
    """
    name: Optional[str] = Field(None, description="VM name")
    description: Optional[str] = Field(None, description="VM description")
    vcpus: Optional[int] = Field(None, description="Number of vCPUs")
    memory: Optional[int] = Field(None, description="Memory in MB")
    autostart: Optional[bool] = Field(None, description="Start on boot")
    shutdown_timeout: Optional[int] = Field(
        None,
        description="Shutdown timeout in seconds"
    )
