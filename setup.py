#!/usr/bin/env python
"""
Setup configuration for TrueNAS MCP Server
"""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Package metadata
setup(
    name="truenas-mcp-server",
    version="3.0.0",
    author="Vinnie Espo",
    author_email="vespo92@gmail.com",
    description="MCP server for TrueNAS Core - Control your NAS through natural language",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vespo92/TrueNasCoreMCP",
    project_urls={
        "Bug Tracker": "https://github.com/vespo92/TrueNasCoreMCP/issues",
        "Documentation": "https://github.com/vespo92/TrueNasCoreMCP/wiki",
        "Source Code": "https://github.com/vespo92/TrueNasCoreMCP",
    },
    
    # Package configuration
    py_modules=["truenas_mcp_server"],
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*", "utils", "docs", "TODELETE"]),
    include_package_data=True,
    
    # Dependencies - these are now in pyproject.toml
    # Let pyproject.toml handle the dependencies
    
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
    
    # Zip safe
    zip_safe=False,
)
