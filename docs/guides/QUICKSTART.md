# Quick Start Guide

Get up and running with TrueNAS Core MCP Server in 5 minutes!

## 1. Get Your TrueNAS API Key

1. Open your TrueNAS Core web interface
2. Go to **Settings** → **API Keys**
3. Click **Add** and name it "MCP Server"
4. Copy the generated key immediately (you can't see it again!)

## 2. Install the MCP Server

### Windows:
```batch
git clone https://github.com/vespo92/TrueNasCoreMCP.git
cd TrueNasCoreMCP
setup.bat
```

### Linux/Mac:
```bash
git clone https://github.com/vespo92/TrueNasCoreMCP.git
cd TrueNasCoreMCP
chmod +x setup.sh
./setup.sh
```

## 3. Configure Your Connection

Edit the `.env` file:
```env
TRUENAS_URL=https://192.168.1.100  # Your TrueNAS IP
TRUENAS_API_KEY=1-abcdef123456...   # Your API key
TRUENAS_VERIFY_SSL=false            # Use 'true' for valid certs
```

## 4. Test the Connection

```bash
# Windows
venv\Scripts\activate
python test_connection.py

# Linux/Mac
source venv/bin/activate
python test_connection.py
```

## 5. Add to Claude Desktop

1. Find your Claude config file:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Add the TrueNAS server configuration:
```json
{
  "mcpServers": {
    "truenas": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\truenas_mcp_server.py"
      ],
      "env": {
        "TRUENAS_URL": "https://192.168.1.100",
        "TRUENAS_API_KEY": "your-api-key",
        "TRUENAS_VERIFY_SSL": "false"
      }
    }
  }
}
```

3. Restart Claude Desktop

## 6. Start Using It!

Ask Claude:
- "List all users in my TrueNAS"
- "Show me my storage pools"
- "Create a dataset called 'photos' in the tank pool"
- "What's the status of my main pool?"

## Troubleshooting

**Connection refused**: Check if your TrueNAS IP is correct and accessible

**401 Unauthorized**: Your API key might be incorrect

**SSL Error**: Set `TRUENAS_VERIFY_SSL=false` for self-signed certificates

Need help? Check the full README or open an issue on GitHub!
