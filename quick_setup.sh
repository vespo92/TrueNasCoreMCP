#!/bin/bash
# Quick setup script for TrueNAS MCP Server

echo "🔧 TrueNAS MCP Server - Quick Setup"
echo "==================================="
echo

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Python not found. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Found Python: $($PYTHON_CMD --version)"
echo

# Create virtual environment
echo "📦 Creating virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if [[ "$OSTYPE" == "win"* ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install core requirements
echo "📦 Installing core requirements..."
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file..."
    cp .env.example .env
    echo "✅ Created .env file - please edit with your TrueNAS details"
else
    echo "⚠️  .env already exists"
fi

echo
echo "🎉 Basic setup complete!"
echo
echo "Next steps:"
echo "1. Edit .env with your TrueNAS connection details"
echo "2. Test connection: python tests/test_connection.py"
echo "3. Run server: python truenas_mcp_server.py"
echo
echo "For development dependencies (optional):"
echo "pip install pytest pytest-asyncio black flake8"
