"""
TrueNAS App models for Docker Compose-based applications

TrueNAS SCALE 25.04+ uses the /api/v2.0/app endpoints for app management.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseModel


class AppState(str, Enum):
    """Application deployment states"""
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    DEPLOYING = "DEPLOYING"
    CRASHED = "CRASHED"
    STOPPING = "STOPPING"
    STARTING = "STARTING"


class AppResourceLimits(BaseModel):
    """Resource limits for an app"""
    cpus: int = Field(default=2, description="Number of CPU cores")
    memory: int = Field(default=4096, description="Memory limit in MB")


class AppResources(BaseModel):
    """Resource configuration for an app"""
    limits: AppResourceLimits = Field(
        default_factory=AppResourceLimits,
        description="Resource limits"
    )


class AppStorageMount(BaseModel):
    """Storage mount configuration for an app"""
    mount_path: str = Field(..., description="Path inside container")
    path: str = Field(..., description="Host path")
    read_only: bool = Field(default=False, description="Whether mount is read-only")


class AppStorageConfig(BaseModel):
    """Storage configuration for an app"""
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Config storage settings"
    )
    additional: List[AppStorageMount] = Field(
        default_factory=list,
        description="Additional storage mounts"
    )


class AppNetworkConfig(BaseModel):
    """Network configuration for an app"""
    host_network: bool = Field(default=False, description="Use host network")
    port: Optional[int] = Field(None, description="Primary port mapping")


class AppRunAsConfig(BaseModel):
    """User/group configuration for an app"""
    user: int = Field(..., description="UID to run as")
    group: int = Field(..., description="GID to run as")


class App(BaseModel):
    """
    TrueNAS App model

    Represents a Docker Compose-based application managed by TrueNAS.
    """
    id: str = Field(..., description="App identifier (same as name)")
    name: str = Field(..., description="App name")
    state: AppState = Field(..., description="Current deployment state")
    version: Optional[str] = Field(None, description="App version")
    human_version: Optional[str] = Field(None, description="Human-readable version")
    upgrade_available: bool = Field(default=False, description="Whether upgrade is available")
    portal: Optional[Dict[str, Any]] = Field(None, description="Web portal information")
    metadata: Optional[Dict[str, Any]] = Field(None, description="App metadata")


class AppConfig(BaseModel):
    """
    Full app configuration as returned by /app/config endpoint

    This is the complete configuration structure that can be retrieved
    and modified via the TrueNAS API.
    """
    resources: Optional[AppResources] = Field(None, description="Resource configuration")
    storage: Optional[Dict[str, Any]] = Field(None, description="Storage configuration")
    network: Optional[Dict[str, Any]] = Field(None, description="Network configuration")
    run_as: Optional[Dict[str, Any]] = Field(None, description="Run as configuration")
    timezone: Optional[str] = Field(None, description="App timezone")

    # Additional fields vary by app type - stored as extra
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional app-specific configuration"
    )


class AppSummary(BaseModel):
    """
    Summary information about an app for list operations
    """
    name: str = Field(..., description="App name")
    state: str = Field(..., description="Current state")
    version: Optional[str] = Field(None, description="App version")
    upgrade_available: bool = Field(default=False, description="Upgrade available")
    portal_url: Optional[str] = Field(None, description="Web portal URL if available")
