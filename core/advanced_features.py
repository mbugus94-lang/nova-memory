"""
Nova Memory 2.0 - Advanced Features Integration Module
Integrates all advanced features (Redis, Semantic Search, Messaging, Security)
"""

import logging
from typing import Dict, Any, Optional

from core.redis_cache import init_redis_cache
from core.semantic_search import init_semantic_search
from core.agent_messaging import get_message_broker
from core.security import (
    get_jwt_manager, get_encryption_manager, get_audit_log,
    get_attribute_manager
)
from core.agent_registry import get_agent_registry
from core.memory_management import (
    MemoryGarbageCollector, ConflictResolver, MemoryOptimizer
)

logger = logging.getLogger(__name__)


class NovaMemoryAdvanced:
    """
    Advanced Nova Memory system with all features integrated

    Features:
    - Redis caching for performance
    - Semantic search with embeddings
    - Agent-to-agent messaging
    - RBAC & JWT authentication
    - Memory encryption
    - Agent registry & discovery
    - Memory optimization & garbage collection
    """

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        cache_ttl: int = 3600,
        enable_cache: bool = True,
        enable_semantic_search: bool = True,
        enable_encryption: bool = True,
        enable_messaging: bool = True,
        semantic_model: Optional[str] = None,
    ):
        """Initialize advanced features"""
        self.cache = init_redis_cache(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            default_ttl=cache_ttl,
            enabled=enable_cache,
        )
        semantic_model = semantic_model or "sentence-transformers/all-MiniLM-L6-v2"
        self.semantic_search = (
            init_semantic_search(model_name=semantic_model)
            if enable_semantic_search
            else None
        )
        self.message_broker = get_message_broker() if enable_messaging else None
        self.jwt_manager = get_jwt_manager()
        self.encryption = get_encryption_manager() if enable_encryption else None
        self.audit_log = get_audit_log()
        self.attributes = get_attribute_manager()
        self.registry = get_agent_registry()
        self.gc = MemoryGarbageCollector()
        self.resolver = ConflictResolver()
        self.optimizer = MemoryOptimizer()

        logger.info("Nova Memory Advanced features initialized")

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            "cache": self.cache.get_stats() if self.cache else {"enabled": False},
            "semantic_search": (
                self.semantic_search.get_cache_stats() if self.semantic_search else None
            ),
            "registry": self.registry.get_stats(),
            "broker": self.message_broker.get_stats() if self.message_broker else None,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
        }

    def health_check(self) -> Dict[str, bool]:
        """Check health of all components"""
        return {
            "cache": self.cache.enabled if self.cache else False,
            "semantic_search": (
                self.semantic_search.enabled if self.semantic_search else False
            ),
            "messaging": self.message_broker is not None,
            "security": self.jwt_manager.available,
            "encryption": self.encryption.available if self.encryption else False,
            "registry": True,
        }


# Global instance
_advanced_system: Optional[NovaMemoryAdvanced] = None


def init_nova_memory_advanced(**kwargs) -> NovaMemoryAdvanced:
    """Initialize the advanced Nova Memory system"""
    global _advanced_system
    _advanced_system = NovaMemoryAdvanced(**kwargs)
    return _advanced_system


def get_nova_memory_advanced() -> NovaMemoryAdvanced:
    """Get the global advanced Nova Memory instance"""
    global _advanced_system
    if _advanced_system is None:
        _advanced_system = NovaMemoryAdvanced()
    return _advanced_system
