"""
User models for TrueNAS MCP Server
"""

from typing import Optional, List
from pydantic import Field, validator
from .base import BaseModel


class User(BaseModel):
    """User model representing a TrueNAS user"""
    
    id: int = Field(..., description="User ID")
    uid: int = Field(..., description="Unix user ID")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    shell: str = Field("/bin/sh", description="User shell")
    home: str = Field(..., description="Home directory path")
    groups: List[int] = Field(default_factory=list, description="Group IDs")
    sudo: bool = Field(False, description="Has sudo privileges")
    locked: bool = Field(False, description="Account is locked")
    builtin: bool = Field(False, description="Is a built-in system user")
    microsoft_account: bool = Field(False, description="Is a Microsoft account")
    sshpubkey: Optional[str] = Field(None, description="SSH public key")
    
    @validator("shell")
    def validate_shell(cls, v):
        """Validate shell path"""
        valid_shells = ["/bin/sh", "/bin/bash", "/bin/csh", "/bin/tcsh", "/bin/zsh", "/usr/bin/bash", "/usr/sbin/nologin"]
        if v not in valid_shells:
            raise ValueError(f"Invalid shell: {v}")
        return v
    
    @validator("home")
    def validate_home(cls, v):
        """Validate home directory path"""
        if not v.startswith("/"):
            raise ValueError("Home directory must be an absolute path")
        return v


class UserCreate(BaseModel):
    """Model for creating a new user"""
    
    username: str = Field(..., min_length=1, max_length=32, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    full_name: Optional[str] = Field(None, max_length=128, description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    shell: str = Field("/bin/bash", description="User shell")
    home: Optional[str] = Field(None, description="Home directory (auto-generated if not specified)")
    groups: Optional[List[int]] = Field(None, description="Group IDs to add user to")
    sudo: bool = Field(False, description="Grant sudo privileges")
    sshpubkey: Optional[str] = Field(None, description="SSH public key")
    
    @validator("username")
    def validate_username(cls, v):
        """Validate username format"""
        import re
        if not re.match(r"^[a-z][a-z0-9_-]*$", v):
            raise ValueError("Username must start with lowercase letter and contain only lowercase letters, numbers, underscore, and hyphen")
        return v
    
    @validator("email")
    def validate_email(cls, v):
        """Validate email format"""
        if v:
            import re
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
                raise ValueError("Invalid email format")
        return v


class UserUpdate(BaseModel):
    """Model for updating an existing user"""
    
    full_name: Optional[str] = Field(None, max_length=128, description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    password: Optional[str] = Field(None, min_length=8, description="New password")
    shell: Optional[str] = Field(None, description="User shell")
    home: Optional[str] = Field(None, description="Home directory")
    groups: Optional[List[int]] = Field(None, description="Group IDs")
    sudo: Optional[bool] = Field(None, description="Sudo privileges")
    locked: Optional[bool] = Field(None, description="Lock/unlock account")
    sshpubkey: Optional[str] = Field(None, description="SSH public key")