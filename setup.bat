@echo off
REM Nova Memory 2.0 - Quick Setup for Windows
REM This script automates the setup process on Windows systems

setlocal enabledelayexpansion
set SCRIPT_DIR=%~dp0

echo.
echo ==============================================================================
echo          NOVA MEMORY 2.0 - WINDOWS SETUP WIZARD
echo ==============================================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.9+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✓ Python detected
python --version

echo.
echo [1/5] Creating project directories...
if not exist "backups" mkdir backups
if not exist "logs" mkdir logs
echo ✓ Directories created

echo.
echo [2/5] Checking for .env file...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo ✓ Created .env from .env.example
        echo ⚠ Remember to update .env with your configuration
    ) else (
        echo ⚠ .env.example not found
    )
) else (
    echo ⚠ .env already exists, skipping...
)

echo.
echo [3/5] Installing core dependencies...
python -m pip install --upgrade pip
if "%1"=="--full" (
    echo Installing with all optional features...
    python -m pip install -e ".[all,dev]"
) else (
    python -m pip install -r requirements.txt
)
if errorlevel 1 (
    echo ✗ Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed

echo.
echo [4/5] Verifying installation...
python -c "import fastapi; import pydantic; print('✓ Core packages verified')" 2>nul
if errorlevel 1 (
    echo ⚠ Warning: Some packages may not be installed correctly
)

echo.
echo ============================================================================
echo                         SETUP COMPLETE!
echo ============================================================================
echo.
echo NEXT STEPS:
echo.
echo 1. UPDATE CONFIGURATION (if needed):
echo    - Edit .env with your settings
echo.
echo 2. START THE API SERVER:
echo    python -m api.server
echo    - API: http://localhost:8000
echo    - Docs: http://localhost:8000/docs
echo.
echo 3. RUN TESTS:
echo    python main.py
echo.
echo 4. VIEW DEMO SCENARIOS:
echo    python demo_scenarios.py
echo.
echo 5. INSTALL ADDITIONAL FEATURES:
echo    python -m pip install -e ".[ml]"           (ML capabilities)
echo    python -m pip install -e ".[blockchain]"   (Solana integration)
echo    python -m pip install -e ".[storage]"      (Advanced storage)
echo.
echo For more information, see README.md
echo ============================================================================
echo.
pause
