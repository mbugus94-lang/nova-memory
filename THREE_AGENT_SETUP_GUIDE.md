# NOVA MEMORY 2.0 - Three-Agent Coordinated System Setup Guide

**Goal**: Run 3 Nova Memory agents that share:
- ✅ One central Redis server
- ✅ One central database
- ✅ Coordinated messaging and discovery

---

## Quick Start (5 minutes)

### Prerequisites
- Python 3.9+
- Windows 10/11 Pro with admin access
- ~2 GB RAM free

### Step 1: Install Dependencies
```powershell
cd C:\Users\DAVID\nova-memory
pip install redis fastapi uvicorn pyjwt cryptography
```

**Expected**: All packages install successfully

### Step 2: Install Redis Server
**Option A: Windows (Recommended)**
```powershell
# Download: https://redis.io/download/redis-stack/redis-stack-server-windows
# Or use WSL:
wsl redis-server
```

**Option B: Docker**
```powershell
docker run -d -p 6379:6379 redis:7-alpine
```

### Step 3: Verify Central Configuration
```powershell
# Check configuration exists
Test-Path .env.central
```

Expected output: `True`

### Step 4: Start Redis Server (Terminal 1)
```powershell
redis-server
```

Expected output:
```
Ready to accept connections
```

**LEAVE THIS TERMINAL OPEN** while agents run.

### Step 5: Start Agent 1 (Terminal 2)
```powershell
.\start_agent_1.bat
```

Expected output:
```
✓ System initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Step 6: Start Agent 2 (Terminal 3 - after 10 seconds)
```powershell
.\start_agent_2.bat
```

Expected: Server running on port 8002

### Step 7: Start Agent 3 (Terminal 4 - after 10 seconds)
```powershell
.\start_agent_3.bat
```

Expected: Server running on port 8003

---

## Verify Setup is Working

### Check Each Agent is Running
```powershell
# Terminal 5 - PowerShell
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

Expected: All should return `{"status": "healthy"}`

### Check System Stats
```powershell
curl http://localhost:8001/stats
curl http://localhost:8002/stats
curl http://localhost:8003/stats
```

### Test Agent Messaging (Agent 1 to Agent 2)
```powershell
$body = @{
    sender = "agent_001"
    recipient = "agent_002"
    subject = "test_message"
    content = @{ greeting = "Hello from Agent 1" }
} | ConvertTo-Json

curl -X POST `
  -ContentType "application/json" `
  -Body $body `
  http://localhost:8001/api/v2/messaging/send
```

### Check Agent 2's Inbox
```powershell
curl http://localhost:8002/api/v2/messaging/inbox/agent_002
```

Expected: Message from agent_001 in the inbox

---

## Configuration Files

### Central Config (.env.central)
Located at: `C:\Users\DAVID\nova-memory\.env.central`

Key settings:
```
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
DATABASE_URL=sqlite:///./nova_memory_central.db
JWT_SECRET_KEY=nova-memory-shared-secret-key-2026-all-agents
```

All 3 agents use this configuration.

### Agent-Specific Settings

Each startup script sets:
```
Agent 1: AGENT_ID=agent_001, API_PORT=8001
Agent 2: AGENT_ID=agent_002, API_PORT=8002
Agent 3: AGENT_ID=agent_003, API_PORT=8003
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              CENTRAL REDIS SERVER                       │
│              (127.0.0.1:6379)                          │
│         - Caching all agents' memories                 │
│         - Message queue for agent communication        │
│         - Agent registry and heartbeats                │
└──────────────┬──────────────┬──────────────┬───────────┘
               │              │              │
       ┌───────▼─────┐ ┌──────▼──────┐ ┌────▼────────┐
       │   AGENT 1   │ │   AGENT 2   │ │   AGENT 3   │
       │ :8001       │ │ :8002       │ │ :8003       │
       └───────┬─────┘ └──────┬──────┘ └────┬────────┘
               │              │              │
               └──────────────┬──────────────┘
                              │
                    ┌─────────▼─────────┐
                    │CENTRAL DATABASE   │
                    │nova_memory_      │
                    │central.db        │
                    └───────────────────┘

All agents:
✓ Connect to same Redis (shared cache & messaging)
✓ Read/write to same database (shared memories)
✓ Share JWT secret (validate each other's tokens)
✓ Use same encryption key (decrypt shared data)
```

---

## Memory Usage

**Current System**: 8 GB RAM, ~1.3 GB available

**Expected Usage**:
- Redis: 100-200 MB
- Agent 1: 100-120 MB
- Agent 2: 100-120 MB
- Agent 3: 100-120 MB
- System: 300-400 MB
- **TOTAL**: ~700-900 MB ✅ **SAFE**

---

## Troubleshooting

### "Redis Connection Failed"
```
Error: Could not connect to Redis at 127.0.0.1:6379
```

**Solution**:
1. Verify Redis server is running: `redis-cli ping`
2. Should return: `PONG`
3. If not, start Redis: `redis-server`

### "Port 8001 Already In Use"
```
OSError: [WinError 10048] Only one usage of each socket address
```

**Solution**:
```powershell
# Find what's using the port
netstat -ano | findstr :8001

# Kill the process
taskkill /PID <PID> /F
```

### "Module Not Found: redis"
```
ModuleNotFoundError: No module named 'redis'
```

**Solution**:
```powershell
pip install redis --upgrade
```

### "JWT Token Invalid"
```
401 Unauthorized: Invalid token
```

**Solution**:
- Verify `.env.central` has same JWT_SECRET_KEY on all agents
- Restart agents if changed

### Database Locked
```
sqlite3.OperationalError: database is locked
```

**Solution**:
- This happens if 2+ agents write simultaneously
- Restart agents with stagger (5-10 sec between starts)

---

## Testing Agent Communication

### Register Agent 1 in Registry
```powershell
$agent = @{
    agent_id = "agent_001"
    name = "Agent One"
    version = "1.0"
    capabilities = @("analyze", "store", "query")
    tags = @("primary", "memory")
    metadata = @{ team = "engineering" }
} | ConvertTo-Json

curl -X POST `
  -ContentType "application/json" `
  -Body $agent `
  http://localhost:8001/api/v2/agents/register
```

### Find Agents with "analyze" Capability
```powershell
curl "http://localhost:8001/api/v2/agents/search?capability=analyze"
```

### Send Message from Agent 1 to Agent 2
```powershell
$msg = @{
    sender = "agent_001"
    recipient = "agent_002"
    subject = "task:analyze_data"
    content = @{ 
        data = @(1,2,3,4,5)
        priority = "high"
    }
} | ConvertTo-Json

curl -X POST `
  -ContentType "application/json" `
  -Body $msg `
  http://localhost:8001/api/v2/messaging/send
```

### Check Agent 2's Messages
```powershell
curl http://localhost:8002/api/v2/messaging/inbox/agent_002
```

---

## Stopping the System

### Graceful Shutdown
1. Close each agent terminal (Ctrl+C)
2. Close Redis terminal (Ctrl+C)
3. All data is persisted in `nova_memory_central.db`

### Restart
Simply run the startup scripts again in the same order.

---

## Next Steps

### Monitor Agents
```powershell
# Check health continuously
while ($true) {
    Write-Host "Agent 1: $(curl http://localhost:8001/health)" 
    Write-Host "Agent 2: $(curl http://localhost:8002/health)"
    Write-Host "Agent 3: $(curl http://localhost:8003/health)"
    Start-Sleep -Seconds 5
}
```

### Scale to PostgreSQL
For production, migrate from SQLite to PostgreSQL:
```
1. Install PostgreSQL
2. Update .env.central:
   DATABASE_URL=postgresql://user:pass@localhost:5432/nova_memory
3. Restart agents
```

### Add More Features
```powershell
pip install sentence-transformers  # Semantic search
pip install scikit-learn            # Clustering
pip install graphene                # GraphQL
```

---

## Support

For issues, check:
- `nova_memory.log` for error details
- `/health` endpoint on each agent
- `test_system.py` to verify core modules

All features documented in: `ADVANCED_FEATURES.md`

---

**Created**: March 11, 2026  
**Nova Memory Version**: 2.0.0  
**Setup Type**: Three-Agent Coordinated System  
**Status**: ✅ Ready for Deployment  
