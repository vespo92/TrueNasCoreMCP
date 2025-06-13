# Makefile for TrueNAS MCP Server
# Provides common development commands

.PHONY: help install install-dev clean test lint format run setup docs

# Default target
help:
	@echo "TrueNAS MCP Server - Development Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup        - Complete initial setup"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test         - Run all tests (or minimal if pytest not installed)"
	@echo "  make test-minimal - Run minimal tests (no pytest required)"
	@echo "  make test-cov     - Run tests with coverage (requires pytest)"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code with Black"
	@echo "  make clean        - Clean up temporary files"
	@echo ""
	@echo "Running:"
	@echo "  make run          - Run the MCP server"
	@echo "  make test-conn    - Test TrueNAS connection"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs         - Build documentation"
	@echo "  make docs-serve   - Serve documentation locally"

# Setup virtual environment and install everything
setup:
	@echo "🔧 Setting up development environment..."
	@if command -v python3 >/dev/null 2>&1; then \
		PYTHON_CMD=python3; \
	elif command -v python >/dev/null 2>&1; then \
		PYTHON_CMD=python; \
	else \
		echo "❌ Python not found. Please install Python 3.8 or higher."; \
		exit 1; \
	fi; \
	$$PYTHON_CMD -m venv venv
	@echo "✅ Virtual environment created"
	@echo ""
	@echo "📦 Installing dependencies..."
	@if [ -f venv/bin/activate ]; then \
		. venv/bin/activate && pip install --upgrade pip setuptools wheel; \
		. venv/bin/activate && pip install -r requirements.txt; \
	else \
		venv\\Scripts\\activate && pip install --upgrade pip setuptools wheel; \
		venv\\Scripts\\activate && pip install -r requirements.txt; \
	fi
	@echo "✅ Core dependencies installed"
	@echo ""
	@echo "📦 Installing development dependencies (optional)..."
	@if [ -f venv/bin/activate ]; then \
		. venv/bin/activate && pip install -r requirements-dev.txt || echo "⚠️  Some dev dependencies failed to install (this is okay)"; \
	else \
		venv\\Scripts\\activate && pip install -r requirements-dev.txt || echo "⚠️  Some dev dependencies failed to install (this is okay)"; \
	fi
	@echo ""
	@echo "📋 Creating .env from example..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file - please edit with your TrueNAS details"; \
	else \
		echo "⚠️  .env already exists - skipping"; \
	fi
	@echo ""
	@echo "🎉 Setup complete! Next steps:"
	@echo "  1. Edit .env with your TrueNAS details"
	@echo "  2. Activate virtual environment:"
	@echo "     - macOS/Linux: source venv/bin/activate"
	@echo "     - Windows: venv\\Scripts\\activate"
	@echo "  3. Run 'make test-conn' to test the connection"

# Install production dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt

# Clean up temporary files
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf dist/ build/ 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Run tests
test:
	@echo "🧪 Running tests..."
	@if command -v pytest >/dev/null 2>&1; then \
		pytest tests/ -v; \
	else \
		echo "⚠️  pytest not installed, running minimal tests..."; \
		python tests/minimal_test.py; \
	fi

# Run minimal tests (no pytest required)
test-minimal:
	@echo "🧪 Running minimal tests..."
	python tests/minimal_test.py

# Run tests with coverage
test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest tests/ --cov=truenas_mcp_server --cov-report=html --cov-report=term

# Test TrueNAS connection
test-conn:
	@echo "🔌 Testing TrueNAS connection..."
	python tests/test_connection.py

# Run linting
lint:
	@echo "🔍 Running linting checks..."
	flake8 truenas_mcp_server.py tests/ examples/ --max-line-length=100 --exclude=venv,build,dist,TODELETE
	@echo "✅ Linting passed"

# Format code
format:
	@echo "🎨 Formatting code with Black..."
	black truenas_mcp_server.py tests/ examples/ --line-length=100
	isort truenas_mcp_server.py tests/ examples/
	@echo "✅ Formatting complete"

# Type checking
typecheck:
	@echo "🔍 Running type checks..."
	mypy truenas_mcp_server.py --ignore-missing-imports

# Security scan
security:
	@echo "🔒 Running security scan..."
	bandit -r truenas_mcp_server.py
	safety check

# Run the MCP server
run:
	@echo "🚀 Starting TrueNAS MCP Server..."
	@echo "Press Ctrl+C to stop"
	@python truenas_mcp_server.py

# Build documentation
docs:
	@echo "📚 Building documentation..."
	@if command -v mkdocs &> /dev/null; then \
		mkdocs build; \
	else \
		echo "⚠️  mkdocs not installed. Run: pip install mkdocs mkdocs-material"; \
	fi

# Serve documentation locally
docs-serve:
	@echo "📚 Serving documentation at http://localhost:8000..."
	@if command -v mkdocs &> /dev/null; then \
		mkdocs serve; \
	else \
		echo "⚠️  mkdocs not installed. Run: pip install mkdocs mkdocs-material"; \
	fi

# Create distribution package
dist:
	@echo "📦 Creating distribution package..."
	python -m build
	@echo "✅ Package created in dist/"

# Upload to PyPI (test)
upload-test:
	@echo "📤 Uploading to TestPyPI..."
	python -m twine upload --repository testpypi dist/*

# Upload to PyPI (production)
upload:
	@echo "📤 Uploading to PyPI..."
	@echo "⚠️  Are you sure? This will upload to the real PyPI!"
	@read -p "Continue? (y/N) " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		python -m twine upload dist/*; \
	else \
		echo "Upload cancelled"; \
	fi

# Install pre-commit hooks
pre-commit:
	@echo "🔗 Installing pre-commit hooks..."
	pre-commit install
	@echo "✅ Pre-commit hooks installed"

# Run pre-commit on all files
pre-commit-all:
	@echo "🔍 Running pre-commit on all files..."
	pre-commit run --all-files

# Update dependencies
update-deps:
	@echo "📦 Updating dependencies..."
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip freeze > requirements-lock.txt
	@echo "✅ Dependencies updated. Lock file created: requirements-lock.txt"

# Development environment info
info:
	@echo "TrueNAS MCP Server - Environment Info"
	@echo "====================================="
	@echo ""
	@echo "Python Version:"
	@python --version
	@echo ""
	@echo "Installed Packages:"
	@pip list | grep -E "(mcp|httpx|dotenv)"
	@echo ""
	@echo "Environment Variables:"
	@if [ -f .env ]; then \
		echo "TRUENAS_URL=$$(grep TRUENAS_URL .env | cut -d'=' -f2)"; \
		echo "TRUENAS_API_KEY=$$(grep TRUENAS_API_KEY .env | cut -d'=' -f2 | sed 's/\(.\{10\}\).*/\1.../')"; \
		echo "TRUENAS_VERIFY_SSL=$$(grep TRUENAS_VERIFY_SSL .env | cut -d'=' -f2)"; \
	else \
		echo "⚠️  .env file not found"; \
	fi
	@echo ""
	@echo "Project Structure:"
	@echo "  Main: truenas_mcp_server.py"
	@echo "  Tests: tests/"
	@echo "  Examples: examples/"
	@echo "  Utils: utils/"
	@echo "  Docs: docs/"
