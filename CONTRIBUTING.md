# Contributing to TrueNAS MCP Server

First off, thank you for considering contributing to TrueNAS MCP Server! It's people like you that make this project better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Process](#development-process)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please be respectful and inclusive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/TrueNasCoreMCP.git
   cd TrueNasCoreMCP
   ```
3. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **System information** (Python version, TrueNAS version, OS)
- **Relevant logs or error messages**

### 💡 Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Use case** - Why is this enhancement needed?
- **Proposed solution** - How should it work?
- **Alternative solutions** - What other approaches did you consider?
- **Additional context** - Screenshots, mockups, or examples

### 🔧 Pull Requests

1. **Small, focused changes** - One feature or fix per PR
2. **Include tests** - All new code should have tests
3. **Update documentation** - Keep docs in sync with code
4. **Follow style guidelines** - Use our linting and formatting tools
5. **Write good commit messages** - Clear and descriptive

## Development Process

### 1. Setting Up Your Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests to ensure everything works
pytest tests/
```

### 2. Making Changes

- **Write tests first** (TDD approach encouraged)
- **Keep changes focused** - One issue per PR
- **Add docstrings** to all functions and classes
- **Update CHANGELOG.md** for user-facing changes

### 3. Testing Your Changes

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_connection.py

# Run with coverage
pytest --cov=truenas_mcp_server tests/

# Test against a real TrueNAS system
python tests/test_connection.py
```

### 4. Code Quality Checks

```bash
# Format code with Black
black truenas_mcp_server.py tests/ --line-length=100

# Sort imports
isort truenas_mcp_server.py tests/

# Lint with flake8
flake8 truenas_mcp_server.py tests/

# Type checking
mypy truenas_mcp_server.py

# Security scan
bandit -r truenas_mcp_server.py

# Run all pre-commit hooks
pre-commit run --all-files
```

## Style Guidelines

### Python Style

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these additions:

- **Line length**: 100 characters maximum
- **Quotes**: Double quotes for strings, single for dict keys
- **Imports**: Grouped in order (standard library, third-party, local)
- **Type hints**: Encouraged for function signatures

### Code Examples

```python
from typing import Dict, List, Optional, Any
import httpx
from mcp.server.fastmcp import FastMCP

# Good function example
async def get_dataset_info(
    dataset_name: str,
    include_children: bool = False
) -> Dict[str, Any]:
    """
    Retrieve information about a ZFS dataset.
    
    Args:
        dataset_name: The name of the dataset (e.g., "tank/data")
        include_children: Whether to include child datasets
        
    Returns:
        Dictionary containing dataset information
        
    Raises:
        HTTPError: If the API request fails
    """
    # Implementation here
    pass
```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
feat: add support for ZFS encryption
fix: handle special characters in dataset names
docs: update installation instructions
test: add tests for permission management
refactor: simplify API client initialization
chore: update dependencies
```

## Testing

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Use `pytest` fixtures for common setup
- Mock external API calls when possible

Example test:

```python
import pytest
from unittest.mock import Mock, patch
import truenas_mcp_server

@pytest.mark.asyncio
async def test_list_users_success():
    """Test successful user listing"""
    with patch('truenas_mcp_server.get_client') as mock_client:
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = [
            {"username": "admin", "uid": 1000}
        ]
        mock_response.raise_for_status = Mock()
        mock_client.return_value.get.return_value = mock_response
        
        # Test
        result = await truenas_mcp_server.list_users()
        
        # Verify
        assert result["success"] is True
        assert len(result["users"]) == 1
        assert result["users"][0]["username"] == "admin"
```

### Test Categories

1. **Unit tests** - Test individual functions
2. **Integration tests** - Test with real TrueNAS API
3. **End-to-end tests** - Test complete workflows

## Documentation

### Docstring Format

We use Google-style docstrings:

```python
def parse_size(size_str: str) -> int:
    """
    Convert human-readable size to bytes.
    
    Args:
        size_str: Size string like "10G" or "100M"
        
    Returns:
        Size in bytes
        
    Raises:
        ValueError: If size string is invalid
        
    Examples:
        >>> parse_size("10G")
        10737418240
        >>> parse_size("100M")
        104857600
    """
```

### Updating Documentation

When adding features, update:

1. **README.md** - For major features
2. **FEATURES.md** - Detailed feature documentation
3. **CHANGELOG.md** - User-facing changes
4. **API documentation** - Function/parameter changes
5. **Examples** - Add usage examples

## Submitting Changes

### Pull Request Process

1. **Update your fork**:
   ```bash
   git remote add upstream https://github.com/vespo92/TrueNasCoreMCP.git
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request**:
   - Use a clear title and description
   - Reference any related issues
   - Include screenshots for UI changes
   - Check all CI tests pass

4. **Code Review**:
   - Respond to feedback promptly
   - Make requested changes
   - Keep the PR updated with main branch

### PR Checklist

- [ ] Tests pass locally (`pytest tests/`)
- [ ] Code is formatted (`black --check .`)
- [ ] Code passes linting (`flake8`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Commit messages follow convention
- [ ] PR description explains changes

## Recognition

Contributors will be recognized in:
- The project README
- Release notes
- Our contributors page

## Questions?

Feel free to:
- Open a [Discussion](https://github.com/vespo92/TrueNasCoreMCP/discussions)
- Join our community chat
- Email the maintainers

Thank you for contributing to TrueNAS MCP Server! 🎉
