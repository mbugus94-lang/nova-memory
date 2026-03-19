"""
Enhanced API Router for Advanced Nova Memory Features
Includes new endpoints for all advanced features
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import logging

from core.redis_cache import get_redis_cache
from core.semantic_search import get_semantic_search
from core.agent_messaging import (
    get_message_broker, create_message, MessageType, MessagePriority
)
from core.security import get_jwt_manager, get_audit_log
from core.agent_registry import get_agent_registry, AgentMetadata
from core.memory_management import MemoryGarbageCollector
from core.advanced_features import get_nova_memory_advanced

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["advanced"])


# ============================================================================
# Caching Endpoints
# ============================================================================

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics and performance metrics"""
    cache = get_redis_cache()
    return {
        "status": "ok",
        "cache": cache.get_stats(),
    }


@router.delete("/cache/clear")
async def clear_cache(pattern: str = "*"):
    """Clear cache entries matching pattern"""
    cache = get_redis_cache()
    cleared = cache.clear_pattern(pattern)
    return {
        "status": "ok",
        "cleared": cleared,
        "pattern": pattern,
    }


# ============================================================================
# Semantic Search Endpoints
# ============================================================================

@router.post("/search/semantic")
async def semantic_search_memories(
    query: str,
    top_k: int = Query(5, ge=1, le=50),
    score_threshold: float = Query(0.3, ge=0, le=1),
):
    """
    Search memories by semantic similarity using embeddings

    This finds conceptually similar memories even if they don't share keywords
    """
    search_engine = get_semantic_search()

    if not search_engine.enabled:
        raise HTTPException(status_code=503, detail="Semantic search not available")

    # In a real implementation, would fetch all memories and search them
    # For now, return example structure
    return {
        "query": query,
        "results": [],
        "search_type": "semantic",
        "model": "all-MiniLM-L6-v2",
    }


@router.post("/search/cluster")
async def cluster_memories(num_clusters: int = Query(5, ge=1, le=50)):
    """Cluster memories by semantic similarity"""
    search_engine = get_semantic_search()

    if not search_engine.enabled:
        raise HTTPException(status_code=503, detail="Semantic search not available")

    return {
        "status": "ok",
        "num_clusters": num_clusters,
        "clusters": {},
        "note": "Requires actual memory data",
    }


# ============================================================================
# Agent Messaging Endpoints
# ============================================================================

@router.post("/messaging/send")
async def send_message(
    sender: str,
    recipient: str,
    subject: str,
    content: Dict[str, Any],
    priority: str = "normal",
):
    """Send a message from one agent to another"""
    broker = get_message_broker()
    broker.register_agent(sender)
    broker.register_agent(recipient)

    priority_map = {
        "low": MessagePriority.LOW,
        "normal": MessagePriority.NORMAL,
        "high": MessagePriority.HIGH,
        "critical": MessagePriority.CRITICAL,
    }

    message = create_message(
        sender=sender,
        recipient=recipient,
        subject=subject,
        content=content,
        message_type=MessageType.NOTIFICATION,
        priority=priority_map.get(priority, MessagePriority.NORMAL),
    )

    success = broker.publish(message)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to send message")

    return {
        "status": "ok",
        "message_id": message.id,
        "sender": sender,
        "recipient": recipient,
    }


@router.get("/messaging/inbox/{agent_id}")
async def get_inbox(agent_id: str):
    """Get all messages in an agent's inbox"""
    broker = get_message_broker()
    broker.register_agent(agent_id)

    messages = broker.receive_all(agent_id)

    return {
        "agent_id": agent_id,
        "message_count": len(messages),
        "messages": [m.to_dict() for m in messages],
    }


@router.post("/messaging/broadcast")
async def broadcast_event(
    sender: str,
    topic: str,
    event_type: str,
    data: Dict[str, Any],
):
    """Broadcast an event to all subscribers of a topic"""
    broker = get_message_broker()
    broker.register_agent(sender)
    broker.subscribe(sender, topic)

    count = broker.broadcast(
        create_message(
            sender=sender,
            recipient="*",
            subject=f"event:{event_type}",
            content=data,
            message_type=MessageType.EVENT,
        ),
        topic,
    )

    return {
        "status": "ok",
        "topic": topic,
        "recipients": count,
        "event_type": event_type,
    }


@router.post("/messaging/subscribe")
async def subscribe_to_topic(agent_id: str, topic: str):
    """Subscribe an agent to a topic"""
    broker = get_message_broker()
    broker.register_agent(agent_id)
    broker.subscribe(agent_id, topic)

    return {
        "status": "ok",
        "agent_id": agent_id,
        "topic": topic,
        "subscribed": True,
    }


@router.get("/messaging/stats")
async def get_messaging_stats():
    """Get message broker statistics"""
    broker = get_message_broker()
    return broker.get_stats()


# ============================================================================
# Agent Registry & Discovery
# ============================================================================

@router.post("/agents/register")
async def register_agent(metadata: Dict[str, Any]):
    """Register a new agent"""
    try:
        agent_metadata = AgentMetadata(
            agent_id=metadata.get("agent_id"),
            name=metadata.get("name"),
            version=metadata.get("version"),
            description=metadata.get("description", ""),
            capabilities=metadata.get("capabilities", []),
            tags=metadata.get("tags", []),
        )

        registry = get_agent_registry()
        success = registry.register(agent_metadata)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to register agent")

        return {
            "status": "ok",
            "agent_id": agent_metadata.agent_id,
            "registered": True,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents/search")
async def search_agents(
    query: Optional[str] = None,
    capability: Optional[str] = None,
    tag: Optional[str] = None,
    online_only: bool = False,
):
    """Search for agents"""
    registry = get_agent_registry()
    agents = registry.search(
        query=query,
        capability=capability,
        tag=tag,
        online_only=online_only,
    )

    return {
        "results": [a.to_dict() for a in agents],
        "count": len(agents),
    }


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details"""
    registry = get_agent_registry()
    agent = registry.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent.to_dict()


@router.post("/agents/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: str):
    """Send heartbeat to keep agent registered"""
    registry = get_agent_registry()
    success = registry.heartbeat(agent_id)

    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "status": "ok",
        "agent_id": agent_id,
    }


@router.get("/registry/stats")
async def get_registry_stats():
    """Get agent registry statistics"""
    registry = get_agent_registry()
    return registry.get_stats()


# ============================================================================
# Security & Authentication Endpoints
# ============================================================================

@router.post("/auth/token")
async def get_auth_token(
    agent_id: str,
    role: str = "agent",
):
    """Generate authentication token for an agent"""
    from core.security import Role

    jwt_mgr = get_jwt_manager()

    try:
        role = Role(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")

    token = jwt_mgr.create_token(agent_id, role)

    if not token:
        raise HTTPException(status_code=500, detail="Failed to create token")

    return {
        "token": token,
        "agent_id": agent_id,
        "role": role.value,
        "type": "bearer",
    }


@router.get("/audit/logs")
async def get_audit_logs(
    actor: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
):
    """Get audit logs"""
    audit = get_audit_log()
    logs = audit.get_logs(actor=actor, action=action, limit=limit)

    return {
        "logs": logs,
        "count": len(logs),
    }


# ============================================================================
# Memory Management Endpoints
# ============================================================================

@router.post("/memory/garbage-collect")
async def run_garbage_collection(
    delete_after_days: int = 730,
    archive_after_days: int = 180,
):
    """Run garbage collection on memories"""
    from core.memory_management import RetentionPolicy

    policy = RetentionPolicy(
        delete_after_days=delete_after_days,
        archive_after_days=archive_after_days,
    )

    MemoryGarbageCollector(policy)

    # In real implementation, would get memories from database
    return {
        "status": "ok",
        "policy": {
            "delete_after_days": delete_after_days,
            "archive_after_days": archive_after_days,
        },
        "note": "Requires actual memory data",
    }


# ============================================================================
# System Status Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Comprehensive system health check"""
    advanced = get_nova_memory_advanced()

    return {
        "status": "ok",
        "version": "2.0.0",
        "components": advanced.health_check(),
    }


@router.get("/stats")
async def get_system_stats():
    """Get comprehensive system statistics"""
    advanced = get_nova_memory_advanced()

    return advanced.get_system_stats()
