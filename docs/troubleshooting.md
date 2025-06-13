# Installation Troubleshooting

## Common Issues

### Development Dependencies Installation Error

If you encounter errors installing development dependencies like:
```
ERROR: Could not find a version that satisfies the requirement types-python-dotenv>=1.0.0
```

**Solution**: Use the quick setup script which only installs core dependencies:

```bash
# macOS/Linux
./quick_setup.sh

# Windows
quick_setup.bat
```

Or install only the core requirements:
```bash
pip install -r requirements.txt
```

The development dependencies are optional and only needed if you plan to:
- Run the test suite with pytest
- Use code formatting tools (black, isort)
- Use linting tools (flake8, mypy)
- Build documentation

### Python Version Issues

Ensure you have Python 3.8 or higher:
```bash
python --version
# or
python3 --version
```

### Virtual Environment Not Activating

**macOS/Linux**:
```bash
source venv/bin/activate
```

**Windows**:
```bash
venv\Scripts\activate
```

### Connection Issues

1. **Check your .env file exists and has correct values**:
   ```bash
   cat .env  # macOS/Linux
   type .env # Windows
   ```

2. **Test basic functionality**:
   ```bash
   python tests/simple_test.py
   ```

3. **Test TrueNAS connection**:
   ```bash
   python tests/test_connection.py
   ```

### SSL Certificate Errors

If you get SSL certificate verification errors with self-signed certificates:

1. Set `TRUENAS_VERIFY_SSL=false` in your `.env` file
2. This is common with home TrueNAS installations

### API Key Issues

1. Ensure your API key is copied exactly from TrueNAS
2. API keys typically start with "1-" or "2-"
3. Check for extra spaces or line breaks in the .env file

## Getting Help

If you're still having issues:

1. Check the [GitHub Issues](https://github.com/vespo92/TrueNasCoreMCP/issues)
2. Run the simple test to verify basic functionality:
   ```bash
   python tests/simple_test.py
   ```
3. Create a new issue with:
   - Your Python version
   - Your TrueNAS version
   - The exact error message
   - Output from `python tests/simple_test.py`
