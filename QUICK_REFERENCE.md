# TrueNAS MCP Server - Quick Reference

## 🚀 Common Claude Commands

### Storage Management
```
"List all pools"
"Show me datasets in tank pool"
"Create dataset tank/backups with compression"
"Get status of tank pool"
```

### User Management
```
"List all users"
"Show details for user john"
"Which groups is mary in?"
```

### Permissions (Phase 2)
```
"Set permissions 755 on tank/data"
"Change owner of tank/shared to john"
"Make tank/public readable by everyone"
"Set ACLs for developers group on tank/code"
```

### Properties (Phase 2)
```
"Enable lz4 compression on tank/data"
"Set 100GB quota on tank/users/alice"
"Disable atime on tank/vms"
"Show all properties for tank/media"
```

### Snapshots
```
"Take snapshot of tank/important"
"Create recursive snapshot of tank/vms called pre-update"
"Set up daily snapshots for tank/data keeping 30 days"
```

### Sharing
```
"List all SMB shares"
"Create SMB share for /mnt/tank/public"
"Create NFS export for tank/k8s accessible from 10.0.0.0/24"
```

### Kubernetes (Phase 2)
```
"Create NFS export for my k8s cluster"
"Create 50GB iSCSI target for postgres"
"Generate StorageClass YAML for tank/k8s-volumes"
```

## 🛠️ Development Commands

### Setup
```bash
# Quick setup (recommended)
./quick_setup.sh  # macOS/Linux
# or
quick_setup.bat   # Windows

# Using make (if dev dependencies needed)
make setup

# Manual setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your details
```

### Testing
```bash
# Test connection
make test-conn
# or
python tests/test_connection.py

# Run all tests
make test
# or
pytest tests/

# Test with coverage
make test-cov
```

### Running
```bash
# Run server
make run
# or
python truenas_mcp_server.py

# Run in Claude Desktop
# Add to claude_desktop_config.json
```

### Code Quality
```bash
# Format code
make format
# or
black truenas_mcp_server.py

# Lint
make lint
# or
flake8 truenas_mcp_server.py

# Type check
make typecheck
# or
mypy truenas_mcp_server.py
```

### Cleanup
```bash
# Clean temp files
make clean

# Remove TODELETE folder (after review)
rm -rf TODELETE/
```

## 📝 Configuration

### Environment Variables (.env)
```env
TRUENAS_URL=https://192.168.1.100
TRUENAS_API_KEY=1-your-api-key-here
TRUENAS_VERIFY_SSL=false
```

### Claude Desktop Config
```json
{
  "mcpServers": {
    "truenas": {
      "command": "python",
      "args": ["/full/path/to/truenas_mcp_server.py"],
      "env": {
        "TRUENAS_URL": "https://192.168.1.100",
        "TRUENAS_API_KEY": "1-your-api-key",
        "TRUENAS_VERIFY_SSL": "false"
      }
    }
  }
}
```

## 🔍 Troubleshooting

### Connection Issues
```bash
# Check environment
python -c "import os; print(os.getenv('TRUENAS_URL'))"

# Test API directly
curl -k -H "Authorization: Bearer YOUR-API-KEY" \
  https://your-truenas-ip/api/v2.0/system/info

# Debug mode
python tests/debug_mcp.py
```

### Common Fixes
1. **401 Unauthorized**: Check API key in TrueNAS Settings → API Keys
2. **Connection refused**: Verify TrueNAS IP and port 443
3. **SSL errors**: Set `TRUENAS_VERIFY_SSL=false` for self-signed certs
4. **Import errors**: Activate virtual environment first

## 📚 Resources

- **Documentation**: [FEATURES.md](FEATURES.md)
- **Examples**: [examples/](examples/)
- **Tests**: [tests/](tests/)
- **Issues**: [GitHub Issues](https://github.com/vespo92/TrueNasCoreMCP/issues)

## 🎯 Quick Examples

### Create Development Dataset
```
1. "Create dataset tank/dev"
2. "Set compression lz4 on tank/dev"
3. "Set permissions 775 on tank/dev with group developers"
4. "Create SMB share DevShare for /mnt/tank/dev"
```

### Set Up Kubernetes Storage
```
1. "Create dataset tank/k8s"
2. "Create NFS export for tank/k8s from 10.0.0.0/16"
3. "Show me the StorageClass YAML"
```

### Automated Backups
```
1. "Create dataset tank/backups"
2. "Enable compression zstd on tank/backups"
3. "Create daily snapshots keeping 30 days"
```

## 🆘 Getting Help

- **Read the docs**: Start with [README.md](README.md) and [FEATURES.md](FEATURES.md)
- **Check examples**: Look in [examples/](examples/) for code samples
- **Run tests**: Use `make test` to verify your setup
- **Open an issue**: Report bugs or request features on GitHub
- **Join discussions**: Ask questions in GitHub Discussions

---

**Pro Tip**: Use `make help` to see all available development commands!
