"""Unit tests for HTTP client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from truenas_mcp_server.client.http_client import TrueNASClient
from truenas_mcp_server.exceptions import (
    TrueNASConnectionError,
    TrueNASAuthenticationError,
    TrueNASAPIError,
    TrueNASTimeoutError,
    TrueNASRateLimitError,
)


class TestTrueNASHTTPClient:
    """Test TrueNAS HTTP client."""

    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_settings):
        """Test client initialization with settings."""
        client = TrueNASClient(settings=mock_settings)
        assert client.settings == mock_settings
        assert client._client is None

    @pytest.mark.asyncio
    async def test_get_headers(self, mock_settings):
        """Test authentication headers are properly set."""
        client = TrueNASClient(settings=mock_settings)
        headers = client._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {mock_settings.truenas_api_key.get_secret_value()}"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_successful_get_request(self, mock_settings, mock_pool_response):
        """Test successful GET request."""
        client = TrueNASClient(settings=mock_settings)

        # Mock the httpx client
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_pool_response

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.request.return_value = mock_response

        result = await client.request("GET", "/api/v2.0/pool")

        assert result == mock_pool_response
        client._client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_authentication_error(self, mock_settings):
        """Test 401 authentication error handling."""
        client = TrueNASClient(settings=mock_settings)

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid API key"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=mock_response
        )

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.request.return_value = mock_response

        with pytest.raises(TrueNASAuthenticationError):
            await client.request("GET", "/api/v2.0/pool")

    @pytest.mark.asyncio
    async def test_403_permission_error(self, mock_settings):
        """Test 403 permission error handling."""
        client = TrueNASClient(settings=mock_settings)

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": "Forbidden"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden",
            request=MagicMock(),
            response=mock_response
        )

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.request.return_value = mock_response

        with pytest.raises(TrueNASAuthenticationError):
            await client.request("GET", "/api/v2.0/pool")

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, mock_settings, mock_rate_limit_response):
        """Test 429 rate limit error handling."""
        client = TrueNASClient(settings=mock_settings)

        mock_rate_limit_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=MagicMock(),
            response=mock_rate_limit_response
        )

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.request.return_value = mock_rate_limit_response

        with pytest.raises(TrueNASRateLimitError):
            await client.request("GET", "/api/v2.0/pool")

    @pytest.mark.asyncio
    async def test_timeout_error(self, mock_settings):
        """Test request timeout handling."""
        client = TrueNASClient(settings=mock_settings)

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.request.side_effect = httpx.TimeoutException("Request timeout")

        with pytest.raises(TrueNASTimeoutError):
            await client.request("GET", "/api/v2.0/pool")

    @pytest.mark.asyncio
    async def test_connection_error(self, mock_settings):
        """Test connection error handling."""
        client = TrueNASClient(settings=mock_settings)

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.request.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(TrueNASConnectionError):
            await client.request("GET", "/api/v2.0/pool")

    @pytest.mark.asyncio
    async def test_generic_http_error(self, mock_settings):
        """Test generic HTTP error handling."""
        client = TrueNASClient(settings=mock_settings)

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal Server Error"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=mock_response
        )

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.request.return_value = mock_response

        with pytest.raises(TrueNASAPIError):
            await client.request("GET", "/api/v2.0/pool")

    @pytest.mark.asyncio
    async def test_post_request_with_data(self, mock_settings):
        """Test POST request with JSON data."""
        client = TrueNASClient(settings=mock_settings)

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "name": "test"}

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.request.return_value = mock_response

        data = {"name": "test", "value": 123}
        result = await client.request("POST", "/api/v2.0/test", json=data)

        assert result == {"id": 1, "name": "test"}

        # Verify the request was made with correct data
        call_kwargs = client._client.request.call_args[1]
        assert call_kwargs["json"] == data

    @pytest.mark.asyncio
    async def test_client_context_manager(self, mock_settings):
        """Test client as async context manager."""
        async with TrueNASClient(settings=mock_settings) as client:
            assert client is not None
            client._client = AsyncMock(spec=httpx.AsyncClient)
            client._client.is_closed = False

    @pytest.mark.asyncio
    async def test_client_close(self, mock_settings):
        """Test client close functionality."""
        client = TrueNASClient(settings=mock_settings)
        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.is_closed = False

        await client.close()

        client._client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_logic(self, mock_settings):
        """Test retry logic for transient failures."""
        client = TrueNASClient(settings=mock_settings)

        # First two calls fail, third succeeds
        mock_response_success = MagicMock(spec=httpx.Response)
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"status": "success"}

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.request.side_effect = [
            httpx.ConnectError("Connection failed"),
            httpx.ConnectError("Connection failed"),
            mock_response_success
        ]

        # Should succeed after retries
        result = await client.request("GET", "/api/v2.0/pool")
        assert result == {"status": "success"}
        assert client._client.request.call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_client_error(self, mock_settings):
        """Test that client errors (4xx) are not retried."""
        client = TrueNASClient(settings=mock_settings)

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad request"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request",
            request=MagicMock(),
            response=mock_response
        )

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.request.return_value = mock_response

        with pytest.raises(TrueNASAPIError):
            await client.request("GET", "/api/v2.0/pool")

        # Should only be called once (no retries for 4xx)
        assert client._client.request.call_count == 1


class TestClientConfiguration:
    """Test client configuration options."""

    @pytest.mark.asyncio
    async def test_ssl_verification_enabled(self, production_settings):
        """Test SSL verification is enabled in production."""
        client = TrueNASClient(settings=production_settings)
        assert production_settings.truenas_verify_ssl is True

    @pytest.mark.asyncio
    async def test_ssl_verification_disabled(self, mock_settings):
        """Test SSL verification can be disabled."""
        client = TrueNASClient(settings=mock_settings)
        assert mock_settings.truenas_verify_ssl is False

    @pytest.mark.asyncio
    async def test_custom_timeout(self, mock_settings):
        """Test custom timeout settings."""
        mock_settings.http_timeout = 120.0
        client = TrueNASClient(settings=mock_settings)
        assert mock_settings.http_timeout == 120.0

    @pytest.mark.asyncio
    async def test_connection_pool_settings(self, mock_settings):
        """Test connection pool configuration."""
        assert mock_settings.http_pool_connections == 10
        assert mock_settings.http_pool_maxsize == 20
