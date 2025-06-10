@echo off
echo TrueNAS Core MCP Server Setup
echo =============================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Creating .env file from template...
if not exist .env (
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file with your TrueNAS connection details!
)

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your TrueNAS URL and API key
echo 2. Run 'test_connection.py' to verify connectivity
echo 3. Configure Claude Desktop with this MCP server
echo.
pause
