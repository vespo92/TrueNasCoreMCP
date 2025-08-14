"""
Settings configuration using Pydantic for validation
"""

import os
from functools import lru_cache
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseSettings, Field, validator, HttpUrl
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
        env="TRUENAS_URL"
    )
    
    truenas_api_key: SecretStr = Field(
        ...,
        description="TrueNAS API key for authentication",
        env="TRUENAS_API_KEY"
    )
    
    truenas_verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates",
        env="TRUENAS_VERIFY_SSL"
    )
    
    # Application Settings
    environment: Environment = Field(
        default=Environment.PRODUCTION,
        description="Application environment",
        env="TRUENAS_ENV"
    )
    
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level",
        env="TRUENAS_LOG_LEVEL"
    )
    
    # HTTP Client Settings
    http_timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
        env="TRUENAS_HTTP_TIMEOUT"
    )
    
    http_max_retries: int = Field(
        default=3,
        description="Maximum number of HTTP retries",
        env="TRUENAS_HTTP_MAX_RETRIES"
    )
    
    http_pool_connections: int = Field(
        default=10,
        description="Number of connection pool connections",
        env="TRUENAS_HTTP_POOL_CONNECTIONS"
    )
    
    http_pool_maxsize: int = Field(
        default=20,
        description="Maximum size of the connection pool",
        env="TRUENAS_HTTP_POOL_MAXSIZE"
    )
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable rate limiting",
        env="TRUENAS_RATE_LIMIT_ENABLED"
    )
    
    rate_limit_requests: int = Field(
        default=100,
        description="Number of requests per window",
        env="TRUENAS_RATE_LIMIT_REQUESTS"
    )
    
    rate_limit_window: int = Field(
        default=60,
        description="Rate limit window in seconds",
        env="TRUENAS_RATE_LIMIT_WINDOW"
    )
    
    # Feature Flags
    enable_debug_tools: bool = Field(
        default=False,
        description="Enable debug tools in production",
        env="TRUENAS_ENABLE_DEBUG_TOOLS"
    )
    
    enable_destructive_operations: bool = Field(
        default=False,
        description="Enable potentially destructive operations",
        env="TRUENAS_ENABLE_DESTRUCTIVE_OPS"
    )
    
    @validator("truenas_url", pre=True)
    def validate_url(cls, v):
        """Ensure URL doesn't end with slash"""
        if isinstance(v, str):
            return v.rstrip("/")
        return v
    
    @validator("environment")
    def validate_debug_tools(cls, v, values):
        """Auto-enable debug tools in development"""
        if v == Environment.DEVELOPMENT:
            values["enable_debug_tools"] = True
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
    
    class Config:
        """Pydantic configuration"""
        env_prefix = "TRUENAS_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Allow extra fields for forward compatibility
        extra = "ignore"
        
        # Use enum values
        use_enum_values = True


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