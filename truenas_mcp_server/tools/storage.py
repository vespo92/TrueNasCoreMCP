"""
Storage management tools for TrueNAS
"""

from typing import Dict, Any, Optional, List
from .base import BaseTool, tool_handler


class StorageTools(BaseTool):
    """Tools for managing TrueNAS storage (pools, datasets, volumes)"""
    
    def get_tool_definitions(self) -> list:
        """Get tool definitions for storage management"""
        return [
            ("list_pools", self.list_pools, "List all storage pools", {}),
            ("get_pool_status", self.get_pool_status, "Get detailed status of a specific pool",
             {"pool_name": {"type": "string", "required": True}}),
            ("list_datasets", self.list_datasets, "List all datasets", {}),
            ("get_dataset", self.get_dataset, "Get detailed information about a dataset",
             {"dataset": {"type": "string", "required": True}}),
            ("create_dataset", self.create_dataset, "Create a new dataset",
             {"pool": {"type": "string", "required": True},
              "name": {"type": "string", "required": True},
              "compression": {"type": "string", "required": False},
              "quota": {"type": "string", "required": False},
              "recordsize": {"type": "string", "required": False}}),
            ("delete_dataset", self.delete_dataset, "Delete a dataset",
             {"dataset": {"type": "string", "required": True},
              "recursive": {"type": "boolean", "required": False}}),
            ("update_dataset", self.update_dataset, "Update dataset properties",
             {"dataset": {"type": "string", "required": True},
              "properties": {"type": "object", "required": True}}),
        ]
    
    @tool_handler
    async def list_pools(self) -> Dict[str, Any]:
        """
        List all storage pools
        
        Returns:
            Dictionary containing list of pools with their status
        """
        await self.ensure_initialized()
        
        pools = await self.client.get("/pool")
        
        pool_list = []
        for pool in pools:
            # Calculate usage percentage
            size = pool.get("size", 0)
            allocated = pool.get("allocated", 0)
            free = pool.get("free", 0)
            usage_percent = (allocated / size * 100) if size > 0 else 0
            
            pool_info = {
                "name": pool.get("name"),
                "status": pool.get("status"),
                "healthy": pool.get("healthy"),
                "encrypted": pool.get("encrypt", 0) > 0,
                "size": self.format_size(size),
                "allocated": self.format_size(allocated),
                "free": self.format_size(free),
                "usage_percent": round(usage_percent, 2),
                "fragmentation": pool.get("fragmentation"),
                "scan": pool.get("scan", {}).get("state") if pool.get("scan") else None,
                "topology": {
                    "data_vdevs": len(pool.get("topology", {}).get("data", [])),
                    "cache_vdevs": len(pool.get("topology", {}).get("cache", [])),
                    "log_vdevs": len(pool.get("topology", {}).get("log", [])),
                    "spare_vdevs": len(pool.get("topology", {}).get("spare", []))
                }
            }
            pool_list.append(pool_info)
        
        # Calculate totals
        total_size = sum(p.get("size", 0) for p in pools)
        total_allocated = sum(p.get("allocated", 0) for p in pools)
        total_free = sum(p.get("free", 0) for p in pools)
        
        return {
            "success": True,
            "pools": pool_list,
            "metadata": {
                "pool_count": len(pool_list),
                "healthy_pools": sum(1 for p in pool_list if p["healthy"]),
                "degraded_pools": sum(1 for p in pool_list if not p["healthy"]),
                "total_capacity": self.format_size(total_size),
                "total_allocated": self.format_size(total_allocated),
                "total_free": self.format_size(total_free),
                "overall_usage_percent": round((total_allocated / total_size * 100) if total_size > 0 else 0, 2)
            }
        }
    
    @tool_handler
    async def get_pool_status(self, pool_name: str) -> Dict[str, Any]:
        """
        Get detailed status of a specific pool
        
        Args:
            pool_name: Name of the pool
            
        Returns:
            Dictionary containing detailed pool status
        """
        await self.ensure_initialized()
        
        try:
            pool = await self.client.get(f"/pool/id/{pool_name}")
        except Exception:
            # Try getting all pools and finding by name
            pools = await self.client.get("/pool")
            pool = None
            for p in pools:
                if p.get("name") == pool_name:
                    pool = p
                    break
            
            if not pool:
                return {
                    "success": False,
                    "error": f"Pool '{pool_name}' not found"
                }
        
        # Extract detailed information
        size = pool.get("size", 0)
        allocated = pool.get("allocated", 0)
        free = pool.get("free", 0)
        
        # Process topology
        topology = pool.get("topology", {})
        vdev_details = []
        
        for vdev_type in ["data", "cache", "log", "spare"]:
            vdevs = topology.get(vdev_type, [])
            for vdev in vdevs:
                vdev_info = {
                    "type": vdev_type,
                    "name": vdev.get("name"),
                    "status": vdev.get("status"),
                    "devices": []
                }
                for device in vdev.get("children", []):
                    vdev_info["devices"].append({
                        "name": device.get("name"),
                        "status": device.get("status"),
                        "read_errors": device.get("read", 0),
                        "write_errors": device.get("write", 0),
                        "checksum_errors": device.get("checksum", 0)
                    })
                vdev_details.append(vdev_info)
        
        return {
            "success": True,
            "pool": {
                "name": pool.get("name"),
                "id": pool.get("id"),
                "guid": pool.get("guid"),
                "status": pool.get("status"),
                "healthy": pool.get("healthy"),
                "encrypted": pool.get("encrypt", 0) > 0,
                "autotrim": pool.get("autotrim", {}).get("value") if pool.get("autotrim") else None,
                "capacity": {
                    "size": self.format_size(size),
                    "size_bytes": size,
                    "allocated": self.format_size(allocated),
                    "allocated_bytes": allocated,
                    "free": self.format_size(free),
                    "free_bytes": free,
                    "usage_percent": round((allocated / size * 100) if size > 0 else 0, 2),
                    "fragmentation": pool.get("fragmentation")
                },
                "topology": {
                    "vdevs": vdev_details,
                    "summary": {
                        "data_vdevs": len(topology.get("data", [])),
                        "cache_vdevs": len(topology.get("cache", [])),
                        "log_vdevs": len(topology.get("log", [])),
                        "spare_vdevs": len(topology.get("spare", []))
                    }
                },
                "scan": pool.get("scan"),
                "properties": pool.get("properties", {})
            }
        }
    
    @tool_handler
    async def list_datasets(self) -> Dict[str, Any]:
        """
        List all datasets
        
        Returns:
            Dictionary containing list of datasets
        """
        await self.ensure_initialized()
        
        datasets = await self.client.get("/pool/dataset")
        
        dataset_list = []
        for ds in datasets:
            # Calculate usage
            used = ds.get("used", {}).get("parsed") if isinstance(ds.get("used"), dict) else ds.get("used", 0)
            available = ds.get("available", {}).get("parsed") if isinstance(ds.get("available"), dict) else ds.get("available", 0)
            
            dataset_info = {
                "name": ds.get("name"),
                "pool": ds.get("pool"),
                "type": ds.get("type"),
                "mountpoint": ds.get("mountpoint"),
                "compression": ds.get("compression", {}).get("value") if isinstance(ds.get("compression"), dict) else ds.get("compression"),
                "deduplication": ds.get("deduplication", {}).get("value") if isinstance(ds.get("deduplication"), dict) else ds.get("deduplication"),
                "encrypted": ds.get("encrypted"),
                "used": self.format_size(used) if isinstance(used, (int, float)) else str(used),
                "available": self.format_size(available) if isinstance(available, (int, float)) else str(available),
                "quota": ds.get("quota", {}).get("value") if isinstance(ds.get("quota"), dict) else ds.get("quota"),
                "children": ds.get("children", [])
            }
            dataset_list.append(dataset_info)
        
        # Organize by pool
        pools_datasets = {}
        for ds in dataset_list:
            pool = ds["pool"]
            if pool not in pools_datasets:
                pools_datasets[pool] = []
            pools_datasets[pool].append(ds)
        
        return {
            "success": True,
            "datasets": dataset_list,
            "metadata": {
                "total_datasets": len(dataset_list),
                "by_pool": {pool: len(datasets) for pool, datasets in pools_datasets.items()},
                "encrypted_datasets": sum(1 for ds in dataset_list if ds.get("encrypted")),
                "compressed_datasets": sum(1 for ds in dataset_list if ds.get("compression") and ds.get("compression") != "off")
            }
        }
    
    @tool_handler
    async def get_dataset(self, dataset: str) -> Dict[str, Any]:
        """
        Get detailed information about a dataset
        
        Args:
            dataset: Dataset path (e.g., "tank/data")
            
        Returns:
            Dictionary containing dataset details
        """
        await self.ensure_initialized()
        
        datasets = await self.client.get("/pool/dataset")
        
        target_dataset = None
        for ds in datasets:
            if ds.get("name") == dataset:
                target_dataset = ds
                break
        
        if not target_dataset:
            return {
                "success": False,
                "error": f"Dataset '{dataset}' not found"
            }
        
        # Extract all properties
        properties = {}
        for key in ["compression", "deduplication", "atime", "sync", "quota", "refquota",
                   "reservation", "refreservation", "recordsize", "snapdir", "copies",
                   "readonly", "exec", "casesensitivity"]:
            value = target_dataset.get(key)
            if isinstance(value, dict):
                properties[key] = value.get("value")
            else:
                properties[key] = value
        
        return {
            "success": True,
            "dataset": {
                "name": target_dataset.get("name"),
                "id": target_dataset.get("id"),
                "pool": target_dataset.get("pool"),
                "type": target_dataset.get("type"),
                "mountpoint": target_dataset.get("mountpoint"),
                "encrypted": target_dataset.get("encrypted"),
                "encryption_root": target_dataset.get("encryption_root"),
                "key_loaded": target_dataset.get("key_loaded"),
                "locked": target_dataset.get("locked"),
                "usage": {
                    "used": target_dataset.get("used", {}).get("value") if isinstance(target_dataset.get("used"), dict) else target_dataset.get("used"),
                    "available": target_dataset.get("available", {}).get("value") if isinstance(target_dataset.get("available"), dict) else target_dataset.get("available"),
                    "referenced": target_dataset.get("referenced", {}).get("value") if isinstance(target_dataset.get("referenced"), dict) else target_dataset.get("referenced"),
                    "usedbysnapshots": target_dataset.get("usedbysnapshots", {}).get("value") if isinstance(target_dataset.get("usedbysnapshots"), dict) else target_dataset.get("usedbysnapshots"),
                    "usedbychildren": target_dataset.get("usedbychildren", {}).get("value") if isinstance(target_dataset.get("usedbychildren"), dict) else target_dataset.get("usedbychildren")
                },
                "properties": properties,
                "children": target_dataset.get("children", []),
                "snapshot_count": target_dataset.get("snapshot_count", 0),
                "origin": target_dataset.get("origin", {}).get("value") if isinstance(target_dataset.get("origin"), dict) else target_dataset.get("origin")
            }
        }
    
    @tool_handler
    async def create_dataset(
        self,
        pool: str,
        name: str,
        compression: str = "lz4",
        quota: Optional[str] = None,
        recordsize: str = "128K",
        sync: str = "standard",
        atime: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new dataset
        
        Args:
            pool: Pool name where dataset will be created
            name: Dataset name
            compression: Compression algorithm (lz4, gzip, zstd, off)
            quota: Optional quota (e.g., "10G")
            recordsize: Record size (e.g., "128K")
            sync: Sync mode (standard, always, disabled)
            atime: Enable access time updates
            
        Returns:
            Dictionary containing created dataset information
        """
        await self.ensure_initialized()
        
        # Prepare dataset data
        dataset_data = {
            "name": f"{pool}/{name}",
            "type": "FILESYSTEM",
            "compression": compression,
            "sync": sync,
            "atime": atime,
            "recordsize": recordsize
        }
        
        # Add quota if specified
        if quota:
            dataset_data["quota"] = self.parse_size(quota)
        
        # Create the dataset
        created = await self.client.post("/pool/dataset", dataset_data)
        
        return {
            "success": True,
            "message": f"Dataset '{pool}/{name}' created successfully",
            "dataset": {
                "name": created.get("name"),
                "id": created.get("id"),
                "mountpoint": created.get("mountpoint"),
                "compression": compression,
                "quota": quota,
                "recordsize": recordsize
            }
        }
    
    @tool_handler
    async def delete_dataset(self, dataset: str, recursive: bool = False, force: bool = False) -> Dict[str, Any]:
        """
        Delete a dataset
        
        Args:
            dataset: Dataset path (e.g., "tank/data")
            recursive: Delete child datasets
            force: Force deletion even if dataset has shares
            
        Returns:
            Dictionary confirming deletion
        """
        await self.ensure_initialized()
        
        # Check if destructive operations are allowed
        if not self.settings.enable_destructive_operations:
            return {
                "success": False,
                "error": "Destructive operations are disabled. Enable TRUENAS_ENABLE_DESTRUCTIVE_OPS to allow dataset deletion."
            }
        
        # Find the dataset
        datasets = await self.client.get("/pool/dataset")
        target_dataset = None
        for ds in datasets:
            if ds.get("name") == dataset:
                target_dataset = ds
                break
        
        if not target_dataset:
            return {
                "success": False,
                "error": f"Dataset '{dataset}' not found"
            }
        
        # Prepare deletion options
        delete_options = {
            "recursive": recursive,
            "force": force
        }
        
        # Delete the dataset
        dataset_id = target_dataset["id"]
        await self.client.delete(f"/pool/dataset/id/{dataset_id}")
        
        return {
            "success": True,
            "message": f"Dataset '{dataset}' deleted successfully",
            "deleted": {
                "name": dataset,
                "recursive": recursive,
                "children_deleted": len(target_dataset.get("children", [])) if recursive else 0
            }
        }
    
    @tool_handler
    async def update_dataset(self, dataset: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update dataset properties
        
        Args:
            dataset: Dataset path (e.g., "tank/data")
            properties: Dictionary of properties to update
            
        Returns:
            Dictionary containing updated dataset information
        """
        await self.ensure_initialized()
        
        # Find the dataset
        datasets = await self.client.get("/pool/dataset")
        target_dataset = None
        for ds in datasets:
            if ds.get("name") == dataset:
                target_dataset = ds
                break
        
        if not target_dataset:
            return {
                "success": False,
                "error": f"Dataset '{dataset}' not found"
            }
        
        # Process properties
        processed_props = {}
        for key, value in properties.items():
            if key in ["quota", "refquota", "reservation", "refreservation"] and isinstance(value, str):
                processed_props[key] = self.parse_size(value)
            else:
                processed_props[key] = value
        
        # Update the dataset
        dataset_id = target_dataset["id"]
        updated = await self.client.put(f"/pool/dataset/id/{dataset_id}", processed_props)
        
        return {
            "success": True,
            "message": f"Dataset '{dataset}' updated successfully",
            "updated_properties": list(properties.keys()),
            "dataset": {
                "name": updated.get("name"),
                "id": updated.get("id")
            }
        }