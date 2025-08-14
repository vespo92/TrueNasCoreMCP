"""
Sharing models for TrueNAS MCP Server
"""

from typing import Optional, List, Dict, Any
from pydantic import Field, validator
from .base import BaseModel


class SMBShare(BaseModel):
    """SMB/CIFS share model"""
    
    id: int = Field(..., description="Share ID")
    name: str = Field(..., description="Share name")
    path: str = Field(..., description="Share path")
    comment: Optional[str] = Field("", description="Share comment")
    enabled: bool = Field(True, description="Share enabled status")
    ro: bool = Field(False, description="Read-only")
    browsable: bool = Field(True, description="Browsable in network neighborhood")
    guestok: bool = Field(False, description="Allow guest access")
    hostsallow: List[str] = Field(default_factory=list, description="Allowed hosts/networks")
    hostsdeny: List[str] = Field(default_factory=list, description="Denied hosts/networks")
    home: bool = Field(False, description="Home share")
    timemachine: bool = Field(False, description="Time Machine backup share")
    recyclebin: bool = Field(False, description="Enable recycle bin")
    shadowcopy: bool = Field(False, description="Enable shadow copies")
    audit: Dict[str, Any] = Field(default_factory=dict, description="Audit settings")
    
    @validator("path")
    def validate_path(cls, v):
        """Validate share path"""
        if not v.startswith("/mnt/"):
            raise ValueError("Share path must start with /mnt/")
        return v
    
    @validator("name")
    def validate_name(cls, v):
        """Validate share name"""
        import re
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$", v):
            raise ValueError("Share name must start with alphanumeric and contain only alphanumeric, underscore, dot, and hyphen")
        return v


class NFSExport(BaseModel):
    """NFS export model"""
    
    id: int = Field(..., description="Export ID")
    path: str = Field(..., description="Export path")
    comment: Optional[str] = Field("", description="Export comment")
    enabled: bool = Field(True, description="Export enabled status")
    ro: bool = Field(False, description="Read-only")
    maproot_user: Optional[str] = Field("root", description="Map root user to")
    maproot_group: Optional[str] = Field("wheel", description="Map root group to")
    mapall_user: Optional[str] = Field(None, description="Map all users to")
    mapall_group: Optional[str] = Field(None, description="Map all groups to")
    networks: List[str] = Field(default_factory=list, description="Allowed networks")
    hosts: List[str] = Field(default_factory=list, description="Allowed hosts")
    alldirs: bool = Field(False, description="Allow mounting subdirectories")
    quiet: bool = Field(False, description="Suppress some warnings")
    security: List[str] = Field(default_factory=lambda: ["sys"], description="Security flavors")
    
    @validator("path")
    def validate_path(cls, v):
        """Validate export path"""
        if not v.startswith("/mnt/"):
            raise ValueError("Export path must start with /mnt/")
        return v
    
    @validator("networks")
    def validate_networks(cls, v):
        """Validate network format"""
        import re
        cidr_pattern = r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$"
        for network in v:
            if network != "0.0.0.0/0" and not re.match(cidr_pattern, network):
                raise ValueError(f"Invalid network format: {network}")
        return v


class ISCSITarget(BaseModel):
    """iSCSI target model"""
    
    id: int = Field(..., description="Target ID")
    name: str = Field(..., description="Target IQN")
    alias: Optional[str] = Field(None, description="Target alias")
    mode: str = Field("ISCSI", description="Target mode")
    groups: List[Dict[str, Any]] = Field(default_factory=list, description="Initiator groups")
    
    @validator("name")
    def validate_iqn(cls, v):
        """Validate IQN format"""
        import re
        iqn_pattern = r"^iqn\.\d{4}-\d{2}\.[a-z0-9.-]+:[a-z0-9.-]+$"
        if not re.match(iqn_pattern, v.lower()):
            raise ValueError(f"Invalid IQN format: {v}")
        return v


class ISCSIExtent(BaseModel):
    """iSCSI extent (LUN) model"""
    
    id: int = Field(..., description="Extent ID")
    name: str = Field(..., description="Extent name")
    type: str = Field("DISK", description="Extent type (DISK or FILE)")
    disk: Optional[str] = Field(None, description="Disk/zvol path")
    path: Optional[str] = Field(None, description="File path")
    filesize: Optional[int] = Field(None, description="File size in bytes")
    blocksize: int = Field(512, description="Block size")
    pblocksize: bool = Field(False, description="Physical block size reporting")
    avail_threshold: Optional[int] = Field(None, description="Available threshold")
    comment: Optional[str] = Field("", description="Comment")
    enabled: bool = Field(True, description="Enabled status")
    ro: bool = Field(False, description="Read-only")
    rpm: str = Field("SSD", description="RPM type")
    
    @validator("blocksize")
    def validate_blocksize(cls, v):
        """Validate block size"""
        valid_sizes = [512, 1024, 2048, 4096]
        if v not in valid_sizes:
            raise ValueError(f"Invalid block size: {v}")
        return v
    
    @validator("rpm")
    def validate_rpm(cls, v):
        """Validate RPM type"""
        valid_rpms = ["UNKNOWN", "SSD", "5400", "7200", "10000", "15000"]
        if v not in valid_rpms:
            raise ValueError(f"Invalid RPM type: {v}")
        return v