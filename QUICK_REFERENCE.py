"""
NOVA MEMORY 2.0 - QUICK REFERENCE CARD

Print or bookmark this file for quick API lookups
"""

# ==============================================================================
# FEATURE OVERVIEW
# ==============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                          QUICK REFERENCE CARD                               │
│                        Nova Memory 2.0 Advanced                              │
└─────────────────────────────────────────────────────────────────────────────┘

INITIALIZATION:
    from core.advanced_features import init_nova_memory_advanced
    system = init_nova_memory_advanced()

    # Or get existing instance:
    from core.advanced_features import get_nova_memory_advanced
    system = get_nova_memory_advanced()


KEY SYSTEMS:
    system.cache                 → Redis Caching
    system.semantic_search       → Semantic Memory Search
    system.message_broker        → Agent-to-Agent Messaging
    system.jwt_manager           → JWT Authentication
    system.encryption            → Memory Encryption
    system.audit_log             → Audit Logging
    system.attributes            → Attribute-based Access Control
    system.registry              → Agent Discovery & Registry
    system.gc                    → Garbage Collection
    system.resolver              → Conflict Resolution
    system.optimizer             → Memory Optimization
"""

# ==============================================================================
# 1. REDIS CACHING
# ==============================================================================

"""
from core.redis_cache import get_redis_cache

cache = get_redis_cache()

SET VALUES:
    cache.set(key, value)
    cache.set(key, value, ttl=3600)                          # 1 hour TTL
    cache.get_or_set(key, fetch_func)                        # Fetch if not cached

GET VALUES:
    value = cache.get(key)                                   # Single value
    values = cache.mget([key1, key2, key3])                  # Multiple values

DELETE VALUES:
    cache.delete(key)                                        # Single key
    cache.clear_pattern("prefix:*")                          # Pattern-based
    cache.flush_all()                                        # All values

STATS:
    stats = cache.get_stats()
    # Returns: {used_memory, keys, clients, connected_clients, operations}

REST API:
    GET  /api/v2/cache/stats
    DELETE /api/v2/cache/clear
"""

# ==============================================================================
# 2. SEMANTIC SEARCH
# ==============================================================================

"""
from core.semantic_search import get_semantic_search

search = get_semantic_search()

BASIC SEARCH:
    results = search.semantic_search(
        query="find weather info",
        memories=[{id, content, ...}, ...],
        top_k=5,                                              # Number of results
        threshold=0.5                                         # Min similarity
    )
    # Returns: [{id, content, score, match_type}, ...]

FIND SIMILAR:
    similar = search.find_similar_memories(
        memory=target_memory,
        memories=all_memories,
        top_k=10,
        threshold=0.7
    )

CLUSTERING:
    clusters = search.cluster_memories(
        memories=all_memories,
        n_clusters=5                                          # Number of groups
    )
    # Groups memories by semantic similarity

EMBEDDINGS:
    embedding = search.embed("text here")                     # Single text
    embeddings = search.embed_batch(texts_list)              # Multiple texts

REST API:
    POST /api/v2/search/semantic
    POST /api/v2/search/cluster
"""

# ==============================================================================
# 3. AGENT MESSAGING
# ==============================================================================

"""
from core.agent_messaging import (
    get_message_broker,
    send_message,
    broadcast_event,
    Message
)

broker = get_message_broker()

AGENT REGISTRATION:
    broker.register_agent("agent_001")                       # Register
    broker.unregister_agent("agent_001")                     # Unregister

SEND MESSAGE:
    send_message(
        sender="agent_001",
        recipient="agent_002",
        subject="task:analyze",
        content={"data": [1,2,3]},
        priority="high"                                       # high, normal, low
    )

RECEIVE MESSAGES:
    messages = broker.receive("agent_002")                   # Get next message
    all_msgs = broker.receive_all("agent_002")               # Get all messages

BROADCAST (Pub/Sub):
    broker.subscribe("agent_002", topic="events")
    broadcast_event(
        topic="events",
        event_type="memory_added",
        data={"memory_id": "123"}
    )

MESSAGE HANDLER (Request/Response):
    def handle_analysis(request):
        return {"result": "done"}

    broker.register_handler("agent_002", "analyze", handle_analysis)
    response = broker.handle_request("agent_002", "analyze", data)

MESSAGE TYPES:
    NOTIFICATION, REQUEST, RESPONSE, EVENT, COMMAND, STATUS

MESSAGE PRIORITY:
    CRITICAL (3), HIGH (2), NORMAL (1), LOW (0)

HISTORY & STATS:
    history = broker.get_history(agent_id, limit=100)
    stats = broker.get_stats()
    # {total_messages, agents_count, subscriptions, message_handlers}

REST API:
    POST /api/v2/messaging/send
    GET  /api/v2/messaging/inbox/{agent_id}
    POST /api/v2/messaging/broadcast
    POST /api/v2/messaging/subscribe
    GET  /api/v2/messaging/stats
"""

# ==============================================================================
# 4. JWT AUTHENTICATION & RBAC
# ==============================================================================

"""
from core.security import get_jwt_manager

jwt = get_jwt_manager()

TOKEN CREATION:
    token = jwt.create_token(
        agent_id="agent_001",
        role="admin",                    # admin, manager, agent, viewer
        claims={"team": "engineering"}
    )

TOKEN VERIFICATION:
    payload = jwt.verify_token(token)
    # Returns: {agent_id, role, permissions, exp, claims, ...}

PERMISSION CHECKING:
    can_create = jwt.has_permission(token, "create_memory")
    can_delete = jwt.has_permission(token, "delete_memory")

ROLES & PERMISSIONS:
    Roles:
        - admin   (all permissions)
        - manager (manage agents, create/update memories)
        - agent   (create/update own memories)
        - viewer  (read-only)

    Permissions:
        create_memory, read_memory, update_memory, delete_memory,
        manage_users, manage_agents, manage_roles, audit_logs,
        configure_system, access_api, etc.

REST API:
    POST /api/v2/auth/token
    GET  /api/v2/audit/logs
"""

# ==============================================================================
# 5. MEMORY ENCRYPTION
# ==============================================================================

"""
from core.security import get_encryption_manager

encryption = get_encryption_manager()

ENCRYPT:
    encrypted = encryption.encrypt("sensitive data")

DECRYPT:
    decrypted = encryption.decrypt(encrypted)

KEY MANAGEMENT:
    # Key is auto-generated and stored in .encryption_key
    # Back up this file for disaster recovery!
"""

# ==============================================================================
# 6. AGENT REGISTRY & DISCOVERY
# ==============================================================================

"""
from core.agent_registry import get_agent_registry

registry = get_agent_registry()

REGISTRATION:
    registry.register(
        agent_id="analyzer_001",
        name="Data Analyzer",
        version="1.0",
        description="Analyzes data",
        capabilities=["analyze", "report", "visualize"],
        tags=["ml", "analytics"],
        metadata={"team": "data-science"}
    )

UNREGISTER:
    registry.unregister("analyzer_001")

DISCOVERY:
    # By ID
    agent = registry.get_agent("analyzer_001")

    # By capability
    analyzers = registry.find_by_capability("analyze")

    # By tag
    ml_agents = registry.find_by_tag("ml")

SEARCH:
    results = registry.search(
        query="analyzer",
        capability="analyze",
        tag="ml",
        status="online",
        online_only=True
    )

HEALTH MONITORING:
    registry.heartbeat("agent_001")                          # Update last seen
    agent = registry.get_agent("agent_001")
    is_alive = agent.is_alive(timeout=300)                   # 5 min timeout

CAPABILITY MANAGEMENT:
    registry.add_capability("agent_001", "new_capability")
    registry.remove_capability("agent_001", "old_capability")

STATUS:
    registry.update_status("agent_001", "processing")

STATS:
    stats = registry.get_stats()
    # {total_agents, active_agents, online_agents, capabilities, tags}

REST API:
    POST /api/v2/agents/register
    GET  /api/v2/agents/search
    GET  /api/v2/agents/{agent_id}
    POST /api/v2/agents/{agent_id}/heartbeat
    GET  /api/v2/registry/stats
"""

# ==============================================================================
# 7. GARBAGE COLLECTION
# ==============================================================================

"""
from core.memory_management import MemoryGarbageCollector, RetentionPolicy

policy = RetentionPolicy(
    delete_after_days=90,                                    # Delete old memories
    archive_after_days=30,                                   # Archive medium-age
    min_access_count=2,                                      # Keep frequently accessed
    min_size_bytes=100                                       # Keep minimum size
)

gc = MemoryGarbageCollector(policy)

ANALYSIS:
    recommendation = gc.analyze_memory(memory)
    # Returns: {action: "keep|archive|delete", reason, score}

COLLECTION:
    def delete_handler(memory):
        # Custom delete logic
        pass

    def archive_handler(memory):
        # Custom archive logic
        pass

    stats = gc.collect_garbage(memories, delete_handler, archive_handler)
    # Returns: {total_analyzed, kept, archived, deleted, errors}

EXPORT:
    archived = gc.export_archived()

REST API:
    POST /api/v2/memory/garbage-collect
"""

# ==============================================================================
# 8. CONFLICT RESOLUTION
# ==============================================================================

"""
from core.memory_management import ConflictResolver

resolver = ConflictResolver()

DETECT CONFLICT:
    is_conflict = resolver.detect_conflict(memory_v1, memory_v2)

LAST-WRITE-WINS:
    resolved = resolver.resolve_last_write_wins(current, incoming)
    # Newer timestamp wins

MERGE:
    merged = resolver.resolve_merge(current, incoming)
    # Combines both versions intelligently

CUSTOM RESOLVER:
    def my_resolver(current, incoming):
        # Your custom logic
        return resolved_version

    result = resolver.resolve_custom(current, incoming, my_resolver)
"""

# ==============================================================================
# 9. ATTRIBUTE-BASED ACCESS CONTROL (ABAC)
# ==============================================================================

"""
from core.security import get_attribute_manager

attr = get_attribute_manager()

SET ATTRIBUTES:
    attr.set_attributes("agent_001", {
        "department": "engineering",
        "clearance": "secret",
        "team": "ai-systems"
    })

GET ATTRIBUTES:
    attrs = attr.get_attributes("agent_001")

CHECK ACCESS:
    has_access = attr.can_access(
        agent_id="agent_001",
        attribute="department",
        value="engineering"
    )
"""

# ==============================================================================
# 10. AUDIT LOGGING
# ==============================================================================

"""
from core.security import get_audit_log

audit = get_audit_log()

LOG ACTION:
    audit.log(
        actor="agent_001",
        action="create_memory",
        resource="memory_123",
        status="success",
        details={"tags": ["important"]}
    )

RETRIEVE LOGS:
    logs = audit.get_logs(
        actor="agent_001",
        action="create_memory",
        limit=100
    )

EXPORT:
    json_logs = audit.export()

REST API:
    GET /api/v2/audit/logs
"""

# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================

"""
CACHING:
    GET  /api/v2/cache/stats
    DELETE /api/v2/cache/clear

SEARCH:
    POST /api/v2/search/semantic
    POST /api/v2/search/cluster

MESSAGING:
    POST /api/v2/messaging/send
    GET  /api/v2/messaging/inbox/{agent_id}
    POST /api/v2/messaging/broadcast
    POST /api/v2/messaging/subscribe
    GET  /api/v2/messaging/stats

AGENT REGISTRY:
    POST /api/v2/agents/register
    GET  /api/v2/agents/search
    GET  /api/v2/agents/{agent_id}
    POST /api/v2/agents/{agent_id}/heartbeat
    GET  /api/v2/registry/stats

SECURITY:
    POST /api/v2/auth/token
    GET  /api/v2/audit/logs

MEMORY:
    POST /api/v2/memory/garbage-collect

SYSTEM:
    GET  /api/v2/health
    GET  /api/v2/stats

EXAMPLES:
    GET  /api/v2/examples/cache-demo
    POST /api/v2/examples/semantic-search
    GET  /api/v2/examples/agent-messaging
    GET  /api/v2/test/all-systems
"""

# ==============================================================================
# GraphQL QUERIES & MUTATIONS
# ==============================================================================

"""
QUERIES:
    memory(id: "123")
    memories(agent_id: "a1", tags: ["important"], limit: 10)
    searchSemantic(query: "weather", limit: 5)
    searchKeyword(query: "weather", limit: 5)
    agent(id: "a1")
    agents(status: "online", capability: "analyze")
    systemStats
    healthCheck

MUTATIONS:
    createMemory(content: "...", agentId: "a1", tags: ["t1"])
    updateMemory(id: "123", content: "...", tags: ["t1"])
    deleteMemory(id: "123", agentId: "a1")
"""

# ==============================================================================
# ENVIRONMENT VARIABLES
# ==============================================================================

"""
# .env configuration reference

# REDIS
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# DATABASE
DATABASE_URL=sqlite:///./nova_memory.db

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# SEMANTIC SEARCH
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.5
EMBEDDING_CACHE_SIZE=1000

# MESSAGING
MESSAGE_HISTORY_LIMIT=1000
MESSAGE_QUEUE_SIZE=10000
AGENT_HEARTBEAT_TIMEOUT=300

# GARBAGE COLLECTION
GC_DELETE_AFTER_DAYS=90
GC_ARCHIVE_AFTER_DAYS=30
GC_MIN_ACCESS_COUNT=2
GC_MIN_SIZE_BYTES=100

# SECURITY
ENCRYPTION_ALGORITHM=fernet
AUDIT_LOG_RETENTION_DAYS=365
ENABLE_RBAC=true

# LOGGING
LOG_LEVEL=info
LOG_FILE=nova_memory.log
"""

# ==============================================================================
# COMMON PATTERNS
# ==============================================================================

"""
PATTERN 1: Cache + Search
    # Cache memory
    system.cache.set(f"mem_{id}", memory)

    # Search all memories
    results = system.semantic_search.semantic_search(
        query="...",
        memories=all_memories
    )

PATTERN 2: Messaging + Registry
    # Find agents by capability
    agents = registry.find_by_capability("analyze")

    # Send to all
    for agent_id in [a.agent_id for a in agents]:
        send_message(sender="master", recipient=agent_id, ...)

PATTERN 3: Auth + Audit
    # Create token
    token = jwt.create_token(agent_id="a1", role="agent")

    # Log action
    audit.log(actor="a1", action="create_memory", status="success")

PATTERN 4: Encryption + Cache
    # Encrypt sensitive data
    encrypted = encryption.encrypt(sensitive_data)

    # Cache encrypted data
    system.cache.set("sensitive", encrypted)

PATTERN 5: Conflict Resolution
    # Detect conflict
    if resolver.detect_conflict(v1, v2):
        # Resolve it
        resolved = resolver.resolve_last_write_wins(v1, v2)
"""

# ==============================================================================
# TIPS & TRICKS
# ==============================================================================

"""
1. Always initialize system first:
    system = init_nova_memory_advanced()

2. Use TTL with cache for auto-cleanup:
    system.cache.set(key, value, ttl=3600)

3. Batch operations for performance:
    system.cache.mget([k1, k2, k3])
    system.semantic_search.embed_batch(texts)

4. Monitor system health:
    health = system.health_check()

5. Use semantic search for better results than keyword matching

6. Register agents before sending messages:
    broker.register_agent(agent_id)

7. Use heartbeat to keep agent alive:
    registry.heartbeat(agent_id)

8. Check audit logs for compliance:
    audit.get_logs(action="delete_memory")

9. Use roles instead of individual permissions:
    jwt.create_token(agent_id="a1", role="admin")

10. Set retention policies for automatic cleanup:
    policy = RetentionPolicy(delete_after_days=90)
"""

# ==============================================================================
# TROUBLESHOOTING
# ==============================================================================

"""
PROBLEM: Redis connection failed
SOLUTION: Start Redis (redis-server) or system falls back

PROBLEM: Semantic search not working
SOLUTION: pip install sentence-transformers scikit-learn

PROBLEM: JWT token verification failed
SOLUTION: Use same JWT_SECRET_KEY, check token expiration

PROBLEM: Message delivery slow
SOLUTION: Check broker stats, reduce message history size

PROBLEM: Memory growing too fast
SOLUTION: Enable garbage collection, set retention policy

PROBLEM: Search results not relevant
SOLUTION: Adjust SIMILARITY_THRESHOLD, use more specific queries

PROBLEM: Agent registry empty
SOLUTION: Call registry.register() for each agent first

For more help: Read ADVANCED_FEATURES.md
"""

print(__doc__)
