@echo off
REM Start Agent 2 of Nova Memory 2.0
REM Connects to CENTRAL Redis and DATABASE

echo.
echo ============================================================
echo STARTING AGENT 2 ^(Port 8002^)
echo ============================================================
echo.
echo Configuration:
echo   Agent ID:       agent_002
echo   Agent Name:     Agent-2
echo   API Port:       8002
echo   Redis:          127.0.0.1:6379
echo   Database:       nova_memory_central.db
echo.
echo Access at: http://localhost:8002/docs
echo.

REM Load central configuration
if exist .env.central (
    echo ✓ Loading central configuration from .env.central
) else (
    echo ⚠ Warning: .env.central not found
)

REM Set agent-specific environment variables
set AGENT_ID=agent_002
set AGENT_NAME=Agent-2
set API_PORT=8002

REM Start the agent
echo Starting Agent 2...
python api/integration.py

pause
