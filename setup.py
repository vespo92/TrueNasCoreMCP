#!/usr/bin/env python
"""
Setup configuration for TrueNAS MCP Server
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements(filename):
    with open(filename, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Package metadata
setup(
    name="truenas-mcp-server",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="MCP server for TrueNAS Core/Scale - Control your NAS through natural language",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/truenas-mcp-server",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/truenas-mcp-server/issues",
        "Documentation": "https://github.com/yourusername/truenas-mcp-server/wiki",
        "Source Code": "https://github.com/yourusername/truenas-mcp-server",
    },
    
    # Package configuration
    py_modules=["truenas_mcp_server"],
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*", "utils", "docs", "TODELETE"]),
    include_package_data=True,
    
    # Dependencies
    install_requires=read_requirements("requirements.txt"),
    
    # Development dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "flake8-docstrings>=1.7.0",
            "mypy>=1.0.0",
            "isort>=5.12.0",
            "pre-commit>=3.0.0",
            "safety>=2.3.0",
            "bandit>=1.7.5",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
            "mkdocstrings[python]>=0.24.0",
        ],
    },
    
    # Python version requirement
    python_requires=">=3.10",
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: System :: Filesystems",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: AsyncIO",
    ],
    
    # Keywords for PyPI
    keywords="truenas mcp claude api nas storage zfs smb nfs iscsi kubernetes",
    
    # Entry points
    entry_points={
        "console_scripts": [
            "truenas-mcp=truenas_mcp_server:main",
        ],
    },
    
    # Package data
    package_data={
        "": ["*.md", "*.json", ".env.example"],
    },
    
    # Zip safe
    zip_safe=False,
)
