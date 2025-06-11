# TrueNAS Core MCP Server

A Model Context Protocol (MCP) server that enables Claude Desktop (or any MCP client) to interact with TrueNAS Core systems through the TrueNAS API.

## Features

- **User Management**: List users, get user details
- **System Information**: Get TrueNAS system info
- **Storage Management**: List pools, datasets, create datasets
- **Sharing**: List and create SMB shares
- **Snapshots**: Create ZFS snapshots

## Prerequisites

- Python 3.8 or higher
- TrueNAS Core system with API access
- Claude Desktop (or any MCP-compatible client)
- TrueNAS API key

## Installation

1. Clone this repository:
```bash
git clone https://github.com/vespo92/TrueNasCoreMCP.git
cd truenas-core-mcp
```

2. Create a virtual environment:
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your TrueNAS details
```

## Getting Your TrueNAS API Key

1. Log into your TrueNAS Core web interface
2. Navigate to **Settings** → **API Keys**
3. Click **Add**
4. Give your key a name (e.g., "MCP Server")
5. Click **Submit**
6. Copy the generated API key (you won't be able to see it again!)

## Configuration

Edit the `.env` file with your TrueNAS connection details:

```env
TRUENAS_URL=https://192.168.1.100  # Your TrueNAS IP or hostname
TRUENAS_API_KEY=1-your-api-key-here
TRUENAS_VERIFY_SSL=false  # Set to true if using valid SSL certificates
```

## Running the Server

### Standalone Mode (for testing)

```bash
python truenas_mcp_server.py
```

### With Claude Desktop

1. Open Claude Desktop settings
2. Navigate to the MCP servers configuration
3. Add the following configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "truenas": {
      "command": "python",
      "args": [
        "C:\\path\\to\\truenas_mcp_server.py"
      ],
      "env": {
        "TRUENAS_URL": "https://your-truenas-ip",
        "TRUENAS_API_KEY": "your-api-key",
        "TRUENAS_VERIFY_SSL": "false"
      }
    }
  }
}
```

4. Restart Claude Desktop

## Available Functions

### User Management
- `list_users()` - List all users in the system
- `get_user(username)` - Get detailed information about a specific user

### System Information
- `get_system_info()` - Get TrueNAS system information

### Storage Management
- `list_pools()` - List all storage pools
- `list_datasets()` - List all datasets
- `get_pool_status(pool_name)` - Get detailed status of a specific pool
- `create_dataset(pool, name, compression="lz4", quota=None)` - Create a new dataset

### Sharing
- `list_smb_shares()` - List all SMB shares
- `create_smb_share(path, name, comment="", read_only=False)` - Create a new SMB share

### Snapshots
- `create_snapshot(dataset, name, recursive=False)` - Create a ZFS snapshot

## Example Usage in Claude

Once configured, you can ask Claude to:

- "List all users in my TrueNAS system"
- "Show me the storage pools"
- "Create a new dataset called 'backups' in the 'tank' pool"
- "List all SMB shares"
- "Create a snapshot of tank/data"

## Security Considerations

- **API Key**: Keep your API key secure and never commit it to version control
- **SSL Verification**: Enable SSL verification in production environments
- **Network Security**: Ensure your TrueNAS system is only accessible from trusted networks
- **Permissions**: The API key will have the same permissions as the user who created it

## Troubleshooting

### Connection Issues
- Verify your TrueNAS URL is correct (include https://)
- Check if the API service is enabled in TrueNAS
- Ensure your API key is valid
- If using self-signed certificates, set `TRUENAS_VERIFY_SSL=false`

### API Errors
- Check TrueNAS logs for detailed error messages
- Ensure your user has appropriate permissions
- Verify the API endpoint compatibility with your TrueNAS Core version

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built for TrueNAS Core using the official API
- Uses the Model Context Protocol (MCP) by Anthropic
- Powered by FastMCP for easy MCP server creation
