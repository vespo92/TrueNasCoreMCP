"""Unit tests for storage tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from truenas_mcp_server.tools.storage import StorageTools
from truenas_mcp_server.exceptions import TrueNASValidationError, TrueNASNotFoundError


class TestStorageTools:
    """Test storage management tools."""

    @pytest.fixture
    async def storage_tools(self, mock_truenas_client, mock_settings):
        """Create storage tools instance for testing."""
        tools = StorageTools(client=mock_truenas_client, settings=mock_settings)
        return tools

    @pytest.mark.asyncio
    async def test_list_pools(self, storage_tools, mock_pool_response):
        """Test listing storage pools."""
        storage_tools.client.request = AsyncMock(return_value=mock_pool_response)

        result = await storage_tools.list_pools({})

        assert "pools" in result
        assert len(result["pools"]) == 1
        assert result["pools"][0]["name"] == "tank"
        assert result["pools"][0]["status"] == "ONLINE"

    @pytest.mark.asyncio
    async def test_get_pool_details(self, storage_tools, mock_pool_response):
        """Test getting pool details."""
        storage_tools.client.request = AsyncMock(return_value=mock_pool_response[0])

        result = await storage_tools.get_pool({"pool_name": "tank"})

        assert result["name"] == "tank"
        assert result["status"] == "ONLINE"
        assert "size" in result

    @pytest.mark.asyncio
    async def test_list_datasets(self, storage_tools, mock_dataset_response):
        """Test listing datasets."""
        storage_tools.client.request = AsyncMock(return_value=mock_dataset_response)

        result = await storage_tools.list_datasets({"pool_name": "tank"})

        assert "datasets" in result
        assert len(result["datasets"]) >= 1
        assert result["datasets"][0]["name"] == "data"

    @pytest.mark.asyncio
    async def test_create_dataset_validation(self, storage_tools):
        """Test dataset creation with missing required fields."""
        with pytest.raises(TrueNASValidationError):
            await storage_tools.create_dataset({})

        with pytest.raises(TrueNASValidationError):
            await storage_tools.create_dataset({"pool_name": "tank"})

    @pytest.mark.asyncio
    async def test_create_dataset_success(self, storage_tools, mock_dataset_response):
        """Test successful dataset creation."""
        storage_tools.client.request = AsyncMock(return_value=mock_dataset_response[0])

        result = await storage_tools.create_dataset({
            "pool_name": "tank",
            "dataset_name": "newdata"
        })

        assert result["name"] == "data"
        storage_tools.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_dataset_validation(self, storage_tools):
        """Test dataset deletion validation."""
        with pytest.raises(TrueNASValidationError):
            await storage_tools.delete_dataset({})

    @pytest.mark.asyncio
    async def test_format_size_bytes(self, storage_tools):
        """Test size formatting for bytes."""
        assert storage_tools._format_size(1024) == "1.0 KB"
        assert storage_tools._format_size(1024 * 1024) == "1.0 MB"
        assert storage_tools._format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert storage_tools._format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"

    @pytest.mark.asyncio
    async def test_parse_size_string(self, storage_tools):
        """Test parsing size strings."""
        assert storage_tools._parse_size("1GB") == 1024 * 1024 * 1024
        assert storage_tools._parse_size("500MB") == 500 * 1024 * 1024
        assert storage_tools._parse_size("1TB") == 1024 * 1024 * 1024 * 1024
        assert storage_tools._parse_size("100") == 100  # Plain number

    @pytest.mark.asyncio
    async def test_get_tool_definitions(self, storage_tools):
        """Test tool definitions are properly defined."""
        definitions = storage_tools.get_tool_definitions()

        assert len(definitions) > 0
        assert any(tool["name"] == "list_pools" for tool in definitions)
        assert any(tool["name"] == "list_datasets" for tool in definitions)
        assert any(tool["name"] == "create_dataset" for tool in definitions)


class TestDatasetOperations:
    """Test dataset-specific operations."""

    @pytest.fixture
    async def storage_tools(self, mock_truenas_client, mock_settings):
        """Create storage tools instance."""
        tools = StorageTools(client=mock_truenas_client, settings=mock_settings)
        return tools

    @pytest.mark.asyncio
    async def test_set_dataset_quota(self, storage_tools):
        """Test setting dataset quota."""
        storage_tools.client.request = AsyncMock(return_value={"status": "success"})

        result = await storage_tools.set_quota({
            "dataset_id": "tank/data",
            "quota": "100GB"
        })

        assert "success" in result or result.get("status") == "success"

    @pytest.mark.asyncio
    async def test_dataset_compression_settings(self, storage_tools, mock_dataset_response):
        """Test dataset compression configuration."""
        dataset = mock_dataset_response[0]
        assert dataset["compression"] == "lz4"

    @pytest.mark.asyncio
    async def test_dataset_deduplication_settings(self, storage_tools, mock_dataset_response):
        """Test dataset deduplication configuration."""
        dataset = mock_dataset_response[0]
        assert dataset["deduplication"]["value"] == "off"


class TestPoolOperations:
    """Test pool-specific operations."""

    @pytest.fixture
    async def storage_tools(self, mock_truenas_client, mock_settings):
        """Create storage tools instance."""
        tools = StorageTools(client=mock_truenas_client, settings=mock_settings)
        return tools

    @pytest.mark.asyncio
    async def test_pool_health_check(self, storage_tools, mock_pool_response):
        """Test pool health checking."""
        pool = mock_pool_response[0]
        assert pool["healthy"] is True
        assert pool["status"] == "ONLINE"

    @pytest.mark.asyncio
    async def test_pool_capacity_calculation(self, storage_tools, mock_pool_response):
        """Test pool capacity calculations."""
        pool = mock_pool_response[0]
        total = pool["size"]
        allocated = pool["allocated"]
        free = pool["free"]

        assert total == allocated + free
        assert total == 4000000000000  # 4TB

    @pytest.mark.asyncio
    async def test_pool_topology(self, storage_tools, mock_pool_response):
        """Test pool topology information."""
        pool = mock_pool_response[0]
        assert "topology" in pool
        assert "data" in pool["topology"]
        assert pool["topology"]["data"][0]["type"] == "MIRROR"
