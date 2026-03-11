@echo off
REM Start Redis Server for Nova Memory 2.0
REM This is the CENTRAL Redis that all 3 agents will connect to

echo.
echo ============================================================
echo STARTING CENTRAL REDIS SERVER FOR NOVA MEMORY 2.0
echo ============================================================
echo.

REM Check if redis-server is available
where redis-server >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ Redis server not found. Please install Redis:
    echo   - Option 1: Download from https://redis.io/download
    echo   - Option 2: Use WSL: wsl redis-server
    echo   - Option 3: Use Docker: docker run -d -p 6379:6379 redis:7-alpine
    echo.
    pause
    exit /b 1
)

echo ✓ Redis server found
echo ✓ Starting Redis on port 6379...
echo   All agents will connect to: 127.0.0.1:6379
echo.

redis-server --port 6379

pause
