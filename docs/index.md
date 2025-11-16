# TrueNAS Core MCP Server

Production-ready Model Context Protocol (MCP) server for TrueNAS Core - Control your NAS through natural language with Claude and other AI assistants.

## Overview

The TrueNAS Core MCP Server enables AI assistants like Claude to interact with your TrueNAS system through natural language, providing:

- **Storage Management**: Create, manage, and monitor ZFS pools and datasets
- **User Management**: Comprehensive user and group administration
- **Sharing**: Configure SMB, NFS, and iSCSI shares
- **Snapshots**: Automated snapshot management and scheduling
- **Production-Ready**: Built-in caching, rate limiting, metrics, and security

## Key Features

### 🚀 Performance
- **Smart Caching**: Configurable TTL-based caching with LRU eviction
- **Rate Limiting**: Token bucket algorithm protects your TrueNAS API
- **Connection Pooling**: Efficient HTTP connection management
- **Async Architecture**: Fully asynchronous for maximum throughput

### 🔒 Security
- **Audit Logging**: Complete audit trail of all operations
- **Input Validation**: Path traversal and injection protection
- **Authentication**: Secure API key management
- **Rate Limiting**: Prevent API abuse

### 📊 Observability
- **Prometheus Metrics**: Full observability with counters, gauges, and histograms
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Health Checks**: Built-in health and readiness endpoints
- **Performance Tracking**: Detailed timing metrics for all operations

### 🛡️ Reliability
- **Circuit Breaker**: Automatic failure detection and recovery
- **Retry Logic**: Exponential backoff with jitter
- **Error Handling**: Comprehensive exception hierarchy
- **Type Safety**: Full type hints and Pydantic validation

## Quick Start

### Installation

```bash
# Using pip
pip install truenas-mcp-server

# Using pipx (recommended)
pipx install truenas-mcp-server

# Using uvx (no installation required)
uvx truenas-mcp-server
```

### Configuration

Create a `.env` file:

```env
TRUENAS_URL=https://your-truenas-server
TRUENAS_API_KEY=your-api-key-here
TRUENAS_VERIFY_SSL=true
LOG_LEVEL=INFO
ENABLE_CACHE=true
CACHE_TTL=300
RATE_LIMIT_PER_MINUTE=60
```

### Running the Server

```bash
truenas-mcp-server
```

## Architecture

```
┌─────────────────────────────────────────────┐
│           Claude / AI Assistant             │
└─────────────────┬───────────────────────────┘
                  │ MCP Protocol
┌─────────────────▼───────────────────────────┐
│         TrueNAS MCP Server                  │
│  ┌──────────┐  ┌─────────┐  ┌────────────┐ │
│  │  Cache   │  │  Rate   │  │  Metrics   │ │
│  │  Layer   │  │ Limiter │  │ Collector  │ │
│  └──────────┘  └─────────┘  └────────────┘ │
│  ┌──────────────────────────────────────┐  │
│  │         Tools Layer                   │  │
│  │  Storage │ Users │ Sharing │ Snapshots│  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │         HTTP Client                   │  │
│  │  Connection Pool │ Retry │ Auth      │  │
│  └──────────────────────────────────────┘  │
└─────────────────┬───────────────────────────┘
                  │ HTTPS API
┌─────────────────▼───────────────────────────┐
│           TrueNAS Core Server               │
└─────────────────────────────────────────────┘
```

## Use Cases

### 1. Storage Management
"Create a new dataset named 'backups' on pool 'tank' with compression enabled"

### 2. Snapshot Management
"Create a snapshot of tank/data and schedule daily snapshots"

### 3. User Administration
"Create a new user 'john' with home directory and add to 'developers' group"

### 4. Share Configuration
"Set up an SMB share for /mnt/tank/data accessible by the team"

## Documentation

- [Installation Guide](guides/INSTALL.md)
- [Quick Start Guide](guides/QUICKSTART.md)
- [Feature Overview](FEATURES.md)
- [API Reference](api/client.md)
- [Troubleshooting](troubleshooting.md)

## Requirements

- Python 3.10 or higher
- TrueNAS Core 13.0 or higher
- Valid TrueNAS API key

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](https://github.com/vespo92/TrueNasCoreMCP/blob/main/LICENSE)

## Support

- GitHub Issues: https://github.com/vespo92/TrueNasCoreMCP/issues
- Documentation: https://github.com/vespo92/TrueNasCoreMCP/wiki
