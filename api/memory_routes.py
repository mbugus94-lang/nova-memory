"""
Simple key-value memory API used by OpenClaw skills.
Implements /api/v2/memory/* endpoints with SQLite persistence and optional Redis cache.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel, Field

from core.redis_cache import get_redis_cache

router = APIRouter(prefix="/api/v2/memory", tags=["memory"])


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _resolve_db_path() -> Path:
    explicit = os.getenv("NOVA_MEMORY_DB_PATH") or os.getenv("NOVA_KV_DB_PATH")
    if explicit:
        return Path(explicit).expanduser()

    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith("sqlite:///"):
        raw = database_url[len("sqlite:///") :]
        return Path(raw).expanduser()

    openclaw_dir = Path(os.getenv("OPENCLAW_MEMORY_DIR", Path.home() / ".openclaw" / "memory"))

    # Check for v2 DB locally first (aligns with server.py)
    local_v2 = Path("nova_memory_v2.db")
    if local_v2.exists():
        return local_v2.resolve()

    return openclaw_dir / "nova_memory_central.db"


def _cache_enabled() -> bool:
    return _get_bool_env("NOVA_CACHE_ENABLED", False)


def _cache_ttl_default() -> int:
    return _get_int_env("NOVA_CACHE_TTL", _get_int_env("REDIS_CACHE_TTL", 3600))


def _default_ttl() -> int:
    return _get_int_env("NOVA_DEFAULT_TTL", 86400)


@dataclass
class MemoryRecord:
    key: str
    value: Any
    created_at: str
    updated_at: str
    expires_at: Optional[int]
    agent_id: Optional[str]


class MemoryStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.Error:
            pass # Ignore if DB locked or readonly
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_kv (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    agent_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at INTEGER
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_kv_agent ON memory_kv(agent_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_kv_expires ON memory_kv(expires_at)"
            )
            conn.commit()
        finally:
            conn.close()

    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        try:
            value = json.loads(row["value"])
        except Exception:
            value = row["value"]
        return MemoryRecord(
            key=row["key"],
            value=value,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            expires_at=row["expires_at"],
            agent_id=row["agent_id"],
        )

    def store(self, key: str, value: Any, ttl: Optional[int], agent_id: Optional[str]) -> MemoryRecord:
        now_iso = datetime.now(timezone.utc).isoformat() + "Z"
        expires_at = None
        if ttl is not None and ttl > 0:
            expires_at = int(time.time()) + int(ttl)

        if not agent_id and ":" in key:
            parts = key.split(":")
            if len(parts) >= 2:
                agent_id = parts[1]

        value_json = json.dumps(value) if not isinstance(value, str) else value

        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT created_at FROM memory_kv WHERE key = ?", (key,))
            existing = cursor.fetchone()
            created_at = existing["created_at"] if existing else now_iso
            cursor.execute(
                """
                INSERT OR REPLACE INTO memory_kv
                (key, value, agent_id, created_at, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (key, value_json, agent_id, created_at, now_iso, expires_at),
            )
            conn.commit()
        finally:
            conn.close()

        return MemoryRecord(
            key=key,
            value=value,
            created_at=created_at,
            updated_at=now_iso,
            expires_at=expires_at,
            agent_id=agent_id,
        )

    def retrieve(self, key: str) -> Optional[MemoryRecord]:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memory_kv WHERE key = ?", (key,))
            row = cursor.fetchone()
            if not row:
                return None

            record = self._row_to_record(row)
            if record.expires_at and record.expires_at <= int(time.time()):
                cursor.execute("DELETE FROM memory_kv WHERE key = ?", (key,))
                conn.commit()
                return None

            return record
        finally:
            conn.close()

    def delete(self, key: str) -> bool:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memory_kv WHERE key = ?", (key,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted > 0
        finally:
            conn.close()

    def search(self, query: str, agent_id: Optional[str], limit: int) -> List[MemoryRecord]:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            sql = "SELECT * FROM memory_kv WHERE (key LIKE ? OR value LIKE ?)"
            params: List[Any] = [f"%{query}%", f"%{query}%"]

            if agent_id:
                sql += " AND agent_id = ?"
                params.append(agent_id)

            sql += " AND (expires_at IS NULL OR expires_at > ?)"
            params.append(int(time.time()))

            sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [self._row_to_record(row) for row in rows]
        finally:
            conn.close()

    def list_keys(self, pattern: str, agent_id: Optional[str], limit: int) -> List[MemoryRecord]:
        sql_pattern = pattern.replace("*", "%").replace("?", "_")
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            sql = "SELECT * FROM memory_kv WHERE key LIKE ?"
            params: List[Any] = [sql_pattern]

            if agent_id:
                sql += " AND agent_id = ?"
                params.append(agent_id)

            sql += " AND (expires_at IS NULL OR expires_at > ?)"
            params.append(int(time.time()))

            sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [self._row_to_record(row) for row in rows]
        finally:
            conn.close()


_store: Optional[MemoryStore] = None


def _get_store() -> MemoryStore:
    global _store
    if _store is None:
        _store = MemoryStore(_resolve_db_path())
    return _store


def _get_cache():
    if not _cache_enabled():
        return None
    return get_redis_cache()


def _cache_key(key: str) -> str:
    return f"nova:memory:{key}"


class MemoryStoreRequest(BaseModel):
    key: str = Field(..., min_length=1)
    value: Any
    ttl: Optional[int] = Field(None, ge=0)
    agent_id: Optional[str] = None


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    agent: Optional[str] = None
    agent_filter: Optional[str] = None
    limit: int = Field(10, ge=1, le=200)


@router.post("/store")
async def store_memory(payload: MemoryStoreRequest):
    store = _get_store()
    ttl = payload.ttl if payload.ttl is not None else _default_ttl()
    record = store.store(payload.key, payload.value, ttl, payload.agent_id)

    cache = _get_cache()
    if cache and cache.enabled:
        ttl = ttl if ttl is not None else _cache_ttl_default()
        cache.set(
            _cache_key(payload.key),
            {
                "value": record.value,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "expires_at": record.expires_at,
                "agent_id": record.agent_id,
            },
            ttl=ttl if ttl > 0 else _cache_ttl_default(),
        )

    return {
        "success": True,
        "key": payload.key,
        "stored": True,
        "ttl": ttl if ttl is not None else 0,
        "expires_at": record.expires_at,
        "cache_hit": False,
    }


@router.get("/retrieve/{key}")
async def retrieve_memory(key: str):
    cache = _get_cache()
    if cache and cache.enabled:
        cached = cache.get(_cache_key(key))
        if cached:
            expires_at = cached.get("expires_at")
            if expires_at and expires_at <= int(time.time()):
                cache.delete(_cache_key(key))
            else:
                created_at = cached.get("created_at")
                age_seconds = _age_seconds(created_at)
                ttl_remaining = _ttl_remaining(expires_at)
                return {
                    "success": True,
                    "found": True,
                    "key": key,
                    "value": cached.get("value"),
                    "age_seconds": age_seconds,
                    "ttl_remaining": ttl_remaining,
                    "from_cache": True,
                    "created_at": created_at,
                    "updated_at": cached.get("updated_at"),
                }

    store = _get_store()
    record = store.retrieve(key)
    if not record:
        return {
            "success": True,
            "found": False,
            "key": key,
            "message": "No memory found for this key",
            "suggestions": [
                "Check key spelling",
                "Try searching instead of retrieve",
                "Key may have expired",
            ],
        }

    if cache and cache.enabled:
        ttl = _ttl_remaining(record.expires_at)
        cache.set(
            _cache_key(key),
            {
                "value": record.value,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "expires_at": record.expires_at,
                "agent_id": record.agent_id,
            },
            ttl=ttl if ttl > 0 else _cache_ttl_default(),
        )

    return {
        "success": True,
        "found": True,
        "key": key,
        "value": record.value,
        "age_seconds": _age_seconds(record.created_at),
        "ttl_remaining": _ttl_remaining(record.expires_at),
        "from_cache": False,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


@router.post("/search")
async def search_memory(payload: MemorySearchRequest):
    agent_filter = payload.agent_filter or payload.agent
    store = _get_store()
    records = store.search(payload.query, agent_filter, payload.limit)

    results = []
    for record in records:
        results.append(
            {
                "key": record.key,
                "value": record.value,
                "created_at": record.created_at,
                "relevance_score": 1.0,
                "age_seconds": _age_seconds(record.created_at),
            }
        )

    return {
        "success": True,
        "query": payload.query,
        "agent_filter": agent_filter,
        "results_count": len(results),
        "count": len(results),
        "results": results,
    }


@router.get("/list")
async def list_memory(
    pattern: str = Query("*"),
    agent: Optional[str] = None,
    limit: int = Query(200, ge=1, le=2000),
):
    store = _get_store()
    records = store.list_keys(pattern, agent, limit)

    keys = [record.key for record in records]
    ages = [_age_seconds(record.created_at) for record in records if record.created_at]

    return {
        "success": True,
        "pattern": pattern,
        "keys_found": len(keys),
        "count": len(keys),
        "keys": keys,
        "oldest_key_age_days": _age_days(max(ages)) if ages else None,
        "newest_key_age_days": _age_days(min(ages)) if ages else None,
    }


@router.delete("/delete/{key}")
async def delete_memory(
    key: str,
    x_confirm: Optional[str] = Header(None, alias="X-Confirm"),
):
    if not x_confirm or str(x_confirm).lower() != "true":
        return {
            "success": True,
            "deleted": False,
            "key": key,
            "message": "Confirmation required (set X-Confirm: true)",
        }

    store = _get_store()
    deleted = store.delete(key)

    cache = _get_cache()
    if cache and cache.enabled:
        cache.delete(_cache_key(key))

    if not deleted:
        return {
            "success": True,
            "deleted": False,
            "key": key,
            "message": "Memory key not found",
        }

    return {
        "success": True,
        "deleted": True,
        "key": key,
        "message": "Memory entry successfully removed",
    }


def _age_seconds(created_at: Optional[str]) -> Optional[int]:
    if not created_at:
        return None
    try:
        base = created_at.replace("Z", "")
        created = datetime.fromisoformat(base)
    except Exception:
        return None
    return int((datetime.now(timezone.utc) - created).total_seconds())


def _ttl_remaining(expires_at: Optional[int]) -> int:
    if not expires_at:
        return 0
    remaining = int(expires_at - time.time())
    return remaining if remaining > 0 else 0


def _age_days(age_seconds: Optional[int]) -> Optional[int]:
    if age_seconds is None:
        return None
    return int(age_seconds / 86400)
