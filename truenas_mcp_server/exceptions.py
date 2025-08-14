"""
Custom exception hierarchy for TrueNAS MCP Server
"""

from typing import Optional, Dict, Any


class TrueNASError(Exception):
    """Base exception for all TrueNAS MCP errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class TrueNASConnectionError(TrueNASError):
    """Raised when connection to TrueNAS fails"""
    pass


class TrueNASAuthenticationError(TrueNASError):
    """Raised when authentication fails"""
    pass


class TrueNASAPIError(TrueNASError):
    """Raised when TrueNAS API returns an error"""
    pass


class TrueNASTimeoutError(TrueNASError):
    """Raised when a request times out"""
    pass


class TrueNASRateLimitError(TrueNASError):
    """Raised when rate limit is exceeded"""
    pass


class TrueNASValidationError(TrueNASError):
    """Raised when input validation fails"""
    pass


class TrueNASNotFoundError(TrueNASError):
    """Raised when a resource is not found"""
    pass


class TrueNASPermissionError(TrueNASError):
    """Raised when operation is not permitted"""
    pass


class TrueNASConfigurationError(TrueNASError):
    """Raised when configuration is invalid"""
    pass