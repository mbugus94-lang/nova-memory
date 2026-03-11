@echo off
REM Master startup script for Nova Memory 2.0 with 3 coordinated agents
REM This script guides you through starting the entire system

echo.
echo ============================================================
echo NOVA MEMORY 2.0 - THREE-AGENT COORDINATED SYSTEM
echo ============================================================
echo.
echo This setup uses:
echo   * ONE central Redis server (for all 3 agents)
echo   * ONE central database (nova_memory_central.db)
echo   * THREE agents communicating via shared message broker
echo.

echo ============================================================
echo STEP 1: STARTING CENTRAL REDIS SERVER
echo ============================================================
echo.
echo Before starting agents, you MUST start the Redis server.
echo.
echo Open a NEW terminal and run:
echo   start_redis.bat
echo.
echo This terminal will show: "Ready to accept connections"
echo DO NOT CLOSE that terminal while agents are running.
echo.

pause

echo ============================================================
echo STEP 2: INSTALLING DEPENDENCIES
echo ============================================================
echo.

call pip install redis fastapi uvicorn pyjwt cryptography

if %errorlevel% neq 0 (
    echo ⚠ Installation failed. Please check the error above.
    pause
    exit /b 1
)

echo ✓ Dependencies installed
echo.

echo ============================================================
echo STEP 3: VERIFYING CENTRAL CONFIGURATION
echo ============================================================
echo.

if not exist .env.central (
    echo ⚠ Creating .env.central...
    copy .env.example .env.central >nul
)

echo ✓ Central configuration ready: .env.central
echo.

echo ============================================================
echo STEP 4: STARTING AGENTS (Open 3 new terminals)
echo ============================================================
echo.
echo Open THREE new terminal windows and run EXACTLY in this order:
echo.
echo  TERMINAL 1: start_agent_1.bat
echo  TERMINAL 2: start_agent_2.bat  (after 10 seconds)
echo  TERMINAL 3: start_agent_3.bat  (after another 10 seconds)
echo.
echo You will see:
echo   Agent 1: http://localhost:8001/docs
echo   Agent 2: http://localhost:8002/docs
echo   Agent 3: http://localhost:8003/docs
echo.

pause

echo.
echo ============================================================
echo SYSTEM STATUS
echo ============================================================
echo.
echo ✓ All components configured for 3-agent coordination:
echo.
echo   Shared Redis:       127.0.0.1:6379
echo   Shared Database:    nova_memory_central.db
echo   Agent 1:            http://localhost:8001
echo   Agent 2:            http://localhost:8002
echo   Agent 3:            http://localhost:8003
echo.
echo All agents share:
echo   ✓ Red is caching layer
echo   ✓ Database memory storage
echo   ✓ Message broker for communication
echo   ✓ Agent registry for discovery
echo   ✓ JWT token validation
echo   ✓ Encryption key
echo.
echo ============================================================
echo NEXT STEPS
echo ============================================================
echo.
echo 1. Click new terminal, run: start_redis.bat
echo 2. Wait for "Ready to accept connections"
echo 3. Click new terminal, run: start_agent_1.bat
echo 4. Wait 10 seconds, run: start_agent_2.bat
echo 5. Wait 10 seconds, run: start_agent_3.bat
echo 6. Test communication:
echo    curl http://localhost:8001/health
echo    curl http://localhost:8002/health
echo    curl http://localhost:8003/health
echo.

pause
