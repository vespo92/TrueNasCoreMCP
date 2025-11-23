# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.0.0] - 2025-01-23

### Major Feature Expansion

This release massively expands the TrueNAS MCP Server with 7 new tool modules, adding comprehensive coverage for system management, networking, replication, and TrueNAS Scale-specific features like Apps and VMs.

### Added

#### System Management Tools (11 tools)
- `get_system_info` - Get comprehensive system information including version, hardware, uptime
- `get_system_version` - Get TrueNAS version details with Scale/Core detection
- `list_services` - List all system services with status
- `get_service_status` - Get status of a specific service
- `start_service` - Start a system service
- `stop_service` - Stop a system service
- `restart_service` - Restart a system service
- `list_alerts` - List all system alerts with severity levels
- `dismiss_alert` - Dismiss system alerts
- `get_boot_info` - Get boot pool and environment information
- `get_update_status` - Check for available system updates

#### Group Management Tools (7 tools)
- `list_groups` - List all groups with categorization
- `get_group` - Get detailed group information with members
- `create_group` - Create new groups with sudo support
- `update_group` - Update group properties
- `delete_group` - Delete groups with safety checks
- `add_user_to_group` - Add users to groups
- `remove_user_from_group` - Remove users from groups

#### Disk Management Tools (8 tools)
- `list_disks` - List all disks with SSD/HDD detection
- `get_disk` - Get detailed disk information
- `get_disk_smart` - Get SMART data and attributes
- `run_smart_test` - Run SMART tests (SHORT, LONG, CONVEYANCE, OFFLINE)
- `get_smart_test_results` - Get SMART test results
- `list_unused_disks` - List disks not in pools
- `get_disk_temperatures` - Get temperature readings with status indicators
- `wipe_disk` - Securely wipe disks (destructive)

#### Network Tools (11 tools)
- `list_network_interfaces` - List all interfaces with IP addresses
- `get_network_interface` - Get detailed interface information
- `get_network_configuration` - Get global network configuration
- `list_static_routes` - List all static routes
- `get_dns_config` - Get DNS server configuration
- `update_dns_config` - Update DNS servers
- `test_network_connectivity` - Test network connectivity
- `get_ipmi_info` - Get IPMI/BMC network information
- `list_vlans` - List VLAN interfaces
- `list_bridges` - List bridge interfaces
- `list_lagg_interfaces` - List link aggregation interfaces

#### Replication Tools (10 tools)
- `list_replication_tasks` - List all replication tasks
- `get_replication_task` - Get detailed replication task info
- `run_replication_task` - Manually run a replication task
- `create_replication_task` - Create new replication tasks (LOCAL, SSH, NETCAT)
- `delete_replication_task` - Delete replication tasks
- `list_ssh_connections` - List SSH connections for remote replication
- `list_ssh_keypairs` - List SSH keypairs
- `get_replication_history` - Get replication task run history
- `list_cloud_sync_tasks` - List cloud sync tasks
- `list_rsync_tasks` - List rsync tasks

#### Application Tools - TrueNAS Scale (12 tools)
- `list_apps` - List all installed applications
- `get_app` - Get detailed application information
- `start_app` - Start an application
- `stop_app` - Stop an application
- `restart_app` - Restart an application
- `delete_app` - Delete an application
- `list_app_catalog` - List available applications from catalog
- `search_app_catalog` - Search for applications
- `get_app_logs` - Get application container logs
- `list_docker_images` - List all Docker images
- `pull_docker_image` - Pull a Docker image
- `get_kubernetes_status` - Get Kubernetes/container runtime status

#### Virtual Machine Tools - TrueNAS Scale (12 tools)
- `list_vms` - List all virtual machines
- `get_vm` - Get detailed VM information with devices
- `start_vm` - Start a virtual machine
- `stop_vm` - Stop a virtual machine (graceful or force)
- `restart_vm` - Restart a virtual machine
- `create_vm` - Create new virtual machines
- `delete_vm` - Delete virtual machines
- `clone_vm` - Clone a virtual machine
- `get_vm_status` - Get VM status
- `list_vm_devices` - List devices attached to a VM
- `get_vm_console` - Get VM console information
- `get_virtualization_status` - Get virtualization support status

### Changed

- **Version bump**: 4.0.0 → 5.0.0
- **Tool count**: 40+ → 110+ tools (175% increase)
- **Module count**: 5 tool modules → 12 tool modules
- **TrueNAS Scale support**: Full support for Scale-specific features

### Summary

| Category | Tools Added |
|----------|-------------|
| System Management | 11 |
| Group Management | 7 |
| Disk Management | 8 |
| Network Management | 11 |
| Replication & Backup | 10 |
| Apps (Scale) | 12 |
| VMs (Scale) | 12 |
| **Total New Tools** | **71** |

### Compatibility

- Works with TrueNAS Core and TrueNAS Scale
- Scale-specific features (Apps, VMs) gracefully handle Core systems
- All existing tools remain unchanged and backward compatible

---

## [4.0.0] - 2025-01-16

### Major Optimizations & Production Enhancements

This release represents a comprehensive optimization of the TrueNAS MCP Server, making it truly production-ready with enterprise-grade features.

### Added

#### Performance & Caching
- **Comprehensive Caching Layer**: In-memory cache with TTL and LRU eviction
  - `@cached` decorator for easy function caching
  - Namespace support for organized cache management
  - Cache statistics and hit rate monitoring
  - Automatic cleanup of expired entries
  - Configurable cache size and TTL
  - Cache invalidation decorators (`@cache_invalidate`)
  - Conditional caching support

#### Rate Limiting
- **Token Bucket Rate Limiter**: Protect TrueNAS API from abuse
  - Per-key rate limiting with configurable limits
  - Burst capacity support
  - `@rate_limit` decorator for easy protection
  - Adaptive rate limiting based on operation cost
  - Automatic token refill
  - Rate limit statistics and monitoring

#### Monitoring & Metrics
- **Prometheus-Compatible Metrics**: Full observability
  - Counters, Gauges, and Histograms
  - Automatic HTTP request tracking
  - Cache performance metrics
  - Rate limit metrics
  - Custom metrics support
  - Prometheus text format export
  - Decorators: `@track_time`, `@track_counter`, `@track_errors`
  - Performance percentiles (P50, P95, P99)

#### Security Enhancements
- **Audit Logging System**: Complete audit trail
  - Structured JSON audit logs
  - Event categorization (auth, data access, modifications)
  - Severity levels (INFO, WARNING, CRITICAL)
  - User and source IP tracking
  - Before/after change tracking
  - Audit event export and filtering
  - Automatic logging of destructive operations
- **Input Validation & Sanitization**:
  - Path traversal protection
  - Command injection prevention
  - SQL injection prevention
  - Email and username validation
  - IP address and port validation
  - Safe path handling with allowed prefixes

#### Resilience & Error Handling
- **Circuit Breaker Pattern**: Fault tolerance and graceful degradation
  - Three states: CLOSED, OPEN, HALF_OPEN
  - Automatic failure detection
  - Configurable failure thresholds
  - Automatic recovery attempts
  - `@circuit_breaker` decorator
  - Circuit state monitoring
- **Advanced Retry Logic**:
  - Exponential backoff with jitter
  - Configurable retry policies
  - `@retry` decorator
  - Exception-specific retry behavior

#### Testing & Quality
- **Comprehensive Test Suite**: 80%+ code coverage
  - Unit tests for all components
  - Integration tests for workflows
  - Pytest fixtures and mocks
  - Async test support
  - Coverage reporting
  - Test organization (unit/, integration/)

#### Documentation
- **MkDocs Documentation Site**:
  - Material theme with dark mode
  - Auto-generated API reference
  - Advanced guides (caching, metrics, security)
  - Code examples and tutorials
  - Architecture diagrams
  - Troubleshooting guides
  - Prometheus/Grafana integration guides

### Changed

- **Version bump**: 3.0.2 → 4.0.0
- **Architecture**: Added modular subsystems (cache/, metrics/, security/, resilience/)
- **Configuration**: Enhanced settings with new feature flags
- **Performance**: 20-100x improvement on cached operations
- **Error Handling**: More granular exception types
- **Logging**: Structured JSON logging for production

### Performance Improvements

- **API Response Time**:
  - Uncached: 100-500ms (API call)
  - Cached: 1-5ms (memory access)
  - Improvement: 20-100x faster
- **Throughput**: Rate limiting prevents API overload
- **Reliability**: Circuit breaker prevents cascading failures
- **Memory**: Efficient LRU cache with automatic eviction
- **Connections**: Improved connection pooling and reuse

### Configuration

New environment variables:
```env
# Caching
ENABLE_CACHE=true
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Metrics
ENABLE_METRICS=true
METRICS_PORT=9090

# Security
ENABLE_AUDIT_LOGGING=true
```

### Security

- Path traversal attack prevention
- Input sanitization on all user inputs
- Comprehensive audit logging
- API key masking in logs and metrics
- Security headers support
- Validation of all file paths and dataset names

### Observability

- Full Prometheus metrics export
- Request/response timing histograms
- Error rate tracking
- Cache hit rate monitoring
- Rate limit metrics
- Circuit breaker state tracking
- Health check endpoints

### Developer Experience

- Comprehensive test fixtures
- Easy-to-use decorators
- Type-safe configuration
- Better error messages
- Detailed logging
- Complete API documentation
- Code examples for all features

### Migration Guide

#### From 3.x to 4.x

No breaking changes! All new features are opt-in via configuration.

To enable new features:
```env
ENABLE_CACHE=true
ENABLE_METRICS=true
ENABLE_AUDIT_LOGGING=true
```

### Metrics

- **Code Coverage**: ~10% → 80%+
- **Test Count**: ~5 → 100+ tests
- **Documentation Pages**: 10 → 30+ pages
- **Module Count**: 12 → 25+ modules
- **Lines of Code**: 3,015 → 8,000+ lines

### Special Thanks

This release brings the TrueNAS MCP Server to production-grade quality suitable for enterprise deployments.

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
