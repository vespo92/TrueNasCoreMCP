"""
Settings configuration using Pydantic for validation
"""

import os
from functools import lru_cache
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import Field, field_validator, HttpUrl
from pydantic_settings import BaseSettings
from pydantic.types import SecretStr


class LogLevel(str, Enum):
    """Logging level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Application environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Application settings with validation
    
    Settings are loaded from environment variables with TRUENAS_ prefix
    """
    
    # TrueNAS Connection Settings  
    truenas_url: HttpUrl = Field(
        default="https://truenas.local",
        description="TrueNAS server URL",
        validation_alias="TRUENAS_URL"
    )
    
    truenas_api_key: SecretStr = Field(
        ...,
        description="TrueNAS API key for authentication",
        validation_alias="TRUENAS_API_KEY"
    )
    
    truenas_verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates",
        validation_alias="TRUENAS_VERIFY_SSL"
    )
    
    # Application Settings
    environment: Environment = Field(
        default=Environment.PRODUCTION,
        description="Application environment",
        validation_alias="TRUENAS_ENV"
    )
    
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level",
        validation_alias="TRUENAS_LOG_LEVEL"
    )
    
    # HTTP Client Settings
    http_timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds"
    )
    
    http_max_retries: int = Field(
        default=3,
        description="Maximum number of HTTP retries"
    )
    
    http_pool_connections: int = Field(
        default=10,
        description="Number of connection pool connections"
    )
    
    http_pool_maxsize: int = Field(
        default=20,
        description="Maximum size of the connection pool"
    )
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable rate limiting",
    )
    
    rate_limit_requests: int = Field(
        default=100,
        description="Number of requests per window",
    )
    
    rate_limit_window: int = Field(
        default=60,
        description="Rate limit window in seconds",
    )
    
    # Feature Flags
    enable_debug_tools: bool = Field(
        default=False,
        description="Enable debug tools in production",
    )
    
    enable_destructive_operations: bool = Field(
        default=False,
        description="Enable potentially destructive operations",
    )
    
    @field_validator("truenas_url", mode="before")
    def validate_url(cls, v):
        """Ensure URL doesn't end with slash"""
        if isinstance(v, str):
            return v.rstrip("/")
        return v
    
    @field_validator("environment")
    def validate_debug_tools(cls, v):
        """Auto-enable debug tools in development"""
        # Note: In Pydantic v2, we can't modify other fields in validators
        # This logic should be in a model_validator or handled differently
        return v
    
    @property
    def api_base_url(self) -> str:
        """Get the full API base URL"""
        return f"{self.truenas_url}/api/v2.0"
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests"""
        return {
            "Authorization": f"Bearer {self.truenas_api_key.get_secret_value()}",
            "Content-Type": "application/json",
            "User-Agent": f"TrueNAS-MCP-Server/{self.get_version()}"
        }
    
    def get_version(self) -> str:
        """Get the package version"""
        from .. import __version__
        return __version__
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "use_enum_values": True,
        "populate_by_name": True
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    
    Returns a singleton Settings instance that's cached for the application lifetime
    """
    return Settings()


def reload_settings() -> Settings:
    """
    Force reload settings (useful for testing)
    
    Clears the cache and returns a new Settings instance
    """
    get_settings.cache_clear()
    return get_settings()