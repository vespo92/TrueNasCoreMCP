"""Unit tests for new v5.0.0 tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from truenas_mcp_server.tools.system import SystemTools
from truenas_mcp_server.tools.groups import GroupTools
from truenas_mcp_server.tools.disks import DiskTools
from truenas_mcp_server.tools.network import NetworkTools
from truenas_mcp_server.tools.replication import ReplicationTools
from truenas_mcp_server.tools.apps import AppTools
from truenas_mcp_server.tools.vms import VMTools


# ============================================================================
# System Tools Tests
# ============================================================================


class TestSystemTools:
    """Test system management tools."""

    @pytest.fixture
    async def system_tools(self, mock_truenas_client, mock_settings):
        """Create system tools instance for testing."""
        tools = SystemTools(client=mock_truenas_client, settings=mock_settings)
        tools._initialized = True
        return tools

    @pytest.mark.asyncio
    async def test_get_tool_definitions(self, system_tools):
        """Test tool definitions are properly defined."""
        definitions = system_tools.get_tool_definitions()
        assert len(definitions) > 0
        tool_names = [d[0] for d in definitions]
        assert "get_system_info" in tool_names
        assert "list_services" in tool_names
        assert "list_alerts" in tool_names

    @pytest.mark.asyncio
    async def test_list_services(self, system_tools):
        """Test listing system services."""
        mock_services = [
            {"id": 1, "service": "smb", "state": "RUNNING", "enable": True},
            {"id": 2, "service": "ssh", "state": "RUNNING", "enable": True},
            {"id": 3, "service": "nfs", "state": "STOPPED", "enable": False},
        ]
        system_tools.client.get = AsyncMock(return_value=mock_services)

        result = await system_tools.list_services()

        assert result["success"] is True
        assert len(result["services"]) == 3
        assert result["metadata"]["running_services"] == 2
        assert result["metadata"]["enabled_services"] == 2

    @pytest.mark.asyncio
    async def test_get_system_version(self, system_tools):
        """Test getting system version."""
        system_tools.client.get = AsyncMock(side_effect=[
            "TrueNAS-SCALE-24.04.0",
            "24.04.0",
            {"buildtime": "2024-01-01T00:00:00"}
        ])

        result = await system_tools.get_system_version()

        assert result["success"] is True
        assert "version" in result
        assert result["version"]["is_scale"] is True


# ============================================================================
# Group Tools Tests
# ============================================================================


class TestGroupTools:
    """Test group management tools."""

    @pytest.fixture
    async def group_tools(self, mock_truenas_client, mock_settings):
        """Create group tools instance for testing."""
        tools = GroupTools(client=mock_truenas_client, settings=mock_settings)
        tools._initialized = True
        return tools

    @pytest.mark.asyncio
    async def test_get_tool_definitions(self, group_tools):
        """Test tool definitions are properly defined."""
        definitions = group_tools.get_tool_definitions()
        assert len(definitions) > 0
        tool_names = [d[0] for d in definitions]
        assert "list_groups" in tool_names
        assert "create_group" in tool_names
        assert "add_user_to_group" in tool_names

    @pytest.mark.asyncio
    async def test_list_groups(self, group_tools):
        """Test listing groups."""
        mock_groups = [
            {"id": 1, "gid": 1000, "group": "users", "builtin": False, "users": [1, 2]},
            {"id": 2, "gid": 0, "group": "wheel", "builtin": True, "users": []},
        ]
        group_tools.client.get = AsyncMock(return_value=mock_groups)

        result = await group_tools.list_groups()

        assert result["success"] is True
        assert len(result["groups"]) == 2
        assert result["metadata"]["system_groups"] == 1
        assert result["metadata"]["regular_groups"] == 1


# ============================================================================
# Disk Tools Tests
# ============================================================================


class TestDiskTools:
    """Test disk management tools."""

    @pytest.fixture
    async def disk_tools(self, mock_truenas_client, mock_settings):
        """Create disk tools instance for testing."""
        tools = DiskTools(client=mock_truenas_client, settings=mock_settings)
        tools._initialized = True
        return tools

    @pytest.mark.asyncio
    async def test_get_tool_definitions(self, disk_tools):
        """Test tool definitions are properly defined."""
        definitions = disk_tools.get_tool_definitions()
        assert len(definitions) > 0
        tool_names = [d[0] for d in definitions]
        assert "list_disks" in tool_names
        assert "get_disk_smart" in tool_names
        assert "get_disk_temperatures" in tool_names

    @pytest.mark.asyncio
    async def test_list_disks(self, disk_tools):
        """Test listing disks."""
        mock_disks = [
            {"name": "sda", "serial": "ABC123", "model": "Samsung SSD",
             "size": 1000000000000, "type": "SSD", "rotationrate": 0},
            {"name": "sdb", "serial": "DEF456", "model": "WDC HDD",
             "size": 4000000000000, "type": "HDD", "rotationrate": 7200},
        ]
        disk_tools.client.get = AsyncMock(return_value=mock_disks)

        result = await disk_tools.list_disks()

        assert result["success"] is True
        assert len(result["disks"]) == 2
        assert result["metadata"]["ssd_count"] == 1
        assert result["metadata"]["hdd_count"] == 1

    @pytest.mark.asyncio
    async def test_temperature_status(self, disk_tools):
        """Test temperature status calculation."""
        assert disk_tools._get_temp_status(30) == "COOL"
        assert disk_tools._get_temp_status(40) == "NORMAL"
        assert disk_tools._get_temp_status(50) == "WARM"
        assert disk_tools._get_temp_status(60) == "HOT"
        assert disk_tools._get_temp_status(70) == "CRITICAL"
        assert disk_tools._get_temp_status(None) == "UNKNOWN"


# ============================================================================
# Network Tools Tests
# ============================================================================


class TestNetworkTools:
    """Test network management tools."""

    @pytest.fixture
    async def network_tools(self, mock_truenas_client, mock_settings):
        """Create network tools instance for testing."""
        tools = NetworkTools(client=mock_truenas_client, settings=mock_settings)
        tools._initialized = True
        return tools

    @pytest.mark.asyncio
    async def test_get_tool_definitions(self, network_tools):
        """Test tool definitions are properly defined."""
        definitions = network_tools.get_tool_definitions()
        assert len(definitions) > 0
        tool_names = [d[0] for d in definitions]
        assert "list_network_interfaces" in tool_names
        assert "get_dns_config" in tool_names
        assert "list_vlans" in tool_names

    @pytest.mark.asyncio
    async def test_list_network_interfaces(self, network_tools):
        """Test listing network interfaces."""
        mock_interfaces = [
            {"id": "em0", "name": "em0", "type": "PHYSICAL",
             "aliases": [{"type": "INET", "address": "192.168.1.100", "netmask": 24}],
             "state": {"name": "em0", "link_state": "LINK_STATE_UP"}},
            {"id": "br0", "name": "br0", "type": "BRIDGE", "aliases": [],
             "state": {"name": "br0"}},
        ]
        network_tools.client.get = AsyncMock(return_value=mock_interfaces)

        result = await network_tools.list_network_interfaces()

        assert result["success"] is True
        assert len(result["interfaces"]) == 2
        assert result["metadata"]["physical_interfaces"] == 1
        assert result["metadata"]["virtual_interfaces"] == 1


# ============================================================================
# Replication Tools Tests
# ============================================================================


class TestReplicationTools:
    """Test replication management tools."""

    @pytest.fixture
    async def replication_tools(self, mock_truenas_client, mock_settings):
        """Create replication tools instance for testing."""
        tools = ReplicationTools(client=mock_truenas_client, settings=mock_settings)
        tools._initialized = True
        return tools

    @pytest.mark.asyncio
    async def test_get_tool_definitions(self, replication_tools):
        """Test tool definitions are properly defined."""
        definitions = replication_tools.get_tool_definitions()
        assert len(definitions) > 0
        tool_names = [d[0] for d in definitions]
        assert "list_replication_tasks" in tool_names
        assert "create_replication_task" in tool_names
        assert "list_cloud_sync_tasks" in tool_names

    @pytest.mark.asyncio
    async def test_list_replication_tasks(self, replication_tools):
        """Test listing replication tasks."""
        mock_tasks = [
            {"id": 1, "name": "daily-backup", "direction": "PUSH",
             "transport": "SSH", "source_datasets": ["tank/data"],
             "target_dataset": "backup/data", "enabled": True},
            {"id": 2, "name": "local-sync", "direction": "PUSH",
             "transport": "LOCAL", "source_datasets": ["tank/data"],
             "target_dataset": "tank/backup", "enabled": True},
        ]
        replication_tools.client.get = AsyncMock(return_value=mock_tasks)

        result = await replication_tools.list_replication_tasks()

        assert result["success"] is True
        assert len(result["replication_tasks"]) == 2
        assert result["metadata"]["local_tasks"] == 1

    @pytest.mark.asyncio
    async def test_create_replication_task_validation(self, replication_tools):
        """Test replication task creation validation."""
        result = await replication_tools.create_replication_task(
            name="test",
            source_datasets=["tank/data"],
            target_dataset="backup/data",
            direction="INVALID",
            transport="LOCAL"
        )
        assert result["success"] is False
        assert "Direction must be" in result["error"]


# ============================================================================
# App Tools Tests
# ============================================================================


class TestAppTools:
    """Test application management tools."""

    @pytest.fixture
    async def app_tools(self, mock_truenas_client, mock_settings):
        """Create app tools instance for testing."""
        tools = AppTools(client=mock_truenas_client, settings=mock_settings)
        tools._initialized = True
        return tools

    @pytest.mark.asyncio
    async def test_get_tool_definitions(self, app_tools):
        """Test tool definitions are properly defined."""
        definitions = app_tools.get_tool_definitions()
        assert len(definitions) > 0
        tool_names = [d[0] for d in definitions]
        assert "list_apps" in tool_names
        assert "start_app" in tool_names
        assert "list_docker_images" in tool_names

    @pytest.mark.asyncio
    async def test_list_apps(self, app_tools):
        """Test listing apps."""
        mock_apps = [
            {"id": "plex", "name": "plex", "state": "RUNNING",
             "version": "1.0.0", "update_available": False},
            {"id": "nextcloud", "name": "nextcloud", "state": "STOPPED",
             "version": "2.0.0", "update_available": True},
        ]
        app_tools.client.get = AsyncMock(return_value=mock_apps)

        result = await app_tools.list_apps()

        assert result["success"] is True
        assert len(result["apps"]) == 2
        assert result["metadata"]["running_apps"] == 1
        assert result["metadata"]["apps_with_updates"] == 1


# ============================================================================
# VM Tools Tests
# ============================================================================


class TestVMTools:
    """Test virtual machine management tools."""

    @pytest.fixture
    async def vm_tools(self, mock_truenas_client, mock_settings):
        """Create VM tools instance for testing."""
        tools = VMTools(client=mock_truenas_client, settings=mock_settings)
        tools._initialized = True
        return tools

    @pytest.mark.asyncio
    async def test_get_tool_definitions(self, vm_tools):
        """Test tool definitions are properly defined."""
        definitions = vm_tools.get_tool_definitions()
        assert len(definitions) > 0
        tool_names = [d[0] for d in definitions]
        assert "list_vms" in tool_names
        assert "start_vm" in tool_names
        assert "create_vm" in tool_names

    @pytest.mark.asyncio
    async def test_list_vms(self, vm_tools):
        """Test listing VMs."""
        mock_vms = [
            {"id": 1, "name": "ubuntu-server", "vcpus": 4, "memory": 8192,
             "status": {"state": "RUNNING"}, "autostart": True},
            {"id": 2, "name": "windows-10", "vcpus": 8, "memory": 16384,
             "status": {"state": "STOPPED"}, "autostart": False},
        ]
        vm_tools.client.get = AsyncMock(return_value=mock_vms)

        result = await vm_tools.list_vms()

        assert result["success"] is True
        assert len(result["vms"]) == 2
        assert result["metadata"]["running_vms"] == 1
        assert result["metadata"]["total_vcpus"] == 4  # Only running VM

    @pytest.mark.asyncio
    async def test_create_vm(self, vm_tools):
        """Test creating a VM."""
        mock_created = {"id": 3, "name": "new-vm", "vcpus": 2, "memory": 4096}
        vm_tools.client.post = AsyncMock(return_value=mock_created)

        result = await vm_tools.create_vm(
            name="new-vm",
            vcpus=2,
            memory=4096
        )

        assert result["success"] is True
        assert result["vm"]["name"] == "new-vm"
        assert "next_steps" in result


# ============================================================================
# Base Tool Method Tests
# ============================================================================


class TestBaseToolMethods:
    """Test base tool utility methods."""

    @pytest.fixture
    async def disk_tools(self, mock_truenas_client, mock_settings):
        """Use disk tools to test base class methods."""
        tools = DiskTools(client=mock_truenas_client, settings=mock_settings)
        tools._initialized = True
        return tools

    @pytest.mark.asyncio
    async def test_format_size(self, disk_tools):
        """Test size formatting."""
        assert "KB" in disk_tools.format_size(1024)
        assert "MB" in disk_tools.format_size(1024 * 1024)
        assert "GB" in disk_tools.format_size(1024 * 1024 * 1024)
        assert "TB" in disk_tools.format_size(1024 * 1024 * 1024 * 1024)

    @pytest.mark.asyncio
    async def test_parse_size(self, disk_tools):
        """Test size parsing."""
        assert disk_tools.parse_size("1K") == 1024
        assert disk_tools.parse_size("1MB") == 1024 * 1024
        assert disk_tools.parse_size("1G") == 1024 * 1024 * 1024
        assert disk_tools.parse_size("100") == 100
