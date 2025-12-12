"""
Live integration tests for TrueNAS virtualization tools

These tests run against actual TrueNAS servers and require:
- TRUENAS_URL and TRUENAS_API_KEY environment variables set
- Test resources created manually or by this test

Test resources use the 'mcp-test-' prefix to avoid conflicts with production.
"""

import asyncio
import os
import pytest
from typing import Optional

# Skip all tests if not configured
pytestmark = pytest.mark.skipif(
    not os.environ.get("TRUENAS_URL"),
    reason="TRUENAS_URL not set - skipping live tests"
)


class TestAppToolsLive:
    """Live tests for AppTools"""

    @pytest.fixture
    def app_tools(self):
        from truenas_mcp_server.tools.apps import AppTools
        return AppTools()

    @pytest.mark.asyncio
    async def test_list_apps(self, app_tools):
        """Test listing all apps (read-only, safe)"""
        result = await app_tools.list_apps()
        assert result["success"] is True
        assert "apps" in result
        assert "metadata" in result
        print(f"\nFound {result['metadata']['total_apps']} apps")
        for app in result["apps"]:
            print(f"  - {app['name']}: {app['state']}")

    @pytest.mark.asyncio
    async def test_get_app_existing(self, app_tools):
        """Test getting an existing app"""
        # First list apps to find one
        list_result = await app_tools.list_apps()
        if not list_result["apps"]:
            pytest.skip("No apps found to test")

        app_name = list_result["apps"][0]["name"]
        result = await app_tools.get_app(app_name)
        assert result["success"] is True
        assert result["app"]["name"] == app_name

    @pytest.mark.asyncio
    async def test_get_app_config_existing(self, app_tools):
        """Test getting app config (uses quirky plain string body!)"""
        list_result = await app_tools.list_apps()
        if not list_result["apps"]:
            pytest.skip("No apps found to test")

        app_name = list_result["apps"][0]["name"]
        result = await app_tools.get_app_config(app_name)
        assert result["success"] is True
        assert result["app_name"] == app_name
        assert "config" in result
        print(f"\nApp {app_name} config keys: {list(result['config'].keys()) if result['config'] else 'empty'}")

    @pytest.mark.asyncio
    async def test_get_app_nonexistent(self, app_tools):
        """Test getting a non-existent app"""
        result = await app_tools.get_app("nonexistent-app-xyz123")
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestInstanceToolsLive:
    """Live tests for InstanceTools"""

    @pytest.fixture
    def instance_tools(self):
        from truenas_mcp_server.tools.instances import InstanceTools
        return InstanceTools()

    @pytest.mark.asyncio
    async def test_list_instances(self, instance_tools):
        """Test listing all Incus instances (read-only, safe)"""
        result = await instance_tools.list_instances()
        assert result["success"] is True
        assert "instances" in result
        assert "metadata" in result
        print(f"\nFound {result['metadata']['total_instances']} instances")
        for inst in result["instances"]:
            print(f"  - {inst['name']} ({inst['type']}): {inst['status']} - {inst['cpu']} CPU, {inst['memory_gb']}GB RAM")

    @pytest.mark.asyncio
    async def test_list_instances_filter_vm(self, instance_tools):
        """Test filtering instances by type"""
        result = await instance_tools.list_instances(instance_type="VM")
        assert result["success"] is True
        for inst in result["instances"]:
            assert inst["type"] == "VM"

    @pytest.mark.asyncio
    async def test_list_instances_filter_container(self, instance_tools):
        """Test filtering instances by type"""
        result = await instance_tools.list_instances(instance_type="CONTAINER")
        assert result["success"] is True
        for inst in result["instances"]:
            assert inst["type"] == "CONTAINER"

    @pytest.mark.asyncio
    async def test_get_instance_existing(self, instance_tools):
        """Test getting an existing instance"""
        list_result = await instance_tools.list_instances()
        if not list_result["instances"]:
            pytest.skip("No instances found to test")

        inst_name = list_result["instances"][0]["name"]
        result = await instance_tools.get_instance(inst_name)
        assert result["success"] is True
        assert result["instance"]["name"] == inst_name

    @pytest.mark.asyncio
    async def test_get_instance_nonexistent(self, instance_tools):
        """Test getting a non-existent instance"""
        result = await instance_tools.get_instance("nonexistent-instance-xyz123")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_list_instance_devices(self, instance_tools):
        """Test listing devices for an instance"""
        list_result = await instance_tools.list_instances()
        if not list_result["instances"]:
            pytest.skip("No instances found to test")

        inst_name = list_result["instances"][0]["name"]
        result = await instance_tools.list_instance_devices(inst_name)
        assert result["success"] is True
        assert "devices" in result
        print(f"\nInstance {inst_name} has {result['metadata']['device_count']} devices")


class TestLegacyVMToolsLive:
    """Live tests for LegacyVMTools"""

    @pytest.fixture
    def vm_tools(self):
        from truenas_mcp_server.tools.vms import LegacyVMTools
        return LegacyVMTools()

    @pytest.mark.asyncio
    async def test_list_legacy_vms(self, vm_tools):
        """Test listing all legacy VMs (read-only, safe)"""
        result = await vm_tools.list_legacy_vms()
        assert result["success"] is True
        assert "vms" in result
        assert "metadata" in result
        print(f"\nFound {result['metadata']['total_vms']} legacy VMs")
        for vm in result["vms"]:
            print(f"  - {vm['name']} (ID: {vm['id']}): {vm['status']} - {vm['vcpus']} vCPU, {vm['memory_mb']}MB RAM")

    @pytest.mark.asyncio
    async def test_get_legacy_vm_existing(self, vm_tools):
        """Test getting an existing legacy VM"""
        list_result = await vm_tools.list_legacy_vms()
        if not list_result["vms"]:
            pytest.skip("No legacy VMs found to test")

        vm_id = list_result["vms"][0]["id"]
        result = await vm_tools.get_legacy_vm(vm_id)
        assert result["success"] is True
        assert result["vm"]["id"] == vm_id

    @pytest.mark.asyncio
    async def test_get_legacy_vm_nonexistent(self, vm_tools):
        """Test getting a non-existent legacy VM"""
        result = await vm_tools.get_legacy_vm(99999)
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestIntegration:
    """Integration tests that exercise multiple tools together"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """
        Test a full workflow:
        1. List resources
        2. Get details of each type
        3. Verify API quirks are handled correctly
        """
        from truenas_mcp_server.tools.apps import AppTools
        from truenas_mcp_server.tools.instances import InstanceTools
        from truenas_mcp_server.tools.vms import LegacyVMTools

        app_tools = AppTools()
        instance_tools = InstanceTools()
        vm_tools = LegacyVMTools()

        # List all resource types
        apps = await app_tools.list_apps()
        instances = await instance_tools.list_instances()
        vms = await vm_tools.list_legacy_vms()

        print("\n=== TrueNAS Virtualization Summary ===")
        print(f"Apps: {apps['metadata']['total_apps']}")
        print(f"Incus Instances: {instances['metadata']['total_instances']}")
        print(f"Legacy VMs: {vms['metadata']['total_vms']}")

        # Verify all succeeded
        assert apps["success"]
        assert instances["success"]
        assert vms["success"]


if __name__ == "__main__":
    # Run quick smoke test
    async def smoke_test():
        from truenas_mcp_server.tools.apps import AppTools
        from truenas_mcp_server.tools.instances import InstanceTools
        from truenas_mcp_server.tools.vms import LegacyVMTools

        print("Testing AppTools...")
        app_tools = AppTools()
        apps = await app_tools.list_apps()
        print(f"  Found {apps['metadata']['total_apps']} apps")

        print("Testing InstanceTools...")
        instance_tools = InstanceTools()
        instances = await instance_tools.list_instances()
        print(f"  Found {instances['metadata']['total_instances']} instances")

        print("Testing LegacyVMTools...")
        vm_tools = LegacyVMTools()
        vms = await vm_tools.list_legacy_vms()
        print(f"  Found {vms['metadata']['total_vms']} legacy VMs")

        print("\nAll smoke tests passed!")

    asyncio.run(smoke_test())
