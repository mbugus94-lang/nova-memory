# Nova Memory - Demo Guide

Centralized memory storage for AI multi-agent deployments.

---

## 🎬 What is Nova Memory?

Nova Memory provides centralized, persistent memory storage for AI agent deployments:
- **Shared Key-Value Store** - Agents share data seamlessly
- **SQLite Persistence** - Data survives restarts
- **Redis Cache** - Optional high-performance caching
- **OpenClaw Integration** - Via `/api/v2/memory/*` endpoints

---

## 🚀 Quick Start Demo

### Installation

```bash
cd nova-memory
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
```

### Start the Central Server

```bash
# Using the startup script
python start_central_server.py

# Or directly
python -m api.server
```

The server starts on `http://localhost:8080`

---

## 📊 Basic Operations Demo

### Store a Memory

```python
import requests

# Store a memory
response = requests.post(
    'http://localhost:8080/memories',
    json={
        'key': 'user_preferences',
        'value': {'theme': 'dark', 'language': 'en'},
        'namespace': 'default'
    }
)
print(response.json())
```

**Response:**
```json
{
  "id": "mem_abc123",
  "key": "user_preferences",
  "value": {"theme": "dark", "language": "en"},
  "namespace": "default",
  "created_at": "2026-04-07T10:00:00Z"
}
```

### Retrieve a Memory

```python
# Get a specific memory
response = requests.get(
    'http://localhost:8080/memories/user_preferences',
    params={'namespace': 'default'}
)
print(response.json())
```

### Search Memories

```python
# Search by key pattern
response = requests.get(
    'http://localhost:8080/memories/search',
    params={
        'pattern': 'user_*',
        'namespace': 'default'
    }
)
print(response.json()['memories'])
```

---

## 🤖 Agent Integration Demo

### Agent 1: Stores Context

```python
# Agent 1 - Learning about user preferences
requests.post('http://localhost:8080/memories', json={
    'key': 'agent1_context',
    'value': {
        'conversation_topic': 'travel_planning',
        'user_interest': 'beach_destinations',
        'budget': 'medium'
    },
    'namespace': 'agents'
})
```

### Agent 2: Retrieves Context

```python
# Agent 2 - Gets shared context
response = requests.get(
    'http://localhost:8080/memories/agent1_context',
    params={'namespace': 'agents'}
)
context = response.json()['value']
# Uses context to provide personalized recommendations
```

---

## 🔄 Swift Context Demo

Get consolidated context for LLM prompts:

```python
# Get consolidated memory context
response = requests.post(
    'http://localhost:8080/memories/context',
    json={
        'query': 'What does the system know about the user?',
        'max_tokens': 1000,
        'namespace': 'default'
    }
)

context = response.json()['context']
print(context)
# "The user prefers dark theme, speaks English, and is 
#  interested in beach travel destinations with a medium budget..."
```

---

## 👥 Collaboration Spaces Demo

Create shared workspaces for agents:

```python
# Create a collaboration space
response = requests.post(
    'http://localhost:8080/collaboration/spaces',
    json={
        'name': 'project_alpha',
        'agents': ['agent_1', 'agent_2', 'agent_3'],
        'description': 'Shared space for Project Alpha team'
    }
)
space = response.json()

# Add shared memory to space
requests.post(
    f'http://localhost:8080/collaboration/spaces/{space["id"]}/memories',
    json={
        'key': 'task_queue',
        'value': ['design', 'implement', 'test']
    }
)
```

---

## 🔐 Authentication Demo

### Login

```python
# Get access token
response = requests.post(
    'http://localhost:8080/auth/login',
    json={
        'username': 'agent_1',
        'password': 'secure_password'
    }
)
token = response.json()['access_token']

# Use token in requests
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:8080/memories',
    headers=headers
)
```

---

## 📈 API Endpoints

### Memory Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/memories` | Store new memory |
| GET | `/memories/{key}` | Retrieve memory |
| PUT | `/memories/{key}` | Update memory |
| DELETE | `/memories/{key}` | Delete memory |
| GET | `/memories/search` | Search memories |
| POST | `/memories/context` | Swift context retrieval |

### Collaboration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/collaboration/spaces` | Create space |
| GET | `/collaboration/spaces` | List spaces |
| POST | `/spaces/{id}/memories` | Add memory to space |
| GET | `/spaces/{id}/memories` | Get space memories |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Get access token |
| POST | `/auth/refresh` | Refresh token |
| POST | `/auth/register` | Register new user |

---

## 🧪 Testing Demo

### Run All Tests

```bash
pytest

# With verbose output
pytest -v

# Specific test file
pytest tests/test_memory.py -v
```

### Manual API Testing

```bash
# Start server
python -m api.server &

# Health check
curl http://localhost:8080/health

# Store memory
curl -X POST http://localhost:8080/memories \
  -H "Content-Type: application/json" \
  -d '{"key": "test", "value": "hello"}'

# Retrieve memory
curl http://localhost:8080/memories/test
```

---

## 🐳 Docker Demo

### Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f nova_memory

# Stop services
docker-compose down
```

### Build Custom Image

```bash
docker build -t nova-memory:latest .
docker run -p 8080:8080 nova-memory:latest
```

---

## 📊 Performance Demo

### Benchmark Queries

```python
import time

# Test write speed
start = time.time()
for i in range(1000):
    requests.post('http://localhost:8080/memories', json={
        'key': f'bench_{i}',
        'value': {'data': 'x' * 1000}
    })
write_time = time.time() - start
print(f'1000 writes in {write_time:.2f}s')

# Test read speed
start = time.time()
for i in range(1000):
    requests.get(f'http://localhost:8080/memories/bench_{i}')
read_time = time.time() - start
print(f'1000 reads in {read_time:.2f}s')
```

---

## 🔧 Configuration

### Environment Variables

```env
# Server
PORT=8080
HOST=0.0.0.0
DEBUG=false

# Database
DATABASE_URL=sqlite:///./nova_memory.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/nova

# Redis (optional)
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true

# Security
JWT_SECRET=your-secret-key
JWT_EXPIRY=3600

# Logging
LOG_LEVEL=INFO
```

---

## 🏗️ Architecture

```
nova-memory/
├── api/
│   └── server.py        # FastAPI server
├── core/
│   ├── memory.py         # Memory store
│   ├── cache.py          # Redis cache
│   └── auth.py           # Authentication
├── agents/              # Agent implementations
├── tests/               # Test suite
└── docker-compose.yml   # Docker setup
```

---

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org)
- [Redis Docs](https://redis.io/documentation)

---

Built with ❤️ for AI developers | [View on GitHub](https://github.com/mbugus94-lang/nova-memory)
