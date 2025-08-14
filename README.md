# TrueNAS MCP Server

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![MCP Version](https://img.shields.io/badge/MCP-1.1.0%2B-green)](https://github.com/modelcontextprotocol/python-sdk)
[![License](https://img.shields.io/badge/license-MIT-purple)](LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/truenas-mcp-server)](https://pypi.org/project/truenas-mcp-server/)

A production-ready Model Context Protocol (MCP) server for TrueNAS Core systems. Control and manage your TrueNAS storage through natural language with Claude or other MCP-compatible clients.

## 🚀 Features

### Core Capabilities
- **User Management** - Create, update, delete users and manage permissions
- **Storage Management** - Manage pools, datasets, volumes with full ZFS support  
- **File Sharing** - Configure SMB, NFS, and iSCSI shares
- **Snapshot Management** - Create, delete, rollback snapshots with automation
- **System Monitoring** - Check system health, pool status, and resource usage

### Enterprise Features
- **Type-Safe Operations** - Full Pydantic models for request/response validation
- **Comprehensive Error Handling** - Detailed error messages and recovery guidance
- **Production Logging** - Structured logging with configurable levels
- **Connection Pooling** - Efficient HTTP connection management with retry logic
- **Rate Limiting** - Built-in rate limiting to prevent API abuse
- **Environment-Based Config** - Flexible configuration via environment variables

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install truenas-mcp-server
```

### From Source

```bash
git clone https://github.com/vespo92/TrueNasCoreMCP.git
cd TrueNasCoreMCP
pip install -e .
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required
TRUENAS_URL=https://your-truenas-server.local
TRUENAS_API_KEY=your-api-key-here

# Optional
TRUENAS_VERIFY_SSL=true                    # Verify SSL certificates
TRUENAS_LOG_LEVEL=INFO                     # Logging level
TRUENAS_ENV=production                     # Environment (development/staging/production)
TRUENAS_HTTP_TIMEOUT=30                    # HTTP timeout in seconds
TRUENAS_ENABLE_DESTRUCTIVE_OPS=false      # Enable delete operations
TRUENAS_ENABLE_DEBUG_TOOLS=false          # Enable debug tools
```

### Getting Your API Key

1. Log into TrueNAS Web UI
2. Go to **Settings → API Keys**
3. Click **Add** and create a new API key
4. Copy the key immediately (it won't be shown again)

### Claude Desktop Configuration

1. **Install the package via pip** (in Claude Desktop's Python environment):
```bash
pip install truenas-mcp-server
```

2. **Add to your Claude Desktop config** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "truenas": {
      "command": "python",
      "args": ["-m", "truenas_mcp_server"],
      "env": {
        "TRUENAS_URL": "https://your-truenas-server.local",
        "TRUENAS_API_KEY": "your-api-key-here",
        "TRUENAS_VERIFY_SSL": "false"
      }
    }
  }
}
```

**Note**: Make sure to install the package in the same Python environment that Claude Desktop uses.

## 📚 Usage Examples

### With Claude Desktop

Once configured, you can interact with TrueNAS using natural language:

```
"List all storage pools and their health status"
"Create a new dataset called 'backups' in the tank pool with compression"
"Set up an SMB share for the documents dataset"
"Create a snapshot of all datasets in the tank pool"
"Show me users who have sudo privileges"
```

### As a Python Library

```python
from truenas_mcp_server import TrueNASMCPServer

# Create server instance
server = TrueNASMCPServer()

# Run the server
server.run()
```

### Programmatic Usage

```python
import asyncio
from truenas_mcp_server.client import TrueNASClient
from truenas_mcp_server.config import Settings

async def main():
    # Initialize client
    settings = Settings(
        truenas_url="https://truenas.local",
        truenas_api_key="your-api-key"
    )
    
    async with TrueNASClient(settings) as client:
        # List pools
        pools = await client.get("/pool")
        print(f"Found {len(pools)} pools")
        
        # Create a dataset
        dataset = await client.post("/pool/dataset", {
            "name": "tank/mydata",
            "compression": "lz4"
        })
        print(f"Created dataset: {dataset['name']}")

asyncio.run(main())
```

## 🛠️ Available Tools

### User Management
- `list_users` - List all users with details
- `get_user` - Get specific user information
- `create_user` - Create new user account
- `update_user` - Modify user properties
- `delete_user` - Remove user account

### Storage Management
- `list_pools` - Show all storage pools
- `get_pool_status` - Detailed pool health and statistics
- `list_datasets` - List all datasets
- `create_dataset` - Create new dataset with options
- `update_dataset` - Modify dataset properties
- `delete_dataset` - Remove dataset

### File Sharing
- `list_smb_shares` - Show SMB/CIFS shares
- `create_smb_share` - Create Windows share
- `list_nfs_exports` - Show NFS exports
- `create_nfs_export` - Create NFS export
- `list_iscsi_targets` - Show iSCSI targets
- `create_iscsi_target` - Create iSCSI target

### Snapshot Management
- `list_snapshots` - Show snapshots
- `create_snapshot` - Create manual snapshot
- `delete_snapshot` - Remove snapshot
- `rollback_snapshot` - Revert to snapshot
- `clone_snapshot` - Clone to new dataset
- `create_snapshot_task` - Setup automated snapshots

### Debug Tools (Development Mode)
- `debug_connection` - Check connection settings
- `test_connection` - Verify API connectivity
- `get_server_stats` - Server statistics

## 🏗️ Architecture

```
truenas_mcp_server/
├── __init__.py           # Package initialization
├── server.py             # Main MCP server
├── config/               # Configuration management
│   ├── __init__.py
│   └── settings.py       # Pydantic settings
├── client/               # HTTP client
│   ├── __init__.py
│   └── http_client.py    # Async HTTP with retry
├── models/               # Data models
│   ├── __init__.py
│   ├── base.py          # Base models
│   ├── user.py          # User models
│   ├── storage.py       # Storage models
│   └── sharing.py       # Share models
├── tools/                # MCP tools
│   ├── __init__.py
│   ├── base.py          # Base tool class
│   ├── users.py         # User tools
│   ├── storage.py       # Storage tools
│   ├── sharing.py       # Share tools
│   └── snapshots.py     # Snapshot tools
└── exceptions.py         # Custom exceptions
```

## 🧪 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/vespo92/TrueNasCoreMCP.git
cd TrueNasCoreMCP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=truenas_mcp_server

# Specific test file
pytest tests/test_client.py
```

### Code Quality

```bash
# Format code
black truenas_mcp_server

# Lint
flake8 truenas_mcp_server

# Type checking
mypy truenas_mcp_server
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security

- Never commit API keys or credentials
- Use environment variables for sensitive data
- Enable SSL verification in production
- Restrict destructive operations by default
- Report security issues to vespo21@gmail.com

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/vespo92/TrueNasCoreMCP/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vespo92/TrueNasCoreMCP/discussions)
- **Email**: vespo21@gmail.com

## 🙏 Acknowledgments

- [Anthropic](https://www.anthropic.com/) for the MCP specification
- [TrueNAS](https://www.truenas.com/) for the excellent storage platform
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) contributors

---

**Made with ❤️ for the TrueNAS community**