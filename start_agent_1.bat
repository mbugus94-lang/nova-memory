@echo off
REM Start Agent 1 of Nova Memory 2.0
REM Connects to CENTRAL Redis and DATABASE

echo.
echo ============================================================
echo STARTING AGENT 1 ^(Port 8001^)
echo ============================================================
echo.
echo Configuration:
echo   Agent ID:       agent_001
echo   Agent Name:     Agent-1  
echo   API Port:       8001
echo   Redis:          127.0.0.1:6379
echo   Database:       nova_memory_central.db
echo.
echo Access at: http://localhost:8001/docs
echo.

REM Load central configuration
if exist .env.central (
    echo ✓ Loading central configuration from .env.central
) else (
    echo ⚠ Warning: .env.central not found
)

REM Set agent-specific environment variables
set AGENT_ID=agent_001
set AGENT_NAME=Agent-1
set API_PORT=8001

REM Start the agent
echo Starting Agent 1...
python api/integration.py

pause
