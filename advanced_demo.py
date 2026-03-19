"""
Advanced Nova Memory 2.0 - Complete Feature Demonstration
Shows how to use all advanced features:
- Redis caching
- Semantic memory search
- Agent-to-agent messaging
- RBAC & JWT authentication
- Memory encryption
- Agent registry
- Garbage collection
- Conflict resolution
"""

from datetime import datetime

# Core imports

# Advanced feature imports
from core.redis_cache import init_redis_cache
from core.semantic_search import init_semantic_search
from core.agent_messaging import (
    get_message_broker, create_message, broadcast_event, MessageType
)
from core.security import (
    get_jwt_manager, get_encryption_manager, Role, Permission
)
from core.agent_registry import get_agent_registry, AgentMetadata
from core.memory_management import (
    MemoryGarbageCollector, ConflictResolver, RetentionPolicy
)


def demo_redis_caching():
    """Demonstrate Redis caching layer"""
    print("\n" + "="*70)
    print("DEMO 1: Redis Caching Layer")
    print("="*70)

    # Initialize Redis cache
    cache = init_redis_cache(host="localhost", port=6379)

    # Set a value with TTL
    cache.set("user:john:preferences", {"theme": "dark", "lang": "en"}, ttl=3600)
    print("✓ Cached user preferences with 1 hour TTL")

    # Retrieve cached value
    cached = cache.get("user:john:preferences")
    print(f"✓ Retrieved from cache: {cached}")

    # Batch operations
    batch_data = {
        "memory:001": {"content": "Important fact 1"},
        "memory:002": {"content": "Important fact 2"},
        "memory:003": {"content": "Important fact 3"},
    }
    cache.mset(batch_data, ttl=1800)
    print("✓ Cached 3 memories with batch operation")

    # Get cache stats
    stats = cache.get_stats()
    print(f"✓ Cache stats: {stats}")


def demo_semantic_search():
    """Demonstrate semantic memory search"""
    print("\n" + "="*70)
    print("DEMO 2: Semantic Memory Search")
    print("="*70)

    # Initialize semantic search
    search = init_semantic_search()

    if not search.enabled:
        print("⚠ Semantic search disabled - install sentence-transformers")
        return

    # Example memories
    memories = [
        {
            "id": "m1",
            "content": "The weather today is sunny and warm",
            "created_at": datetime.now().isoformat(),
        },
        {
            "id": "m2",
            "content": "It is raining heavily with thunderstorms",
            "created_at": datetime.now().isoformat(),
        },
        {
            "id": "m3",
            "content": "Python is a programming language",
            "created_at": datetime.now().isoformat(),
        },
        {
            "id": "m4",
            "content": "Java is also a programming language",
            "created_at": datetime.now().isoformat(),
        },
    ]

    # Semantic search
    results = search.semantic_search(
        query="What is the weather like?",
        memories=memories,
        top_k=2,
    )

    print("✓ Semantic search for 'What is the weather like?'")
    for memory, score in results:
        print(f"  - {memory['content'][:50]}... (score: {score:.3f})")

    # Cluster memories
    clusters = search.cluster_memories(memories, num_clusters=2)
    print(f"✓ Clustered {len(memories)} memories into {len(clusters)} clusters")


def demo_agent_messaging():
    """Demonstrate agent-to-agent messaging"""
    print("\n" + "="*70)
    print("DEMO 3: Agent-to-Agent Messaging")
    print("="*70)

    broker = get_message_broker()

    # Register agents
    broker.register_agent("agent_001")
    broker.register_agent("agent_002")
    broker.register_agent("agent_003")
    print("✓ Registered 3 agents")

    # Agent 001 sends message to Agent 002
    msg1 = create_message(
        sender="agent_001",
        recipient="agent_002",
        subject="task:analyze",
        content={"data": "sample data to analyze"},
        message_type=MessageType.REQUEST,
    )
    broker.publish(msg1)
    print("✓ Agent 001 sent task request to Agent 002")

    # Agent 002 receives message
    msg = broker.receive("agent_002", timeout=0.1)
    if msg:
        print(f"✓ Agent 002 received: {msg.subject}")

    # Broadcast event to multiple agents
    broker.subscribe("agent_002", "important_events")
    broker.subscribe("agent_003", "important_events")

    count = broadcast_event(
        sender="agent_001",
        topic="important_events",
        event_type="memory_update",
        data={"updated_memories": 5},
    )
    print(f"✓ Broadcast event to {count} agents")

    # Show broker stats
    stats = broker.get_stats()
    print(f"✓ Broker stats: {len(stats['inbox_sizes'])} agents, "
          f"{stats['history_size']} messages in history")


def demo_jwt_authentication():
    """Demonstrate JWT authentication and RBAC"""
    print("\n" + "="*70)
    print("DEMO 4: JWT Authentication & RBAC")
    print("="*70)

    jwt_mgr = get_jwt_manager()
    if not jwt_mgr.available:
        print("⚠ JWT not available - install PyJWT")
        return

    # Create token for agent with MANAGER role
    token = jwt_mgr.create_token(
        agent_id="agent_admin_001",
        role=Role.MANAGER,
    )
    print("✓ Generated token for MANAGER role")

    # Verify token
    payload = jwt_mgr.verify_token(token)
    if payload:
        print(f"✓ Token verified: agent_id={payload['agent_id']}, "
              f"role={payload['role']}")

    # Check permissions
    has_perm = jwt_mgr.has_permission(
        token,
        Permission.DELETE_MEMORY,
    )
    print(f"✓ MANAGER role has DELETE_MEMORY permission: {has_perm}")

    # Create VIEWER token (no delete permission)
    viewer_token = jwt_mgr.create_token(
        agent_id="viewer_001",
        role=Role.VIEWER,
    )

    has_delete_perm = jwt_mgr.has_permission(viewer_token, Permission.DELETE_MEMORY)
    print(f"✓ VIEWER role has DELETE_MEMORY permission: {has_delete_perm}")


def demo_memory_encryption():
    """Demonstrate memory encryption"""
    print("\n" + "="*70)
    print("DEMO 5: Memory Encryption")
    print("="*70)

    encryption = get_encryption_manager()
    if not encryption.available:
        print("⚠ Encryption not available - install cryptography")
        return

    # Encrypt sensitive memory
    sensitive_data = "This is confidential information"
    encrypted = encryption.encrypt(sensitive_data)
    print(f"✓ Encrypted: {sensitive_data[:30]}...")
    print(f"  → {encrypted[:50]}...")

    # Decrypt
    decrypted = encryption.decrypt(encrypted)
    print(f"✓ Decrypted: {decrypted}")

    if decrypted == sensitive_data:
        print("✓ Encryption/decryption verified")


def demo_agent_registry():
    """Demonstrate agent registry and discovery"""
    print("\n" + "="*70)
    print("DEMO 6: Agent Registry & Discovery")
    print("="*70)

    registry = get_agent_registry()

    # Register agents
    agents_data = [
        {
            "agent_id": "analyzer_001",
            "name": "Data Analyzer",
            "version": "1.0.0",
            "capabilities": ["analyze", "summarize", "report"],
            "tags": ["data", "ml"],
        },
        {
            "agent_id": "messenger_001",
            "name": "Message Router",
            "version": "1.0.0",
            "capabilities": ["route", "deliver", "track"],
            "tags": ["messaging", "routing"],
        },
        {
            "agent_id": "learner_001",
            "name": "Learning Agent",
            "version": "1.5.0",
            "capabilities": ["learn", "train", "improve"],
            "tags": ["ml", "learning"],
        },
    ]

    for agent_data in agents_data:
        metadata = AgentMetadata(**agent_data)
        registry.register(metadata)

    print(f"✓ Registered {len(agents_data)} agents")

    # Search by capability
    analyzers = registry.find_by_capability("analyze")
    print(f"✓ Found {len(analyzers)} agents with 'analyze' capability")

    # Search by tag
    ml_agents = registry.find_by_tag("ml")
    print(f"✓ Found {len(ml_agents)} ML agents")

    # Advanced search
    results = registry.search(
        query="Agent",
        capability="learn",
    )
    print(f"✓ Found {len(results)} agents matching criteria")

    # Registry stats
    stats = registry.get_stats()
    print(f"✓ Registry stats: {stats['total_agents']} agents, "
          f"{stats['total_capabilities']} capabilities")


def demo_garbage_collection():
    """Demonstrate memory garbage collection"""
    print("\n" + "="*70)
    print("DEMO 7: Memory Garbage Collection")
    print("="*70)

    # Setup retention policy
    policy = RetentionPolicy(
        delete_after_days=730,      # Delete after 2 years
        archive_after_days=180,     # Archive after 6 months
        min_access_count=2,         # Minimum accesses to keep
    )

    gc = MemoryGarbageCollector(policy)

    # Example memories to analyze
    old_memory = {
        "id": "old_001",
        "content": "Very old memory",
        "created_at": "2022-01-01T00:00:00",
        "access_count": 0,
    }

    new_memory = {
        "id": "new_001",
        "content": "Recent memory",
        "created_at": datetime.now().isoformat(),
        "access_count": 10,
    }

    # Analyze memories
    old_analysis = gc.analyze_memory(old_memory)
    print(f"✓ Old memory analysis: {old_analysis['recommendation']}")
    if old_analysis.get('reasons'):
        for reason in old_analysis['reasons']:
            print(f"  - {reason}")

    new_analysis = gc.analyze_memory(new_memory)
    print(f"✓ New memory analysis: {new_analysis['recommendation']}")


def demo_conflict_resolution():
    """Demonstrate conflict resolution for concurrent updates"""
    print("\n" + "="*70)
    print("DEMO 8: Conflict Resolution")
    print("="*70)

    resolver = ConflictResolver()

    # Two conflicting versions of the same memory
    version1 = {
        "id": "mem_001",
        "content": "Updated content version A",
        "tags": ["v1", "test"],
        "updated_at": "2024-03-10T10:00:00",
        "access_count": 5,
    }

    version2 = {
        "id": "mem_001",
        "content": "Updated content version B",
        "tags": ["v2", "production"],
        "updated_at": "2024-03-10T11:00:00",
        "access_count": 3,
    }

    # Last-write-wins
    lww_result = resolver.resolve_last_write_wins(version1, version2)
    print(f"✓ Last-write-wins: {lww_result['content']}")

    # Merge strategy
    merged = resolver.resolve_merge(version1, version2)
    print("✓ Merged strategy:")
    print(f"  - Tags: {merged['tags']}")
    print(f"  - Content: {merged['content'][:40]}...")

    # Detect conflict
    has_conflict = resolver.detect_conflict(version1, version2)
    print(f"✓ Conflict detected: {has_conflict}")


def main():
    """Run all demonstrations"""
    print("\n" + "="*70)
    print("NOVA MEMORY 2.0 - ADVANCED FEATURES DEMO")
    print("="*70)

    try:
        demo_redis_caching()
    except Exception as e:
        print(f"⚠ Redis caching demo: {e}")

    try:
        demo_semantic_search()
    except Exception as e:
        print(f"⚠ Semantic search demo: {e}")

    try:
        demo_agent_messaging()
    except Exception as e:
        print(f"⚠ Agent messaging demo: {e}")

    try:
        demo_jwt_authentication()
    except Exception as e:
        print(f"⚠ JWT auth demo: {e}")

    try:
        demo_memory_encryption()
    except Exception as e:
        print(f"⚠ Encryption demo: {e}")

    try:
        demo_agent_registry()
    except Exception as e:
        print(f"⚠ Agent registry demo: {e}")

    try:
        demo_garbage_collection()
    except Exception as e:
        print(f"⚠ Garbage collection demo: {e}")

    try:
        demo_conflict_resolution()
    except Exception as e:
        print(f"⚠ Conflict resolution demo: {e}")

    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. Start Redis: redis-server")
    print("2. Run API server: python -m api.server")
    print("3. Visit API docs: http://localhost:8000/docs")
    print("4. Install optional dependencies: pip install -e .[all]")
    print("\n")


if __name__ == "__main__":
    main()
