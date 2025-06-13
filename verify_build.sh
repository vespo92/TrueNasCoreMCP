#!/bin/bash
# Verify build configuration

echo "🔍 Verifying Build Configuration"
echo "================================"

# Check for required files
echo -e "\n📌 Checking required files..."
for file in "setup.py" "pyproject.toml" "requirements.txt" "README.md" "LICENSE" "MANIFEST.in"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing!"
    fi
done

# Check Python version in configs
echo -e "\n📌 Checking Python version consistency..."
grep -n "python_requires" setup.py pyproject.toml 2>/dev/null | grep "3.10" && echo "✅ Python version is 3.10+"

# Check for problematic patterns
echo -e "\n📌 Checking for build issues..."
grep -n "read_requirements" setup.py && echo "⚠️ Found read_requirements - may cause build issues!" || echo "✅ No read_requirements function"
grep -n "License :: OSI Approved :: MIT License" setup.py pyproject.toml && echo "⚠️ Found license classifier - may cause warnings!" || echo "✅ No duplicate license classifier"

# Check MANIFEST.in includes requirements.txt
echo -e "\n📌 Checking MANIFEST.in..."
grep "requirements.txt" MANIFEST.in && echo "✅ MANIFEST.in includes requirements.txt" || echo "❌ MANIFEST.in missing requirements.txt"

echo -e "\n✨ Verification complete!"
echo -e "\nTo test the build locally:"
echo "  python -m build"
