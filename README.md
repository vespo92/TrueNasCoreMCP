# TrueNAS MCP Server

<div align="center">

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/yourusername/truenas-mcp-server/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.com)
[![TrueNAS](https://img.shields.io/badge/TrueNAS-Core%20%7C%20Scale-red.svg)](https://www.truenas.com/)
[![Tested](https://img.shields.io/badge/tested%20on-TrueNAS--13.0--U6.1-brightgreen.svg)](https://www.truenas.com/)

**Control your TrueNAS system using natural language through Claude Desktop**

[Features](#features) • [Quick Start](#quick-start) • [Installation](#installation) • [Documentation](#documentation) • [Examples](#examples)

</div>

---

## 🌟 Overview

TrueNAS MCP Server enables seamless interaction between Claude Desktop (or any MCP client) and your TrueNAS system. Manage storage, users, permissions, and even Kubernetes storage backends—all through natural language commands.

### 🎯 Key Features

- **🗂️ Storage Management** - Create and manage pools, datasets, and snapshots
- **👥 User Administration** - List, view, and manage system users
- **🔐 Advanced Permissions** - Control Unix permissions and ACLs with simple commands
- **☸️ Kubernetes Ready** - Export NFS shares and create iSCSI targets for K8s
- **🤖 Automation** - Set up automated snapshot policies and retention
- **📊 Property Control** - Manage ZFS properties like compression, deduplication, and quotas

### ✅ Tested On

- **TrueNAS Core**: Version 13.0-U6.1
- **API Version**: v2.0
- **Python**: 3.8+

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- TrueNAS Core/Scale system with API access
- Claude Desktop (or any MCP-compatible client)
- TrueNAS API key

### 1. Clone & Install

```bash
# Clone the repository
git clone https://github.com/yourusername/truenas-mcp-server.git
cd truenas-mcp-server

# Quick setup (recommended)
./quick_setup.sh  # On Windows: quick_setup.bat

# Or manual setup:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy example config
cp .env.example .env

# Edit with your TrueNAS details
nano .env
```

Set your TrueNAS connection details:
```env
TRUENAS_URL=https://192.168.1.100
TRUENAS_API_KEY=1-your-api-key-here
TRUENAS_VERIFY_SSL=false
```

### 3. Test Connection

```bash
python tests/test_connection.py
```

### 4. Configure Claude Desktop

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "truenas": {
      "command": "python",
      "args": ["/path/to/truenas_mcp_server.py"],
      "env": {
        "TRUENAS_URL": "https://your-truenas-ip",
        "TRUENAS_API_KEY": "your-api-key",
        "TRUENAS_VERIFY_SSL": "false"
      }
    }
  }
}
```

## 📚 Documentation

### Getting Your API Key

1. Log into TrueNAS web interface
2. Navigate to **Settings** → **API Keys**
3. Click **Add** and name your key
4. Copy the generated key immediately

### Example Commands

Once configured, ask Claude natural language questions:

#### Basic Operations
- "List all users in my TrueNAS"
- "Show me the storage pools"
- "Create a dataset called backups in the tank pool"
- "Take a snapshot of tank/important"

#### Advanced Features
- "Set permissions 755 on tank/shared with owner john"
- "Enable compression on tank/backups"
- "Create an NFS export for my Kubernetes cluster"
- "Set up daily snapshots for tank/data with 30-day retention"

### Detailed Documentation

- 📖 [Complete Feature List](docs/features.md)
- 🔧 [Troubleshooting Guide](docs/troubleshooting.md)
- 🚀 [Deployment Options](docs/deployment.md)
- 📡 [API Reference](docs/api_reference.md)

## 🛠️ Available Functions

<details>
<summary><b>Storage Management</b></summary>

- `list_pools()` - View all storage pools
- `list_datasets()` - List all datasets
- `get_pool_status()` - Detailed pool information
- `create_dataset()` - Create new datasets
- `modify_dataset_properties()` - Change ZFS properties
- `get_dataset_properties()` - View dataset configuration

</details>

<details>
<summary><b>User & Permission Management</b></summary>

- `list_users()` - List system users
- `get_user()` - Detailed user information
- `modify_dataset_permissions()` - Change Unix permissions
- `update_dataset_acl()` - Manage Access Control Lists
- `get_dataset_permissions()` - View current permissions

</details>

<details>
<summary><b>Sharing & Kubernetes</b></summary>

- `list_smb_shares()` - View SMB/CIFS shares
- `create_smb_share()` - Create new SMB shares
- `create_nfs_export()` - NFS exports for Kubernetes
- `create_iscsi_target()` - iSCSI block storage

</details>

<details>
<summary><b>Snapshots & Automation</b></summary>

- `create_snapshot()` - Manual snapshots
- `create_snapshot_policy()` - Automated snapshot schedules

</details>

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black truenas_mcp_server.py

# Lint
flake8 truenas_mcp_server.py
```

## 🔒 Security

- API keys are stored securely in environment variables
- SSL/TLS verification is configurable
- Never commit `.env` files or API keys
- See [Security Policy](SECURITY.md) for reporting vulnerabilities

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for [TrueNAS](https://www.truenas.com/) Core and Scale
- Powered by [Model Context Protocol](https://modelcontextprotocol.com) (MCP)
- Uses [FastMCP](https://github.com/jlowin/fastmcp) for easy server creation
- Tested on TrueNAS-13.0-U6.1

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/truenas-mcp-server&type=Date)](https://star-history.com/#yourusername/truenas-mcp-server&Date)

---

<div align="center">
Made with ❤️ for the TrueNAS community
</div>
