"""
Storage models for TrueNAS MCP Server
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import Field, validator
from .base import BaseModel


class PoolStatus(str, Enum):
    """Pool status enumeration"""
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    FAULTED = "FAULTED"
    OFFLINE = "OFFLINE"
    UNAVAIL = "UNAVAIL"
    REMOVED = "REMOVED"


class CompressionType(str, Enum):
    """Compression type enumeration"""
    OFF = "off"
    LZ4 = "lz4"
    GZIP = "gzip"
    GZIP_1 = "gzip-1"
    GZIP_9 = "gzip-9"
    ZSTD = "zstd"
    ZSTD_FAST = "zstd-fast"
    ZLE = "zle"
    LZJB = "lzjb"


class DeduplicationType(str, Enum):
    """Deduplication type enumeration"""
    OFF = "off"
    ON = "on"
    VERIFY = "verify"


class SyncType(str, Enum):
    """Sync type enumeration"""
    STANDARD = "standard"
    ALWAYS = "always"
    DISABLED = "disabled"


class Pool(BaseModel):
    """Storage pool model"""
    
    id: int = Field(..., description="Pool ID")
    name: str = Field(..., description="Pool name")
    guid: str = Field(..., description="Pool GUID")
    status: PoolStatus = Field(..., description="Pool status")
    healthy: bool = Field(..., description="Pool health status")
    size: int = Field(..., description="Total size in bytes")
    allocated: int = Field(..., description="Allocated space in bytes")
    free: int = Field(..., description="Free space in bytes")
    fragmentation: Optional[int] = Field(None, description="Fragmentation percentage")
    encrypted: bool = Field(False, description="Encryption status")
    topology: Dict[str, List[Dict[str, Any]]] = Field(..., description="Pool topology")
    scan: Optional[Dict[str, Any]] = Field(None, description="Scrub/resilver status")
    
    @property
    def usage_percent(self) -> float:
        """Calculate usage percentage"""
        if self.size > 0:
            return round((self.allocated / self.size) * 100, 2)
        return 0.0
    
    @property
    def health_status(self) -> str:
        """Get health status description"""
        if self.healthy and self.status == PoolStatus.ONLINE:
            return "Healthy"
        elif self.status == PoolStatus.DEGRADED:
            return "Degraded - Check disk status"
        elif self.status == PoolStatus.FAULTED:
            return "Faulted - Immediate attention required"
        else:
            return f"Status: {self.status}"


class Dataset(BaseModel):
    """Dataset model"""
    
    id: str = Field(..., description="Dataset ID")
    name: str = Field(..., description="Dataset name")
    pool: str = Field(..., description="Parent pool name")
    type: str = Field("FILESYSTEM", description="Dataset type")
    mountpoint: Optional[str] = Field(None, description="Mount point")
    compression: CompressionType = Field(CompressionType.LZ4, description="Compression type")
    deduplication: DeduplicationType = Field(DeduplicationType.OFF, description="Deduplication")
    encrypted: bool = Field(False, description="Encryption status")
    quota: Optional[int] = Field(None, description="Quota in bytes")
    refquota: Optional[int] = Field(None, description="Reference quota in bytes")
    reservation: Optional[int] = Field(None, description="Reservation in bytes")
    refreservation: Optional[int] = Field(None, description="Reference reservation in bytes")
    recordsize: str = Field("128K", description="Record size")
    atime: bool = Field(True, description="Access time updates")
    sync: SyncType = Field(SyncType.STANDARD, description="Sync mode")
    readonly: bool = Field(False, description="Read-only status")
    exec: bool = Field(True, description="Allow execution")
    used: int = Field(0, description="Used space in bytes")
    available: int = Field(0, description="Available space in bytes")
    referenced: int = Field(0, description="Referenced space in bytes")
    children: List[str] = Field(default_factory=list, description="Child datasets")
    
    @validator("recordsize")
    def validate_recordsize(cls, v):
        """Validate record size"""
        valid_sizes = ["512", "1K", "2K", "4K", "8K", "16K", "32K", "64K", "128K", "256K", "512K", "1M"]
        if v not in valid_sizes:
            raise ValueError(f"Invalid record size: {v}")
        return v


class DatasetCreate(BaseModel):
    """Model for creating a dataset"""
    
    name: str = Field(..., description="Dataset name (relative to pool)")
    pool: str = Field(..., description="Pool name")
    type: str = Field("FILESYSTEM", description="Dataset type")
    compression: CompressionType = Field(CompressionType.LZ4, description="Compression type")
    deduplication: DeduplicationType = Field(DeduplicationType.OFF, description="Deduplication")
    quota: Optional[str] = Field(None, description="Quota (e.g., '10G')")
    recordsize: str = Field("128K", description="Record size")
    atime: bool = Field(True, description="Access time updates")
    sync: SyncType = Field(SyncType.STANDARD, description="Sync mode")
    readonly: bool = Field(False, description="Read-only")
    exec: bool = Field(True, description="Allow execution")
    casesensitivity: str = Field("sensitive", description="Case sensitivity")
    
    @validator("name")
    def validate_name(cls, v):
        """Validate dataset name"""
        import re
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$", v):
            raise ValueError("Dataset name must start with alphanumeric and contain only alphanumeric, underscore, dot, and hyphen")
        return v
    
    @property
    def full_path(self) -> str:
        """Get full dataset path"""
        return f"{self.pool}/{self.name}"


class Snapshot(BaseModel):
    """Snapshot model"""
    
    name: str = Field(..., description="Full snapshot name (dataset@snapshot)")
    dataset: str = Field(..., description="Parent dataset")
    snapshot: str = Field(..., description="Snapshot name")
    created: int = Field(..., description="Creation timestamp")
    referenced: Optional[int] = Field(None, description="Referenced size in bytes")
    used: Optional[int] = Field(None, description="Used space in bytes")
    holds: List[str] = Field(default_factory=list, description="Snapshot holds")
    
    @validator("name")
    def validate_name(cls, v):
        """Validate snapshot name format"""
        if "@" not in v:
            raise ValueError("Snapshot name must be in format 'dataset@snapshot'")
        return v
    
    @property
    def age_days(self) -> int:
        """Calculate snapshot age in days"""
        from datetime import datetime
        now = datetime.now().timestamp()
        return int((now - self.created) / 86400)