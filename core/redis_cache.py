"""
Redis Caching Layer for Nova Memory
Provides fast in-memory caching for frequently accessed memories
"""

import json
import logging
from typing import Any, Optional, Dict, List
from datetime import timedelta
import hashlib

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-based caching layer for Nova Memory"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: int = 3600,  # 1 hour default
        enabled: bool = True,
    ):
        """
        Initialize Redis cache connection
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Optional Redis password
            default_ttl: Default time-to-live in seconds
            enabled: Whether caching is enabled
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.default_ttl = default_ttl
        self.client: Optional[redis.Redis] = None
        
        if not self.enabled:
            logger.warning("Redis caching disabled - install redis-py or ensure Redis is available")
            return
        
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            # Test connection
            self.client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache MISS: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache with optional TTL"""
        if not self.enabled or not self.client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            self.client.setex(
                key,
                ttl,
                json.dumps(value),
            )
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.enabled or not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries matching {pattern}")
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def flush_all(self) -> bool:
        """Flush entire cache"""
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.flushdb()
            logger.warning("Cache flushed")
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False
    
    def get_or_set(
        self,
        key: str,
        callback,
        ttl: Optional[int] = None,
    ) -> Any:
        """Get from cache or compute and cache if missing"""
        cached = self.get(key)
        if cached is not None:
            return cached
        
        value = callback()
        self.set(key, value, ttl)
        return value
    
    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values at once"""
        if not self.enabled or not self.client:
            return {}
        
        try:
            values = self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            return result
        except Exception as e:
            logger.error(f"Cache mget error: {e}")
            return {}
    
    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values at once"""
        if not self.enabled or not self.client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            pipe = self.client.pipeline()
            for key, value in mapping.items():
                pipe.setex(key, ttl, json.dumps(value))
            pipe.execute()
            logger.debug(f"Cache MSET: {len(mapping)} items")
            return True
        except Exception as e:
            logger.error(f"Cache mset error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled or not self.client:
            return {"enabled": False}
        
        try:
            info = self.client.info()
            return {
                "enabled": True,
                "used_memory": info.get("used_memory_human"),
                "keys": self.client.dbsize(),
                "clients": info.get("connected_clients"),
                "operations": info.get("total_commands_processed"),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": False, "error": str(e)}
    
    @staticmethod
    def make_key(prefix: str, *parts: str) -> str:
        """Create a cache key from parts"""
        key_parts = [prefix] + list(parts)
        return ":".join(str(p) for p in key_parts)
    
    @staticmethod
    def hash_key(value: str) -> str:
        """Create a hash of a value for use as cache key"""
        return hashlib.sha256(value.encode()).hexdigest()[:16]


# Singleton instance
_redis_cache: Optional[RedisCache] = None


def get_redis_cache() -> RedisCache:
    """Get or create Redis cache instance"""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache


def init_redis_cache(
    host: str = "localhost",
    port: int = 6379,
    **kwargs
) -> RedisCache:
    """Initialize global Redis cache instance"""
    global _redis_cache
    _redis_cache = RedisCache(host=host, port=port, **kwargs)
    return _redis_cache
