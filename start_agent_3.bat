@echo off
REM Start Agent 3 of Nova Memory 2.0
REM Connects to CENTRAL Redis and DATABASE

echo.
echo ============================================================
echo STARTING AGENT 3 ^(Port 8003^)
echo ============================================================
echo.
echo Configuration:
echo   Agent ID:       agent_003
echo   Agent Name:     Agent-3
echo   API Port:       8003
echo   Redis:          127.0.0.1:6379
echo   Database:       nova_memory_central.db
echo.
echo Access at: http://localhost:8003/docs
echo.

REM Load central configuration
if exist .env.central (
    echo ✓ Loading central configuration from .env.central
) else (
    echo ⚠ Warning: .env.central not found
)

REM Set agent-specific environment variables
set AGENT_ID=agent_003
set AGENT_NAME=Agent-3
set API_PORT=8003

REM Start the agent
echo Starting Agent 3...
python api/integration.py

pause
