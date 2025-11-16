"""Pytest configuration and fixtures for TrueNAS MCP Server tests."""

import asyncio
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import httpx
from pydantic import SecretStr

from truenas_mcp_server.config.settings import Settings
from truenas_mcp_server.client.http_client import TrueNASClient


# ============================================================================
# Pytest Configuration
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Settings Fixtures
# ============================================================================


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    return Settings(
        truenas_url="https://truenas.local",
        truenas_api_key=SecretStr("test-api-key-1234567890"),
        truenas_verify_ssl=False,
        environment="testing",
        log_level="DEBUG",
        enable_destructive_operations=True,
        http_timeout=30.0,
        http_pool_connections=10,
        http_pool_maxsize=20,
        http_max_retries=3,
        http_retry_backoff_factor=2.0,
    )


@pytest.fixture
def production_settings() -> Settings:
    """Create production-like settings for testing."""
    return Settings(
        truenas_url="https://truenas.example.com",
        truenas_api_key=SecretStr("prod-api-key-1234567890abcdef"),
        truenas_verify_ssl=True,
        environment="production",
        log_level="INFO",
        enable_destructive_operations=False,
        http_timeout=60.0,
    )


# ============================================================================
# HTTP Client Fixtures
# ============================================================================


@pytest.fixture
def mock_httpx_client() -> MagicMock:
    """Create a mock httpx.AsyncClient."""
    client = MagicMock(spec=httpx.AsyncClient)
    client.is_closed = False
    return client


@pytest.fixture
async def mock_truenas_client(mock_settings: Settings) -> AsyncGenerator[TrueNASClient, None]:
    """Create a mock TrueNAS HTTP client."""
    client = TrueNASClient(settings=mock_settings)
    # Don't actually connect
    client._client = AsyncMock(spec=httpx.AsyncClient)
    client._client.is_closed = False
    yield client
    # Clean up
    if not client._client.is_closed:
        await client.close()


# ============================================================================
# API Response Fixtures
# ============================================================================


@pytest.fixture
def mock_pool_response() -> Dict[str, Any]:
    """Mock response for pool list API."""
    return [
        {
            "id": 1,
            "name": "tank",
            "guid": "1234567890",
            "status": "ONLINE",
            "healthy": True,
            "size": 4000000000000,
            "allocated": 1000000000000,
            "free": 3000000000000,
            "fragmentation": "5%",
            "topology": {
                "data": [
                    {
                        "type": "MIRROR",
                        "children": [
                            {"type": "DISK", "path": "/dev/sda", "status": "ONLINE"},
                            {"type": "DISK", "path": "/dev/sdb", "status": "ONLINE"},
                        ],
                    }
                ],
            },
        }
    ]


@pytest.fixture
def mock_dataset_response() -> Dict[str, Any]:
    """Mock response for dataset list API."""
    return [
        {
            "id": "tank/data",
            "name": "data",
            "pool": "tank",
            "type": "FILESYSTEM",
            "used": {"parsed": 500000000000},
            "available": {"parsed": 2500000000000},
            "compression": "lz4",
            "readonly": {"value": "off"},
            "deduplication": {"value": "off"},
            "mountpoint": "/mnt/tank/data",
            "quota": {"parsed": None},
            "reservation": {"parsed": None},
        }
    ]


@pytest.fixture
def mock_user_response() -> Dict[str, Any]:
    """Mock response for user list API."""
    return [
        {
            "id": 1000,
            "uid": 1000,
            "username": "testuser",
            "full_name": "Test User",
            "email": "test@example.com",
            "locked": False,
            "sudo_commands": [],
            "sudo_commands_nopasswd": [],
            "shell": "/bin/bash",
            "home": "/mnt/tank/home/testuser",
            "group": {"id": 1000, "bsdgrp_gid": 1000, "bsdgrp_group": "testuser"},
            "groups": [1000],
        }
    ]


@pytest.fixture
def mock_snapshot_response() -> Dict[str, Any]:
    """Mock response for snapshot list API."""
    return [
        {
            "id": "tank/data@auto-2024-01-01-00-00",
            "name": "auto-2024-01-01-00-00",
            "dataset": "tank/data",
            "properties": {
                "used": {"parsed": 1000000},
                "referenced": {"parsed": 500000000000},
                "creation": {"parsed": "2024-01-01T00:00:00"},
            },
        }
    ]


@pytest.fixture
def mock_smb_share_response() -> Dict[str, Any]:
    """Mock response for SMB share list API."""
    return [
        {
            "id": 1,
            "path": "/mnt/tank/data",
            "name": "data",
            "comment": "Test SMB share",
            "enabled": True,
            "guestok": False,
            "ro": False,
            "browsable": True,
            "recyclebin": False,
            "hostsallow": [],
            "hostsdeny": [],
        }
    ]


# ============================================================================
# HTTP Response Fixtures
# ============================================================================


@pytest.fixture
def mock_http_response() -> MagicMock:
    """Create a mock HTTP response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {"status": "success"}
    response.text = '{"status": "success"}'
    return response


@pytest.fixture
def mock_error_response() -> MagicMock:
    """Create a mock error HTTP response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 500
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {"error": "Internal Server Error"}
    response.text = '{"error": "Internal Server Error"}'
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Internal Server Error", request=MagicMock(), response=response
    )
    return response


# ============================================================================
# Tool Test Helpers
# ============================================================================


@pytest.fixture
def mock_tool_arguments() -> Dict[str, Any]:
    """Common tool arguments for testing."""
    return {
        "pool_name": "tank",
        "dataset_name": "data",
        "username": "testuser",
        "snapshot_name": "auto-2024-01-01-00-00",
        "share_name": "data",
    }


# ============================================================================
# Async Helpers
# ============================================================================


@pytest.fixture
def async_return():
    """Helper to create async return values."""

    def _async_return(value):
        async def _wrapper():
            return value

        return _wrapper()

    return _async_return


# ============================================================================
# Exception Fixtures
# ============================================================================


@pytest.fixture
def mock_connection_error() -> httpx.ConnectError:
    """Create a mock connection error."""
    return httpx.ConnectError("Connection refused")


@pytest.fixture
def mock_timeout_error() -> httpx.TimeoutException:
    """Create a mock timeout error."""
    return httpx.TimeoutException("Request timeout")


@pytest.fixture
def mock_rate_limit_response() -> MagicMock:
    """Create a mock rate limit response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 429
    response.headers = {
        "content-type": "application/json",
        "X-RateLimit-Limit": "100",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1704067200",
    }
    response.json.return_value = {"error": "Rate limit exceeded"}
    response.text = '{"error": "Rate limit exceeded"}'
    return response
