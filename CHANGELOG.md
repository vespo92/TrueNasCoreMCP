# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-06-11

### Added - Phase 2 Features
- **Permission Management**
  - `modify_dataset_permissions()` - Change Unix permissions (chmod/chown equivalent)
  - `update_dataset_acl()` - Manage Access Control Lists (ACLs)
  - `get_dataset_permissions()` - View current permissions and ACL information
  
- **Dataset Property Management**
  - `modify_dataset_properties()` - Update ZFS properties (compression, dedup, quota, etc.)
  - `get_dataset_properties()` - Retrieve all dataset properties
  
- **Kubernetes Storage Integration**
  - `create_nfs_export()` - Create NFS exports for Kubernetes persistent volumes
  - `create_iscsi_target()` - Create iSCSI targets for Kubernetes block storage
  - Automatic generation of K8s StorageClass and PersistentVolume YAML examples
  
- **Automation Features**
  - `create_snapshot_policy()` - Automated snapshot scheduling with retention policies
  - Helper functions for size parsing and K8s YAML generation

### Enhanced
- Added support for recursive permission changes
- Human-readable size inputs (e.g., "10G", "100M") for quotas and storage
- Better error handling with detailed response messages
- Type hints for Union types to support mixed parameter types

### Security
- Maintained API key security model
- Added validation for permission operations
- Secure handling of ACL modifications

## [1.0.0] - 2025-01-09

### Added
- Initial release of TrueNAS Core MCP Server
- User management functions (list users, get user details)
- System information retrieval
- Storage pool management (list pools, get pool status)
- Dataset management (list datasets, create datasets)
- SMB share management (list shares, create shares)
- Snapshot creation functionality
- Connection test script
- Comprehensive documentation
- Setup scripts for Windows and Unix-like systems

### Features
- Full compatibility with TrueNAS Core API v2.0
- Environment-based configuration
- SSL/TLS support with optional verification
- Error handling and status reporting
- Clean, minimal implementation using FastMCP

### Security
- API key authentication
- No hardcoded credentials
- Secure environment variable usage
