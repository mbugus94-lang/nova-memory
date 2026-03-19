"""
Shared database connection utilities for Nova Memory.
Provides both sync and async connection context managers with unified DB path resolution.
"""

import os
import sqlite3
import logging
import asyncio
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import AsyncGenerator, Generator, Optional

logger = logging.getLogger(__name__)

# aiosqlite is optional — imported lazily
_aiosqlite_available: Optional[bool] = None


def _check_aiosqlite() -> bool:
    global _aiosqlite_available
    if _aiosqlite_available is None:
        try:
            import aiosqlite  # noqa: F401
            _aiosqlite_available = True
        except ImportError:
            _aiosqlite_available = False
            logger.warning("aiosqlite not installed — async DB operations will use sync fallback")
    return _aiosqlite_available


def resolve_db_path() -> str:
    """Resolve the database path from environment or defaults."""
    explicit = os.getenv("NOVA_MEMORY_DB_PATH") or os.getenv("NOVA_KV_DB_PATH")
    if explicit:
        return str(Path(explicit).expanduser().resolve())

    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith("sqlite:///"):
        raw = database_url[len("sqlite:///"):]
        return str(Path(raw).expanduser().resolve())

    db_path = os.getenv("DATABASE_PATH", "nova_memory_v2.db")
    return str(Path(db_path).resolve())


def get_db_path() -> str:
    """Get the unified database path."""
    return resolve_db_path()


@contextmanager
def get_conn(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """
    Yield a synchronous SQLite connection with row_factory and guaranteed cleanup.

    Usage:
        with get_conn(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(...)
            conn.commit()
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@asynccontextmanager
async def get_async_conn(db_path: str) -> AsyncGenerator:
    """
    Yield an async SQLite connection via aiosqlite.

    Falls back to sync connection if aiosqlite is not installed.

    Usage:
        async with get_async_conn(db_path) as conn:
            await conn.execute("SELECT * FROM memories")
    """
    if _check_aiosqlite():
        import aiosqlite
        conn = await aiosqlite.connect(db_path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        except Exception:
            await conn.rollback()
            raise
        finally:
            await conn.close()
    else:
        # Sync fallback — wraps in thread executor
        asyncio.get_event_loop()
        sync_conn = sqlite3.connect(db_path)
        sync_conn.row_factory = sqlite3.Row
        sync_conn.execute("PRAGMA journal_mode=WAL")
        sync_conn.execute("PRAGMA foreign_keys=ON")

        class _SyncFallback:
            """Wraps a sync connection to mimic aiosqlite interface."""
            def __init__(self, conn):
                self._conn = conn

            async def execute(self, sql, params=None):
                cursor = self._conn.cursor()
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                return cursor

            async def commit(self):
                self._conn.commit()

            async def rollback(self):
                self._conn.rollback()

            async def close(self):
                self._conn.close()

        yield _SyncFallback(sync_conn)


def init_table(conn: sqlite3.Connection, sql: str) -> None:
    """Execute a CREATE TABLE IF NOT EXISTS statement."""
    conn.cursor().execute(sql)


def db_exists(db_path: str) -> bool:
    """Check if the database file exists and has tables."""
    path = Path(db_path)
    if not path.exists():
        return False
    try:
        with get_conn(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return cursor.fetchone() is not None
    except Exception:
        return False
