@echo off
REM Quick setup script for TrueNAS MCP Server on Windows

echo.
echo TrueNAS MCP Server - Quick Setup
echo ================================
echo.

REM Check Python
where python >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
) else (
    where python3 >nul 2>nul
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python3
    ) else (
        echo ERROR: Python not found. Please install Python 3.8 or higher.
        exit /b 1
    )
)

echo Found Python
echo.

REM Create virtual environment
echo Creating virtual environment...
%PYTHON_CMD% -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
pip install --upgrade pip setuptools wheel

REM Install core requirements
echo Installing core requirements...
pip install -r requirements.txt

REM Create .env if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Created .env file - please edit with your TrueNAS details
) else (
    echo .env already exists
)

echo.
echo Basic setup complete!
echo.
echo Next steps:
echo 1. Edit .env with your TrueNAS connection details
echo 2. Test connection: python tests\test_connection.py
echo 3. Run server: python truenas_mcp_server.py
echo.
echo For development dependencies (optional):
echo pip install pytest pytest-asyncio black flake8
echo.
pause
