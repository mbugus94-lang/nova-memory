"""
GETTING STARTED with Nova Memory 2.0 Advanced Features
======================================================

This quick start guide covers the essential steps to use all advanced features.
Expected time: 5-10 minutes
"""

# ==============================================================================
# STEP 1: Installation
# ==============================================================================

"""
Quick Start Installation:

Option A - Basic (SQLite only):
    pip install -e .

Option B - With Caching (Redis):
    pip install -e ".[cache]"

Option C - With ML Features (Semantic Search):
    pip install -e ".[ml]"

Option D - With Security (JWT, Encryption):
    pip install -e ".[security]"

Option E - Everything (Recommended):
    pip install -e ".[all]"

Option F - Development (Code + Testing):
    pip install -e ".[all,dev]"
"""

# ==============================================================================
# STEP 2: Start Required Services
# ==============================================================================

"""
If you installed Redis support, start Redis:

    On Windows (with WSL):
        wsl redis-server

    On Linux/Mac:
        redis-server

    Or with Docker:
        docker run -d -p 6379:6379 redis:7-alpine

For testing without Redis:
    The system gracefully falls back to no caching
"""

# ==============================================================================
# STEP 3: Initialize the System
# ==============================================================================

from core.advanced_features import init_nova_memory_advanced, get_nova_memory_advanced

# Initialize all advanced systems
system = init_nova_memory_advanced()

# Check health
health = system.health_check()
print("System Health:", health)

# Get statistics
stats = system.get_system_stats()
print("System Stats:", stats)


# ==============================================================================
# STEP 4: Use Individual Features
# ==============================================================================

# --- FEATURE 1: Redis Caching ---
print("\n1️⃣ CACHING")
cache = system.cache

# Set a value (with 1 hour TTL)
cache.set("my_key", {"data": "value"}, ttl=3600)

# Get the value
value = cache.get("my_key")
print(f"  Cached value: {value}")

# Get stats
stats = cache.get_stats()
print(f"  Cache stats: {stats}")


# --- FEATURE 2: Semantic Search ---
print("\n2️⃣ SEMANTIC SEARCH")
search = system.semantic_search

memories = [
    {"id": "1", "content": "The weather is sunny"},
    {"id": "2", "content": "It's raining today"},
    {"id": "3", "content": "Blue sky visible"},
]

results = search.semantic_search(
    query="What's the weather?",
    memories=memories,
    top_k=2
)
print(f"  Found {len(results)} similar memories")
for r in results:
    print(f"    - {r['content']} (score: {r['score']:.2f})")


# --- FEATURE 3: Agent Messaging ---
print("\n3️⃣ AGENT MESSAGING")
from core.agent_messaging import send_message, get_message_broker

broker = get_message_broker()

# Register agents
broker.register_agent("agent_001")
broker.register_agent("agent_002")

# Send a message
send_message(
    sender="agent_001",
    recipient="agent_002",
    subject="task:process",
    content={"data": [1, 2, 3]},
    priority="high"
)

# Check inbox
inbox = broker.receive_all("agent_002")
print(f"  Agent 002 has {len(inbox)} messages")


# --- FEATURE 4: JWT Authentication ---
print("\n4️⃣ AUTHENTICATION (JWT)")
jwt = system.jwt_manager

# Create a token for an agent
token = jwt.create_token(
    agent_id="agent_001",
    role="admin",
    claims={"team": "engineering"}
)
print(f"  Token created: {token[:20]}...")

# Verify the token
verified = jwt.verify_token(token)
print(f"  Token verified: {verified['agent_id']} (role: {verified['role']})")

# Check permissions
has_permission = jwt.has_permission(token, "create_memory")
print(f"  Has 'create_memory' permission: {has_permission}")


# --- FEATURE 5: Memory Encryption ---
print("\n5️⃣ ENCRYPTION")
encryption = system.encryption

# Encrypt sensitive data
encrypted = encryption.encrypt("password123")
print(f"  Encrypted: {encrypted[:30]}...")

# Decrypt
decrypted = encryption.decrypt(encrypted)
print(f"  Decrypted: {decrypted}")


# --- FEATURE 6: Agent Registry ---
print("\n6️⃣ AGENT REGISTRY")
registry = system.registry

# Register an agent with capabilities
registry.register(
    agent_id="analyzer_001",
    name="Data Analyzer",
    capabilities=["analyze", "visualize", "report"],
    tags=["ml", "analytics"],
    metadata={"team": "data-science"}
)

# Find agents by capability
analyzers = registry.find_by_capability("analyze")
print(f"  Found {len(analyzers)} analyzer agents")

# Find agents by tag
ml_agents = registry.find_by_tag("ml")
print(f"  Found {len(ml_agents)} ML agents")

# Search with advanced criteria
results = registry.search(
    query="analyzer",
    capability="analyze",
    status="online"
)
print(f"  Search found {len(results)} agents")


# --- FEATURE 7: Garbage Collection ---
print("\n7️⃣ GARBAGE COLLECTION")
from core.memory_management import MemoryGarbageCollector, RetentionPolicy

gc = MemoryGarbageCollector(
    policy=RetentionPolicy(
        delete_after_days=90,
        archive_after_days=30,
        min_access_count=2
    )
)

# Analyze memory for cleanup
memories = [
    {"id": "1", "content": "old", "last_accessed": 120, "access_count": 1},
    {"id": "2", "content": "new", "last_accessed": 5, "access_count": 10},
]

for mem in memories:
    recommendation = gc.analyze_memory(mem)
    print(f"  Memory {mem['id']}: {recommendation['action']}")


# --- FEATURE 8: Conflict Resolution ---
print("\n8️⃣ CONFLICT RESOLUTION")
from core.memory_management import ConflictResolver

resolver = ConflictResolver()

# Two conflicting updates (same memory, different content)
current = {"id": "1", "content": "version A", "updated": 100}
incoming = {"id": "1", "content": "version B", "updated": 200}

# Last-write-wins strategy
resolved = resolver.resolve_last_write_wins(current, incoming)
print(f"  LWW Result: {resolved['content']}")

# Merge strategy
merged = resolver.resolve_merge(current, incoming)
print(f"  Merge Result: {merged}")


# ==============================================================================
# STEP 5: Use the REST API
# ==============================================================================

"""
Start the API server:

    python -m uvicorn api.integration:app --reload

Then use these endpoints:

Advanced Features:
    GET  /api/v2/cache/stats
    DELETE /api/v2/cache/clear
    POST /api/v2/search/semantic
    POST /api/v2/search/cluster
    POST /api/v2/messaging/send
    GET  /api/v2/messaging/inbox/{agent_id}
    POST /api/v2/agents/register
    GET  /api/v2/agents/search
    POST /api/v2/auth/token
    GET  /api/v2/audit/logs
    POST /api/v2/memory/garbage-collect

System:
    GET  /health
    GET  /stats
    GET  /api/v2/examples/cache-demo
    POST /api/v2/examples/semantic-search

GraphQL:
    POST /graphql
"""

# ==============================================================================
# STEP 6: Use GraphQL
# ==============================================================================

"""
Query examples for GraphQL endpoint (POST to /graphql):

Query memories:
    query {
        memories(limit: 10) {
            id
            content
            agent_id
            tags
        }
    }

Search semantically:
    query {
        searchSemantic(query: "weather", limit: 5) {
            id
            content
            score
        }
    }

Find agents:
    query {
        agents(status: "online") {
            id
            name
            capabilities
            tags
        }
    }

Get system stats:
    query {
        systemStats {
            timestamp
            total_memories
            total_agents
        }
    }

Create memory:
    mutation {
        createMemory(
            content: "New memory"
            agentId: "agent_001"
            tags: ["test"]
        ) {
            id
            created_at
        }
    }
"""

# ==============================================================================
# STEP 7: Configuration
# ==============================================================================

"""
Key environment variables in .env:

# Redis (Caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Database
DATABASE_URL=sqlite:///./nova_memory.db

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Semantic Search
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.5

# Messaging
MESSAGE_HISTORY_LIMIT=1000
MESSAGE_QUEUE_SIZE=10000

# Garbage Collection
GC_DELETE_AFTER_DAYS=90
GC_ARCHIVE_AFTER_DAYS=30
GC_MIN_ACCESS_COUNT=2

# Security
ENCRYPTION_KEY_FILE=.encryption_key
AUDIT_LOG_RETENTION_DAYS=365
"""

# ==============================================================================
# STEP 8: Run the Full Demo
# ==============================================================================

"""
To see all features in action, run:

    python advanced_demo.py

This will demonstrate:
- Redis caching operations
- Semantic memory search
- Agent-to-agent messaging
- JWT authentication
- Memory encryption
- Agent discovery and registry
- Garbage collection
"""

# ==============================================================================
# STEP 9: Common Tasks
# ==============================================================================

"""
1. Cache a memory for fast retrieval:
    system.cache.set(f"mem_{id}", memory_dict, ttl=3600)
    cached = system.cache.get(f"mem_{id}")

2. Find similar memories:
    results = system.semantic_search.semantic_search(
        query="find memories about weather",
        memories=all_memories,
        top_k=5
    )

3. Send message between agents:
    send_message(
        sender="agent_a",
        recipient="agent_b",
        subject="task",
        content=task_data
    )

4. Authenticate an agent:
    token = jwt.create_token(agent_id="a1", role="agent")
    verified = jwt.verify_token(token)

5. Encrypt sensitive data:
    encrypted = system.encryption.encrypt(sensitive_data)
    decrypted = system.encryption.decrypt(encrypted)

6. Discover agents by capability:
    analyzers = registry.find_by_capability("analyze")

7. Clean up old memories:
    stats = gc.collect_garbage(memories, delete_handler)

8. Resolve conflicts:
    resolved = resolver.resolve_last_write_wins(v1, v2)

9. Check system health:
    health = system.health_check()
    stats = system.get_system_stats()

10. Query with GraphQL:
    See Step 6 for GraphQL examples
"""

# ==============================================================================
# STEP 10: Troubleshooting
# ==============================================================================

"""
Common Issues:

Redis Connection Failed:
    → Start Redis: redis-server
    → Check: redis-cli ping (should return PONG)
    → System gracefully falls back to no caching

Models Not Downloading:
    → sentence-transformers auto-downloads on first use
    → Takes ~80MB disk space
    → Internet connection required on first run

JWT Operations Failing:
    → Ensure cryptography package is installed: pip install cryptography

Semantic Search Results Poor:
    → Adjust SIMILARITY_THRESHOLD in .env
    → Use more specific queries
    → Check embedding cache: system.semantic_search.get_cache_stats()

Message Delivery Issues:
    → Verify agents are registered: broker.register_agent(agent_id)
    → Check agent inbox: broker.receive_all(agent_id)
    → Monitor stats: broker.get_stats()
"""

# ==============================================================================
# NEXT STEPS
# ==============================================================================

"""
After learning the basics:

1. Read ADVANCED_FEATURES.md for detailed documentation
2. Check IMPLEMENTATION_SUMMARY.md for architecture overview
3. Integrate into your application (see api/integration.py)
4. Add your own agent discovery logic
5. Implement custom conflict resolution strategies
6. Monitor audit logs for compliance
7. Scale with PostgreSQL (see ADVANCED_FEATURES.md)
8. Deploy to production (Docker/Kubernetes)

Essential Documentation:
- QUICKSTART.md - Basic usage
- README.md - Project overview  
- ADVANCED_FEATURES.md - Deep dive
- IMPLEMENTATION_SUMMARY.md - Architecture
- setup.py - Installation options
- .env.example - Configuration

Support:
- Run: python advanced_demo.py (see it in action)
- Read: Docstrings in core/* (function documentation)
- Check: api/integration.py (example implementation)
"""

print("\n✅ Getting started guide complete!")
print("📚 Next: Read ADVANCED_FEATURES.md for detailed documentation")
print("🚀 Then: Run 'python advanced_demo.py' to see everything in action")
