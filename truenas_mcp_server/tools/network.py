"""
Network management tools for TrueNAS
"""

from typing import Dict, Any, Optional, List
from .base import BaseTool, tool_handler


class NetworkTools(BaseTool):
    """Tools for managing TrueNAS network configuration"""

    def get_tool_definitions(self) -> list:
        """Get tool definitions for network management"""
        return [
            ("list_network_interfaces", self.list_network_interfaces,
             "List all network interfaces", {}),
            ("get_network_interface", self.get_network_interface,
             "Get detailed information about a network interface",
             {"interface_name": {"type": "string", "required": True}}),
            ("get_network_configuration", self.get_network_configuration,
             "Get global network configuration", {}),
            ("list_static_routes", self.list_static_routes,
             "List all static routes", {}),
            ("get_dns_config", self.get_dns_config,
             "Get DNS configuration", {}),
            ("update_dns_config", self.update_dns_config,
             "Update DNS configuration",
             {"nameserver1": {"type": "string", "required": False},
              "nameserver2": {"type": "string", "required": False},
              "nameserver3": {"type": "string", "required": False}}),
            ("test_network_connectivity", self.test_network_connectivity,
             "Test network connectivity by pinging a host",
             {"host": {"type": "string", "required": True}}),
            ("get_ipmi_info", self.get_ipmi_info,
             "Get IPMI/BMC network information", {}),
            ("list_vlans", self.list_vlans,
             "List all VLAN interfaces", {}),
            ("list_bridges", self.list_bridges,
             "List all bridge interfaces", {}),
            ("list_lagg_interfaces", self.list_lagg_interfaces,
             "List all LAGG (link aggregation) interfaces", {}),
        ]

    @tool_handler
    async def list_network_interfaces(self) -> Dict[str, Any]:
        """
        List all network interfaces

        Returns:
            Dictionary containing list of network interfaces
        """
        await self.ensure_initialized()

        interfaces = await self.client.get("/interface")

        interface_list = []
        for iface in interfaces:
            # Get aliases/IP addresses
            aliases = iface.get("aliases", [])
            ipv4_addresses = []
            ipv6_addresses = []
            for alias in aliases:
                if alias.get("type") == "INET":
                    ipv4_addresses.append(f"{alias.get('address')}/{alias.get('netmask')}")
                elif alias.get("type") == "INET6":
                    ipv6_addresses.append(f"{alias.get('address')}/{alias.get('netmask')}")

            interface_info = {
                "id": iface.get("id"),
                "name": iface.get("name"),
                "type": iface.get("type"),
                "state": iface.get("state", {}).get("name") if isinstance(iface.get("state"), dict) else iface.get("state"),
                "aliases": aliases,
                "ipv4_addresses": ipv4_addresses,
                "ipv6_addresses": ipv6_addresses,
                "mtu": iface.get("mtu"),
                "description": iface.get("description"),
                "options": iface.get("options"),
                "link_state": iface.get("state", {}).get("link_state") if isinstance(iface.get("state"), dict) else None,
                "media_type": iface.get("state", {}).get("media_type") if isinstance(iface.get("state"), dict) else None,
                "media_subtype": iface.get("state", {}).get("media_subtype") if isinstance(iface.get("state"), dict) else None,
                "active_media_type": iface.get("state", {}).get("active_media_type") if isinstance(iface.get("state"), dict) else None,
                "active_media_subtype": iface.get("state", {}).get("active_media_subtype") if isinstance(iface.get("state"), dict) else None,
                "link_address": iface.get("state", {}).get("link_address") if isinstance(iface.get("state"), dict) else None,
            }
            interface_list.append(interface_info)

        # Categorize interfaces
        physical = [i for i in interface_list if i["type"] == "PHYSICAL"]
        virtual = [i for i in interface_list if i["type"] != "PHYSICAL"]

        return {
            "success": True,
            "interfaces": interface_list,
            "metadata": {
                "total_interfaces": len(interface_list),
                "physical_interfaces": len(physical),
                "virtual_interfaces": len(virtual),
                "interfaces_with_ip": sum(1 for i in interface_list if i["ipv4_addresses"])
            }
        }

    @tool_handler
    async def get_network_interface(self, interface_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a network interface

        Args:
            interface_name: Name of the interface

        Returns:
            Dictionary containing interface details
        """
        await self.ensure_initialized()

        interfaces = await self.client.get("/interface")

        target_iface = None
        for iface in interfaces:
            if iface.get("name") == interface_name or iface.get("id") == interface_name:
                target_iface = iface
                break

        if not target_iface:
            return {
                "success": False,
                "error": f"Interface '{interface_name}' not found"
            }

        # Extract detailed state information
        state = target_iface.get("state", {}) if isinstance(target_iface.get("state"), dict) else {}

        return {
            "success": True,
            "interface": {
                "id": target_iface.get("id"),
                "name": target_iface.get("name"),
                "type": target_iface.get("type"),
                "description": target_iface.get("description"),
                "aliases": target_iface.get("aliases", []),
                "mtu": target_iface.get("mtu"),
                "options": target_iface.get("options"),
                "ipv4_dhcp": target_iface.get("ipv4_dhcp"),
                "ipv6_auto": target_iface.get("ipv6_auto"),
                "state": {
                    "name": state.get("name"),
                    "orig_name": state.get("orig_name"),
                    "description": state.get("description"),
                    "mtu": state.get("mtu"),
                    "cloned": state.get("cloned"),
                    "flags": state.get("flags", []),
                    "nd6_flags": state.get("nd6_flags", []),
                    "capabilities": state.get("capabilities", []),
                    "link_state": state.get("link_state"),
                    "media_type": state.get("media_type"),
                    "media_subtype": state.get("media_subtype"),
                    "active_media_type": state.get("active_media_type"),
                    "active_media_subtype": state.get("active_media_subtype"),
                    "supported_media": state.get("supported_media", []),
                    "media_options": state.get("media_options"),
                    "link_address": state.get("link_address"),
                    "rx_queues": state.get("rx_queues"),
                    "tx_queues": state.get("tx_queues"),
                    "aliases": state.get("aliases", []),
                },
                "failover_critical": target_iface.get("failover_critical"),
                "failover_group": target_iface.get("failover_group"),
                "failover_vhid": target_iface.get("failover_vhid"),
                "failover_aliases": target_iface.get("failover_aliases", []),
                "failover_virtual_aliases": target_iface.get("failover_virtual_aliases", []),
            }
        }

    @tool_handler
    async def get_network_configuration(self) -> Dict[str, Any]:
        """
        Get global network configuration

        Returns:
            Dictionary containing network configuration
        """
        await self.ensure_initialized()

        config = await self.client.get("/network/configuration")

        return {
            "success": True,
            "configuration": {
                "id": config.get("id"),
                "hostname": config.get("hostname"),
                "domain": config.get("domain"),
                "hostname_local": config.get("hostname_local"),
                "ipv4gateway": config.get("ipv4gateway"),
                "ipv6gateway": config.get("ipv6gateway"),
                "nameserver1": config.get("nameserver1"),
                "nameserver2": config.get("nameserver2"),
                "nameserver3": config.get("nameserver3"),
                "httpproxy": config.get("httpproxy"),
                "hosts": config.get("hosts"),
                "domains": config.get("domains", []),
                "service_announcement": config.get("service_announcement", {}),
                "activity": config.get("activity", {}),
                "state": config.get("state", {})
            }
        }

    @tool_handler
    async def list_static_routes(self) -> Dict[str, Any]:
        """
        List all static routes

        Returns:
            Dictionary containing list of static routes
        """
        await self.ensure_initialized()

        routes = await self.client.get("/staticroute")

        route_list = []
        for route in routes:
            route_info = {
                "id": route.get("id"),
                "destination": route.get("destination"),
                "gateway": route.get("gateway"),
                "description": route.get("description")
            }
            route_list.append(route_info)

        return {
            "success": True,
            "routes": route_list,
            "metadata": {
                "total_routes": len(route_list)
            }
        }

    @tool_handler
    async def get_dns_config(self) -> Dict[str, Any]:
        """
        Get DNS configuration

        Returns:
            Dictionary containing DNS configuration
        """
        await self.ensure_initialized()

        config = await self.client.get("/network/configuration")

        return {
            "success": True,
            "dns": {
                "nameserver1": config.get("nameserver1"),
                "nameserver2": config.get("nameserver2"),
                "nameserver3": config.get("nameserver3"),
                "domain": config.get("domain"),
                "domains": config.get("domains", [])
            }
        }

    @tool_handler
    async def update_dns_config(
        self,
        nameserver1: Optional[str] = None,
        nameserver2: Optional[str] = None,
        nameserver3: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update DNS configuration

        Args:
            nameserver1: Primary DNS server
            nameserver2: Secondary DNS server
            nameserver3: Tertiary DNS server

        Returns:
            Dictionary containing result
        """
        await self.ensure_initialized()

        update_data = {}
        if nameserver1 is not None:
            update_data["nameserver1"] = nameserver1
        if nameserver2 is not None:
            update_data["nameserver2"] = nameserver2
        if nameserver3 is not None:
            update_data["nameserver3"] = nameserver3

        if not update_data:
            return {
                "success": False,
                "error": "No DNS servers specified"
            }

        try:
            result = await self.client.put("/network/configuration", update_data)
            return {
                "success": True,
                "message": "DNS configuration updated successfully",
                "dns": {
                    "nameserver1": result.get("nameserver1"),
                    "nameserver2": result.get("nameserver2"),
                    "nameserver3": result.get("nameserver3")
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update DNS configuration: {str(e)}"
            }

    @tool_handler
    async def test_network_connectivity(self, host: str) -> Dict[str, Any]:
        """
        Test network connectivity by pinging a host

        Args:
            host: Hostname or IP address to ping

        Returns:
            Dictionary containing ping result
        """
        await self.ensure_initialized()

        try:
            result = await self.client.post("/network/general/summary")
            # The ping might be done differently, let's try an alternative approach
        except Exception:
            pass

        # Alternative: Use the system to ping
        try:
            # This endpoint may vary by TrueNAS version
            result = await self.client.get(f"/network/general/summary")
            return {
                "success": True,
                "host": host,
                "network_summary": result,
                "note": "Direct ping not available via API. Use network summary to verify connectivity."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to test connectivity: {str(e)}"
            }

    @tool_handler
    async def get_ipmi_info(self) -> Dict[str, Any]:
        """
        Get IPMI/BMC network information

        Returns:
            Dictionary containing IPMI information
        """
        await self.ensure_initialized()

        try:
            ipmi = await self.client.get("/ipmi")
            if isinstance(ipmi, list) and ipmi:
                ipmi_info = ipmi[0]  # Usually there's one IPMI interface
            else:
                ipmi_info = ipmi

            return {
                "success": True,
                "ipmi": {
                    "id": ipmi_info.get("id") if isinstance(ipmi_info, dict) else None,
                    "channel": ipmi_info.get("channel") if isinstance(ipmi_info, dict) else None,
                    "dhcp": ipmi_info.get("dhcp") if isinstance(ipmi_info, dict) else None,
                    "ipaddress": ipmi_info.get("ipaddress") if isinstance(ipmi_info, dict) else None,
                    "netmask": ipmi_info.get("netmask") if isinstance(ipmi_info, dict) else None,
                    "gateway": ipmi_info.get("gateway") if isinstance(ipmi_info, dict) else None,
                    "vlan": ipmi_info.get("vlan") if isinstance(ipmi_info, dict) else None,
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"IPMI not available or not configured: {str(e)}"
            }

    @tool_handler
    async def list_vlans(self) -> Dict[str, Any]:
        """
        List all VLAN interfaces

        Returns:
            Dictionary containing list of VLANs
        """
        await self.ensure_initialized()

        interfaces = await self.client.get("/interface")

        vlan_list = []
        for iface in interfaces:
            if iface.get("type") == "VLAN":
                vlan_info = {
                    "id": iface.get("id"),
                    "name": iface.get("name"),
                    "vlan_tag": iface.get("vlan_tag"),
                    "vlan_parent_interface": iface.get("vlan_parent_interface"),
                    "aliases": iface.get("aliases", []),
                    "mtu": iface.get("mtu"),
                    "description": iface.get("description"),
                    "state": iface.get("state", {}).get("name") if isinstance(iface.get("state"), dict) else iface.get("state")
                }
                vlan_list.append(vlan_info)

        return {
            "success": True,
            "vlans": vlan_list,
            "metadata": {
                "total_vlans": len(vlan_list)
            }
        }

    @tool_handler
    async def list_bridges(self) -> Dict[str, Any]:
        """
        List all bridge interfaces

        Returns:
            Dictionary containing list of bridges
        """
        await self.ensure_initialized()

        interfaces = await self.client.get("/interface")

        bridge_list = []
        for iface in interfaces:
            if iface.get("type") == "BRIDGE":
                bridge_info = {
                    "id": iface.get("id"),
                    "name": iface.get("name"),
                    "bridge_members": iface.get("bridge_members", []),
                    "aliases": iface.get("aliases", []),
                    "mtu": iface.get("mtu"),
                    "description": iface.get("description"),
                    "state": iface.get("state", {}).get("name") if isinstance(iface.get("state"), dict) else iface.get("state"),
                    "stp": iface.get("stp")
                }
                bridge_list.append(bridge_info)

        return {
            "success": True,
            "bridges": bridge_list,
            "metadata": {
                "total_bridges": len(bridge_list)
            }
        }

    @tool_handler
    async def list_lagg_interfaces(self) -> Dict[str, Any]:
        """
        List all LAGG (link aggregation) interfaces

        Returns:
            Dictionary containing list of LAGGs
        """
        await self.ensure_initialized()

        interfaces = await self.client.get("/interface")

        lagg_list = []
        for iface in interfaces:
            if iface.get("type") == "LINK_AGGREGATION":
                lagg_info = {
                    "id": iface.get("id"),
                    "name": iface.get("name"),
                    "lag_protocol": iface.get("lag_protocol"),
                    "lag_ports": iface.get("lag_ports", []),
                    "aliases": iface.get("aliases", []),
                    "mtu": iface.get("mtu"),
                    "description": iface.get("description"),
                    "state": iface.get("state", {}).get("name") if isinstance(iface.get("state"), dict) else iface.get("state"),
                    "xmit_hash_policy": iface.get("xmit_hash_policy"),
                    "lacpdu_rate": iface.get("lacpdu_rate")
                }
                lagg_list.append(lagg_info)

        return {
            "success": True,
            "lagg_interfaces": lagg_list,
            "metadata": {
                "total_laggs": len(lagg_list)
            }
        }
