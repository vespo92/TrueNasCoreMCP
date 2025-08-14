# Installation Guide

## Prerequisites

- Python 3.10 or higher
- TrueNAS Core server with API access
- TrueNAS API key

## Installation Methods

### Method 1: Install from PyPI (Recommended)

```bash
pip install truenas-mcp-server
```

Or with specific version:
```bash
pip install truenas-mcp-server==3.0.0
```

### Method 2: Install from GitHub

Install the latest development version directly from GitHub:

```bash
pip install git+https://github.com/vespo92/TrueNasCoreMCP.git
```

Or a specific release:
```bash
pip install git+https://github.com/vespo92/TrueNasCoreMCP.git@v3.0.0
```

### Method 3: Development Installation

For development or contributing:

```bash
# Clone the repository
git clone https://github.com/vespo92/TrueNasCoreMCP.git
cd TrueNasCoreMCP

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Configuration

### Step 1: Get Your TrueNAS API Key

1. Log into your TrueNAS Web UI
2. Navigate to **Settings → API Keys**
3. Click **Add** to create a new API key
4. Copy the generated key immediately (it won't be shown again)

### Step 2: Set Environment Variables

Create a `.env` file in your working directory:

```bash
# Required
TRUENAS_URL=https://your-truenas-server.local
TRUENAS_API_KEY=your-api-key-here

# Optional
TRUENAS_VERIFY_SSL=true
TRUENAS_LOG_LEVEL=INFO
TRUENAS_ENV=production
```

Or export them in your shell:

```bash
export TRUENAS_URL="https://your-truenas-server.local"
export TRUENAS_API_KEY="your-api-key-here"
```

## Claude Desktop Setup

### Step 1: Install the Package

First, ensure the package is installed in Claude Desktop's Python environment:

```bash
# Find Claude Desktop's Python
which python  # Should show Claude's Python path

# Install the package
pip install truenas-mcp-server
```

### Step 2: Configure Claude Desktop

Edit your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

Add the TrueNAS MCP server configuration:

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

### Step 3: Restart Claude Desktop

After saving the configuration, restart Claude Desktop for the changes to take effect.

## Verification

### Test the Installation

```python
# test_connection.py
import asyncio
from truenas_mcp_server import TrueNASMCPServer

async def test():
    server = TrueNASMCPServer()
    await server.initialize()
    print("✅ Connection successful!")

asyncio.run(test())
```

Run the test:
```bash
python test_connection.py
```

### Test with Claude

In Claude Desktop, try these commands:
- "Test connection to TrueNAS"
- "List all storage pools"
- "Show system information"

## Troubleshooting

### SSL Certificate Issues

If you get SSL verification errors with self-signed certificates:

```json
{
  "env": {
    "TRUENAS_VERIFY_SSL": "false"
  }
}
```

⚠️ **Warning**: Only disable SSL verification for development or trusted internal networks.

### Permission Denied

If you get permission errors:
1. Verify your API key has the necessary permissions
2. Check that destructive operations are enabled if needed:
   ```json
   {
     "env": {
       "TRUENAS_ENABLE_DESTRUCTIVE_OPS": "true"
     }
   }
   ```

### Module Not Found

If Claude can't find the module:
1. Verify installation: `pip show truenas-mcp-server`
2. Check Python path: `python -c "import truenas_mcp_server; print(truenas_mcp_server.__file__)"`
3. Ensure Claude Desktop uses the same Python environment

### Connection Timeout

If connections timeout:
1. Verify TrueNAS URL is accessible: `curl https://your-truenas-server.local`
2. Check firewall rules
3. Increase timeout in environment:
   ```json
   {
     "env": {
       "TRUENAS_HTTP_TIMEOUT": "60"
     }
   }
   ```

## Upgrading

To upgrade to the latest version:

```bash
pip install --upgrade truenas-mcp-server
```

Check current version:
```bash
pip show truenas-mcp-server
```

## Uninstalling

To remove the package:

```bash
pip uninstall truenas-mcp-server
```

## Support

- **Issues**: [GitHub Issues](https://github.com/vespo92/TrueNasCoreMCP/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vespo92/TrueNasCoreMCP/discussions)
- **Email**: vespo92@gmail.com