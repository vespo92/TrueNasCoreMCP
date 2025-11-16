"""End-to-end integration tests."""

import pytest
from unittest.mock import AsyncMock, patch

from truenas_mcp_server.server import create_server
from truenas_mcp_server.config.settings import Settings
from pydantic import SecretStr


class TestEndToEnd:
    """Test end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_server_creation(self, mock_settings):
        """Test MCP server can be created."""
        with patch('truenas_mcp_server.server.get_client') as mock_get_client:
            mock_get_client.return_value = AsyncMock()
            server = create_server()
            assert server is not None

    @pytest.mark.asyncio
    async def test_pool_workflow(self, mock_truenas_client, mock_pool_response):
        """Test complete pool management workflow."""
        # Mock client responses
        mock_truenas_client.request = AsyncMock(side_effect=[
            mock_pool_response,  # list pools
            mock_pool_response[0],  # get pool details
        ])

        from truenas_mcp_server.tools.storage import StorageTools

        tools = StorageTools(client=mock_truenas_client, settings=mock_truenas_client.settings)

        # List pools
        pools_result = await tools.list_pools({})
        assert len(pools_result["pools"]) == 1

        # Get specific pool
        pool_result = await tools.get_pool({"pool_name": "tank"})
        assert pool_result["name"] == "tank"

    @pytest.mark.asyncio
    async def test_user_workflow(self, mock_truenas_client, mock_user_response):
        """Test complete user management workflow."""
        mock_truenas_client.request = AsyncMock(side_effect=[
            mock_user_response,  # list users
            {"id": 1001},  # create user
            mock_user_response[0],  # get user
        ])

        from truenas_mcp_server.tools.users import UserTools

        tools = UserTools(client=mock_truenas_client, settings=mock_truenas_client.settings)

        # List users
        users_result = await tools.list_users({})
        assert "users" in users_result

        # Note: Create/modify operations require actual implementation


class TestErrorHandlingIntegration:
    """Test error handling across components."""

    @pytest.mark.asyncio
    async def test_authentication_failure_propagation(self, mock_settings):
        """Test authentication errors propagate correctly."""
        from truenas_mcp_server.client.http_client import TrueNASClient
        from truenas_mcp_server.exceptions import TrueNASAuthenticationError

        client = TrueNASClient(settings=mock_settings)

        # Mock 401 response
        from unittest.mock import MagicMock
        import httpx

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=mock_response
        )

        client._client = AsyncMock()
        client._client.request.return_value = mock_response

        with pytest.raises(TrueNASAuthenticationError):
            await client.request("GET", "/api/v2.0/pool")

    @pytest.mark.asyncio
    async def test_network_error_handling(self, mock_settings):
        """Test network errors are handled properly."""
        from truenas_mcp_server.client.http_client import TrueNASClient
        from truenas_mcp_server.exceptions import TrueNASConnectionError
        import httpx

        client = TrueNASClient(settings=mock_settings)
        client._client = AsyncMock()
        client._client.request.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(TrueNASConnectionError):
            await client.request("GET", "/api/v2.0/pool")


class TestConfigurationIntegration:
    """Test configuration across components."""

    @pytest.mark.asyncio
    async def test_settings_propagation(self, mock_settings):
        """Test settings are properly propagated to components."""
        from truenas_mcp_server.client.http_client import TrueNASClient

        client = TrueNASClient(settings=mock_settings)
        assert client.settings.truenas_url == mock_settings.truenas_url
        assert client.settings.http_timeout == mock_settings.http_timeout

    @pytest.mark.asyncio
    async def test_feature_flags(self, mock_settings):
        """Test feature flags work across components."""
        # Test destructive operations flag
        mock_settings.enable_destructive_operations = False

        from truenas_mcp_server.tools.storage import StorageTools

        tools = StorageTools(client=AsyncMock(), settings=mock_settings)
        assert tools.settings.enable_destructive_operations is False
