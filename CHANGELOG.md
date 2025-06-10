# Changelog

All notable changes to this project will be documented in this file.

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
