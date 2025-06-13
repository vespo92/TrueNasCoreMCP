#!/bin/bash
# Quick verification script for CI/CD fixes

echo "🔍 Verifying GitHub Actions CI/CD Fixes"
echo "======================================="

# Check Python version
echo -e "\n📌 Checking Python version requirement..."
grep -n "python_requires" setup.py pyproject.toml | grep -E "3\.(8|9)" && echo "❌ Found old Python version requirements!" || echo "✅ Python version requirements updated"

# Check for deprecated actions
echo -e "\n📌 Checking for deprecated GitHub Actions..."
grep -rn "upload-artifact@v3" .github/workflows/ && echo "❌ Found deprecated upload-artifact@v3!" || echo "✅ No deprecated upload-artifact found"
grep -rn "create-release@v1" .github/workflows/ && echo "❌ Found deprecated create-release@v1!" || echo "✅ No deprecated create-release found"
grep -rn "upload-release-asset@v1" .github/workflows/ && echo "❌ Found deprecated upload-release-asset@v1!" || echo "✅ No deprecated upload-release-asset found"

# Check test matrix
echo -e "\n📌 Checking test matrix..."
grep -n "3.9" .github/workflows/tests.yml | grep python-version && echo "❌ Python 3.9 still in test matrix!" || echo "✅ Python 3.9 removed from test matrix"

# Check MCP in requirements
echo -e "\n📌 Checking MCP package requirement..."
grep "^mcp>=" requirements.txt && echo "✅ MCP package in requirements.txt" || echo "❌ MCP package missing from requirements.txt"

echo -e "\n✨ Verification complete!"
