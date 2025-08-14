"""
Base class and utilities for MCP tools
"""

import logging
from functools import wraps
from typing import Any, Dict, Optional, Callable
from abc import ABC, abstractmethod

from ..client import TrueNASClient
from ..config import Settings
from ..exceptions import TrueNASError
from ..models.base import ResponseModel

logger = logging.getLogger(__name__)


def tool_handler(func: Callable) -> Callable:
    """
    Decorator for handling tool execution with consistent error handling and logging
    
    Wraps tool methods to:
    - Log execution start/end
    - Handle exceptions consistently
    - Return standardized responses
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs) -> Dict[str, Any]:
        tool_name = func.__name__
        logger.info(f"Executing tool: {tool_name}")
        
        try:
            # Execute the tool function
            result = await func(self, *args, **kwargs)
            
            # Ensure we have a dict response
            if isinstance(result, ResponseModel):
                response = result.dict()
            elif isinstance(result, dict):
                response = result
            else:
                response = {"success": True, "data": result}
            
            logger.info(f"Tool {tool_name} completed successfully")
            return response
            
        except TrueNASError as e:
            logger.error(f"Tool {tool_name} failed with TrueNAS error: {e.message}")
            return {
                "success": False,
                "error": e.message,
                "error_type": e.__class__.__name__,
                "details": e.details
            }
        except Exception as e:
            logger.exception(f"Tool {tool_name} failed with unexpected error")
            return {
                "success": False,
                "error": str(e),
                "error_type": "UnexpectedError"
            }
    
    return wrapper


class BaseTool(ABC):
    """
    Base class for all MCP tools
    
    Provides common functionality for tool implementations including:
    - Client management
    - Configuration access
    - Logging setup
    - Error handling utilities
    """
    
    def __init__(self, client: Optional[TrueNASClient] = None, settings: Optional[Settings] = None):
        """
        Initialize the tool
        
        Args:
            client: Optional TrueNASClient instance
            settings: Optional Settings instance
        """
        self.client = client
        self.settings = settings
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._initialized = False
    
    async def initialize(self):
        """Initialize the tool (connect client, etc.)"""
        if not self._initialized:
            if self.client is None:
                from ..client import get_client
                self.client = await get_client()
            
            if self.settings is None:
                from ..config import get_settings
                self.settings = get_settings()
            
            self._initialized = True
            self.logger.debug(f"{self.__class__.__name__} initialized")
    
    async def ensure_initialized(self):
        """Ensure the tool is initialized before use"""
        if not self._initialized:
            await self.initialize()
    
    @abstractmethod
    def get_tool_definitions(self) -> list:
        """
        Get MCP tool definitions for this tool class
        
        Returns:
            List of tool definitions for MCP registration
        """
        pass
    
    def format_size(self, size_bytes: int) -> str:
        """
        Format bytes as human-readable size
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Human-readable size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} EB"
    
    def parse_size(self, size_str: str) -> int:
        """
        Parse human-readable size to bytes
        
        Args:
            size_str: Size string (e.g., "10G", "500M")
            
        Returns:
            Size in bytes
        """
        units = {
            'B': 1,
            'K': 1024,
            'KB': 1024,
            'M': 1024**2,
            'MB': 1024**2,
            'G': 1024**3,
            'GB': 1024**3,
            'T': 1024**4,
            'TB': 1024**4,
            'P': 1024**5,
            'PB': 1024**5
        }
        
        size_str = size_str.upper().strip()
        
        # Find the unit
        unit = None
        for u in sorted(units.keys(), key=len, reverse=True):
            if size_str.endswith(u):
                unit = u
                number_str = size_str[:-len(u)].strip()
                break
        
        if unit is None:
            # No unit specified, assume bytes
            return int(float(size_str))
        
        try:
            number = float(number_str)
            return int(number * units[unit])
        except ValueError:
            raise ValueError(f"Invalid size format: {size_str}")
    
    def validate_required_fields(self, data: Dict[str, Any], required: list) -> bool:
        """
        Validate that required fields are present in data
        
        Args:
            data: Data dictionary to validate
            required: List of required field names
            
        Returns:
            True if all required fields are present
            
        Raises:
            ValueError: If any required fields are missing
        """
        missing = [field for field in required if field not in data or data[field] is None]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        return True