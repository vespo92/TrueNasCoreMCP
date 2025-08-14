# TrueNAS MCP Server Documentation

Welcome to the TrueNAS MCP Server documentation. This directory contains comprehensive guides and references for using and developing with the TrueNAS MCP Server.

## 📚 Documentation Structure

### Getting Started
- [Installation Guide](guides/INSTALL.md) - Complete installation instructions for all platforms
- [Quick Start](guides/QUICKSTART.md) - Get up and running in 5 minutes
- [Quick Reference](guides/QUICK_REFERENCE.md) - Command and tool reference

### Features & Guides
- [Features Overview](guides/FEATURES.md) - Detailed feature documentation
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

### API Documentation
- [API Reference](api/) - Coming soon

### Developer Documentation
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute to the project
- [Security Policy](../SECURITY.md) - Security guidelines and reporting

## 🚀 Quick Links

- **PyPI Package**: https://pypi.org/project/truenas-mcp-server/
- **GitHub Repository**: https://github.com/vespo92/TrueNasCoreMCP
- **Issue Tracker**: https://github.com/vespo92/TrueNasCoreMCP/issues

## 📦 Installation Options

### Fastest (with uvx)
```bash
uvx truenas-mcp-server
```

### Traditional (with pip)
```bash
pip install truenas-mcp-server
```

## 🔧 Configuration

Set your environment variables:
```bash
export TRUENAS_URL="https://your-truenas.local"
export TRUENAS_API_KEY="your-api-key"
```

Or use a `.env` file in your working directory.

## 💬 Getting Help

- Check the [Troubleshooting Guide](troubleshooting.md)
- Open an [issue on GitHub](https://github.com/vespo92/TrueNasCoreMCP/issues)
- Contact: vespo21@gmail.com