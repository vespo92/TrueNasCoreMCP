# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2024-01-14

### Changed
- **BREAKING**: Complete refactor from monolithic to modular architecture
- **BREAKING**: Changed package structure - now use `from truenas_mcp_server import TrueNASMCPServer`
- Migrated from single 900-line file to organized package structure
- Added comprehensive Pydantic models for type safety
- Implemented proper error hierarchy with custom exceptions
- Added connection pooling and retry logic for HTTP client
- Introduced environment-based configuration with validation
- Added structured logging throughout the application
- Improved tool organization with base classes and inheritance

### Added
- Full type hints and Pydantic models for all data structures
- Comprehensive error handling with detailed error messages
- HTTP client with automatic retry and exponential backoff
- Rate limiting support (configurable)
- Environment-based configuration via `.env` files
- Structured logging with configurable levels
- Plugin architecture for easy tool extension
- Comprehensive documentation and examples
- Production-ready packaging for PyPI distribution

### Fixed
- Memory leaks from global client singleton
- Inconsistent error responses
- Missing validation on user inputs
- Connection timeout issues
- SSL verification problems

### Security
- API keys now properly masked in logs
- Added validation for all user inputs
- Destructive operations disabled by default
- SSL verification enabled by default

## [2.0.0] - 2025-01-11

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
