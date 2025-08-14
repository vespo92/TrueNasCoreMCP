"""
Base models for TrueNAS MCP Server
"""

from typing import Any, Dict, Optional, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel as PydanticBaseModel, Field

T = TypeVar("T")


class BaseModel(PydanticBaseModel):
    """Base model with common configuration"""
    
    class Config:
        """Pydantic configuration"""
        # Allow population by field name or alias
        allow_population_by_field_name = True
        
        # Use enum values
        use_enum_values = True
        
        # Validate on assignment
        validate_assignment = True
        
        # JSON encoders for custom types
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
        # Schema extra
        schema_extra = {
            "example": {}
        }


class ResponseModel(BaseModel, Generic[T]):
    """
    Standard response model for all API responses
    
    Provides consistent response structure with success indicator,
    optional data, error information, and metadata.
    """
    
    success: bool = Field(
        ...,
        description="Indicates if the operation was successful"
    )
    
    data: Optional[T] = Field(
        None,
        description="Response data (present on success)"
    )
    
    error: Optional[str] = Field(
        None,
        description="Error message (present on failure)"
    )
    
    error_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata about the response"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    
    @classmethod
    def success_response(cls, data: T, metadata: Optional[Dict[str, Any]] = None) -> "ResponseModel[T]":
        """
        Create a successful response
        
        Args:
            data: Response data
            metadata: Optional metadata
            
        Returns:
            ResponseModel instance
        """
        return cls(
            success=True,
            data=data,
            metadata=metadata or {}
        )
    
    @classmethod
    def error_response(
        cls,
        error: str,
        error_details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ResponseModel[T]":
        """
        Create an error response
        
        Args:
            error: Error message
            error_details: Optional error details
            metadata: Optional metadata
            
        Returns:
            ResponseModel instance
        """
        return cls(
            success=False,
            error=error,
            error_details=error_details,
            metadata=metadata or {}
        )