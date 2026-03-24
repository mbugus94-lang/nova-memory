# Nova Memory 2.1 - AI Agent Memory Management

<p align="center">
  <strong>Centralized memory storage for multi-agent AI deployments</strong><br>
  <em>Shared key-value store with SQLite persistence and optional Redis cache</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.1.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-Other-yellow" alt="License">
  <img src="[[Image 1: unavailable (https://img.shields.io/github/actions/workflow/status/mbugus94-lang/nova-memory/ci.yml)]]" alt="CI Status">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
</p>

---

Centralized memory storage for OpenClaw multi-agent deployments.

## ✨ What It Does

- **Shared Key-Value Memory Store** - Agents can share data seamlessly
- **SQLite Persistence** - Data survives restarts
- **Optional Redis Cache** - For high-performance deployments
- **Lightweight Defaults** - Fits low-resource machines out of the box
- **OpenClaw Skill Integration** - Via `/api/v2/memory/*` endpoints

---

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/mbugus94-lang/nova-memory.git
cd nova-memory
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the environment variables file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

---

## 🏢 Nova Memory v2.1 (Enhanced Central Server)

For robust multi-agent deployments, run the central server which supports:
- **Enhanced Storage:** Compression, Versioning, Access Tracking.
- **Auto-Capture:** Automatically save chat interactions.
- **Swift Context:** Get consolidated context for LLMs.
- **Collaboration:** Shared spaces and memory sharing.
- **Security:** JWT Authentication.

### Start Central Server
```bash
start_central_server.bat
# or
python -m api.server
```

### New Endpoints (v2.1)
- `POST /memories/context` (Swift Retrieval)
- `POST /interactions?auto_capture=true`
- `POST /collaboration/spaces`
- `POST /auth/login`

---

## 🔍 Health Checks

The API includes a health check endpoint for monitoring:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "timestamp": "2025-01-15T10:30:00Z",
  "uptime_seconds": 3600,
  "version": "2.1.0"
}
```

---

## ⚡ Quick Start (Legacy / Agent-Specific)

1. Install dependencies:
```bash
python -m pip install -r requirements.txt
```

2. Start an agent API (Agent 1 on port 8001):
```bash
python launch_agents.py --agent 1
```

3. Verify:
```bash
curl http://localhost:8001/health
curl http://localhost:8001/api/v2/memory/list
```

---

## ⚙️ Low Resource Defaults

By default, `.env.central` disables heavy features:
- `NOVA_CACHE_ENABLED=false`
- `NOVA_ENABLE_SEMANTIC_SEARCH=false`
- `NOVA_ENABLE_ENCRYPTION=false`

Enable any feature by setting it to `true` in `.env.central`.

---

## 🔗 OpenClaw Integration

Each OpenClaw agent should use the Nova Memory skill and point to its local API port:

- Agent 1: `http://localhost:8001`
- Agent 2: `http://localhost:8002`
- Agent 3: `http://localhost:8003`

Update the skill config at:
```
C:\Users\DAVID\clawd\skills\nova-memory\nova-memory.config.json
C:\Users\DAVID\openclaw-beta\skills\nova-memory\nova-memory.config.json
C:\Users\DAVID\openclaw-gamma\skills\nova-memory\nova-memory.config.json
```

---

## 📚 API Endpoints (OpenClaw Skill)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/memory/store` | POST | Store a memory |
| `/api/v2/memory/retrieve/{key}` | GET | Retrieve a memory by key |
| `/api/v2/memory/search` | POST | Search memories |
| `/api/v2/memory/list` | GET | List all memories |
| `/api/v2/memory/delete/{key}` | DELETE | Delete a memory |

---

## 📁 Config Files

- `.env.central` - Shared config for all agents
- `.env.example` - Environment template
- `nova-memory.config.json` - OpenClaw skill config

---

## 🐛 Troubleshooting

### Common Issues

**Python version errors:**
```bash
# Check Python version (requires 3.10+)
python --version
```

**Module not found errors:**
```bash
# Ensure you're in the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Port already in use:**
```bash
# Kill existing Python processes or change port in .env
lsof -ti:8000 | xargs kill -9  # macOS/Linux
taskkill /F /IM python.exe     # Windows
```

**Database locked:**
```bash
# Stop all agents and central server, then restart
pkill -f python
```

**Redis connection errors (if using cache):**
- Ensure Redis is running: `redis-server`
- Or set `NOVA_CACHE_ENABLED=false` in `.env.central`

---

## 📝 Notes

If you want all agents to share one database file, keep:
```
NOVA_MEMORY_DB_PATH=C:\Users\DAVID\.openclaw\memory\nova_memory_central.db
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

See [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/mbugus94-lang">David Gakere</a>
</p>