"""
Nova Memory Cloud - API Key Authentication & Usage Tracking

This module provides API key-based authentication and usage tracking
for the cloud version of Nova Memory.
"""

import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import sqlite3
import os


@dataclass
class APIKey:
    id: str
    key_hash: str
    name: str
    user_id: str
    tier: str = "free"
    monthly_requests: int = 0
    monthly_tokens: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class UsageRecord:
    id: int
    api_key_id: str
    endpoint: str
    method: str
    tokens_used: int
    latency_ms: int
    timestamp: datetime


class APIKeyManager:
    """Manages API keys for cloud customers"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "..", "data", "api_keys.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                key_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                tier TEXT DEFAULT 'free',
                monthly_requests INTEGER DEFAULT 0,
                monthly_tokens INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                latency_ms INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_key_limits (
                tier TEXT PRIMARY KEY,
                requests_per_minute INTEGER DEFAULT 60,
                requests_per_month INTEGER DEFAULT 10000,
                tokens_per_month INTEGER DEFAULT 100000,
                max_memories INTEGER DEFAULT 1000,
                features TEXT DEFAULT '[]'
            )
        """)
        
        for tier, limits in TIER_LIMITS.items():
            cursor.execute("""
                INSERT OR IGNORE INTO api_key_limits (tier, requests_per_minute, requests_per_month, tokens_per_month, max_memories, features)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tier, limits["rpm"], limits["monthly_requests"], limits["monthly_tokens"], limits["max_memories"], ",".join(limits["features"])))
        
        conn.commit()
        conn.close()
    
    def create_api_key(self, name: str, user_id: str, tier: str = "free") -> tuple[str, str]:
        """Create a new API key. Returns (key_id, raw_key)"""
        key_id = f"nm_{hashlib.sha256(f'{name}{time.time()}'.encode()).hexdigest()[:16]}"
        raw_key = f"nm_live_{hashlib-sha256(f'{key_id}{time.time()}'.encode()).hexdigest()[:48]}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO api_keys (id, key_hash, name, user_id, tier)
            VALUES (?, ?, ?, ?, ?)
        """, (key_id, key_hash, name, user_id, tier))
        conn.commit()
        conn.close()
        
        return key_id, raw_key
    
    def verify_api_key(self, raw_key: str) -> Optional[APIKey]:
        """Verify an API key and return the APIKey object if valid"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_keys WHERE key_hash = ? AND is_active = 1", (key_hash,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        if row["expires_at"]:
            expires = datetime.fromisoformat(row["expires_at"])
            if expires < datetime.utcnow():
                return None
        
        return APIKey(
            id=row["id"],
            key_hash=row["key_hash"],
            name=row["name"],
            user_id=row["user_id"],
            tier=row["tier"],
            monthly_requests=row["monthly_requests"],
            monthly_tokens=row["monthly_tokens"],
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoplot(row["expires_at"]) if row["expires_at"] else None,
            is_active=bool(row["is_active"])
        )
    
    def get_tier_limits(self, tier: str) -> Dict:
        """Get rate limits for a tier"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_key_limits WHERE tier = ?", (tier,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return TIER_LIMITS.get("free", TIER_LIMITS["free"])
        
        return {
            "rpm": row[1],
            "monthly_requests": row[2],
            "monthly_tokens": row[3],
            "max_memories": row[4],
            "features": row[5].split(",") if row[5] else []
        }
    
    def check_rate_limit(self, api_key: APIKey) -> tuple[bool, str]:
        """Check if API key is within rate limits"""
        limits = self.get_tier_limits(api_key.tier)
        
        if api_key.monthly_requests >= limits["monthly_requests"]:
            return False, "Monthly request limit exceeded"
        
        return True, "OK"
    
    def record_usage(self, api_key_id: str, endpoint: str, method: str, tokens: int = 0, latency_ms: int = 0):
        """Record API usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO usage_records (api_key_id, endpoint, method, tokens_used, latency_ms)
            VALUES (?, ?, ?, ?, ?)
        """, (api_key_id, endpoint, method, tokens, latency_ms))
        
        cursor.execute("""
            UPDATE api_keys 
            SET monthly_requests = monthly_requests + 1,
                monthly_tokens = monthly_tokens + ?
            WHERE id = ?
        """, (tokens, api_key_id))
        
        conn.commit()
        conn.close()
    
    def get_usage_stats(self, api_key_id: str, days: int = 30) -> Dict:
        """Get usage statistics for an API key"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_requests,
                SUM(tokens_used) as total_tokens,
                AVG(latency_ms) as avg_latency,
                COUNT(DISTINCT DATE(timestamp)) as active_days
            FROM usage_records
            WHERE api_key_id = ? AND timestamp >= datetime('now', '-{} days')
        """.format(days), (api_key_id,))
        
        row = cursor.fetchone()
        
        cursor.execute("""
            SELECT endpoint, COUNT(*) as count
            FROM usage_records
            WHERE api_key_id = ?
            GROUP BY endpoint
            ORDER BY count DESC
            LIMIT 10
        """, (api_key_id,))
        
        top_endpoints = cursor.fetchall()
        conn.close()
        
        return {
            "total_requests": row["total_requests"] or 0,
            "total_tokens": row["total_tokens"] or 0,
            "avg_latency_ms": row["avg_latency"] or 0,
            "active_days": row["active_days"] or 0,
            "top_endpoints": [{"endpoint": r["endpoint"], "count": r["count"]} for r in top_endpoints]
        }
    
    def list_api_keys(self, user_id: str) -> List[APIKey]:
        """List all API keys for a user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_keys WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [
            APIKey(
                id=row["id"],
                key_hash=row["key_hash"],
                name=row["name"],
                user_id=row["user_id"],
                tier=row["tier"],
                monthly_requests=row["monthly_requests"],
                monthly_tokens=row["monthly_tokens"],
                created_at=datetime.fromisoformat(row["created_at"]),
                expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
                is_active=bool(row["is_active"])
            )
            for row in rows
        ]
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success


TIER_LIMITS = {
    "free": {
        "name": "Free",
        "rpm": 60,
        "monthly_requests": 10000,
        "monthly_tokens": 100000,
        "max_memories": 1000,
        "features": ["memory", "search", "basic_stats"]
    },
    "starter": {
        "name": "Starter",
        "rpm": 300,
        "monthly_requests": 100000,
        "monthly_tokens": 1000000,
        "max_memories": 10000,
        "features": ["memory", "search", "stats", "collaboration"]
    },
    "pro": {
        "name": "Pro",
        "rpm": 1000,
        "monthly_requests": 1000000,
        "monthly_tokens": 10000000,
        "max_memories": 100000,
        "features": ["memory", "search", "stats", "collaboration", "workflows", "priority_support"]
    },
    "enterprise": {
        "name": "Enterprise",
        "rpm": 10000,
        "monthly_requests": -1,
        "monthly_tokens": -1,
        "max_memories": -1,
        "features": ["memory", "search", "stats", "collaboration", "workflows", "dedicated_support", "sla", "custom_integrations"]
    }
}


api_key_manager = APIKeyManager()
