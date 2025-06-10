#!/bin/bash

echo "TrueNAS Core MCP Server Setup"
echo "============================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv venv

echo
echo "Activating virtual environment..."
source venv/bin/activate

echo
echo "Installing dependencies..."
pip install -r requirements.txt

echo
echo "Creating .env file from template..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo
    echo "IMPORTANT: Please edit .env file with your TrueNAS connection details!"
fi

echo
echo "Setup complete!"
echo
echo "Next steps:"
echo "1. Edit .env file with your TrueNAS URL and API key"
echo "2. Run 'python test_connection.py' to verify connectivity"
echo "3. Configure Claude Desktop with this MCP server"
echo
