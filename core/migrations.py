"""
Nova Memory — Database Migration System

A lightweight migration framework that uses raw SQLite (no SQLAlchemy required).
Migrations are tracked in a _migrations table and applied in order.

Usage:
    from core.migrations import run_migrations
    run_migrations(db_path="nova_memory_v2.db")
"""

import sqlite3
import logging
from typing import Callable, List, Dict, Any

logger = logging.getLogger(__name__)

# Registry of all migrations — append new ones here
MIGRATIONS: List[Dict[str, Any]] = []


def migration(version: int, description: str):
    """Decorator to register a migration function."""
    def decorator(fn: Callable[[sqlite3.Connection], None]):
        MIGRATIONS.append({
            "version": version,
            "description": description,
            "fn": fn,
        })
        return fn
    return decorator


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    """Create the migrations tracking table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            version     INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def _get_applied_versions(conn: sqlite3.Connection) -> set:
    """Return the set of already-applied migration versions."""
    cursor = conn.execute("SELECT version FROM _migrations")
    return {row[0] for row in cursor.fetchall()}


def run_migrations(db_path: str) -> int:
    """
    Apply all pending migrations to the database.

    Args:
        db_path: Path to the SQLite database.

    Returns:
        Number of migrations applied.
    """
    # Sort migrations by version
    sorted_migrations = sorted(MIGRATIONS, key=lambda m: m["version"])

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_migrations_table(conn)
        applied = _get_applied_versions(conn)
        count = 0

        for m in sorted_migrations:
            if m["version"] in applied:
                continue

            logger.info("Applying migration %d: %s", m["version"], m["description"])
            try:
                conn.execute("BEGIN")
                m["fn"](conn)
                conn.execute(
                    "INSERT INTO _migrations (version, description) VALUES (?, ?)",
                    (m["version"], m["description"]),
                )
                conn.commit()
                count += 1
                logger.info("Migration %d applied successfully", m["version"])
            except Exception:
                conn.rollback()
                logger.exception("Migration %d failed", m["version"])
                raise

        return count
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Migration definitions
# ---------------------------------------------------------------------------

@migration(1, "Create core tables (memories, versions, backups, FTS)")
def _migration_001(conn: sqlite3.Connection) -> None:
    """Create the base schema that EnhancedMemoryStorage expects."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id          TEXT PRIMARY KEY,
            version     INTEGER DEFAULT 1,
            content     TEXT NOT NULL,
            compressed  BOOLEAN DEFAULT 1,
            compressed_size  INTEGER DEFAULT 0,
            original_size    INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata    TEXT,
            tags        TEXT,
            author      TEXT,
            access_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_versions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_id   TEXT NOT NULL,
            version     INTEGER NOT NULL,
            content     TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (memory_id) REFERENCES memories(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backups (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_name TEXT NOT NULL,
            backup_data TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            size_bytes  INTEGER
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
        USING fts5(memory_id UNINDEXED, content, tags)
    """)


@migration(2, "Create collaboration tables")
def _migration_002(conn: sqlite3.Connection) -> None:
    """Create collaboration tables that AgentCollaboration expects."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collaborative_spaces (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            space_name  TEXT NOT NULL UNIQUE,
            created_by  TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            members     TEXT,
            permissions TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS space_memories (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            space_id   INTEGER NOT NULL,
            memory_id  TEXT NOT NULL,
            added_by   TEXT NOT NULL,
            added_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (space_id) REFERENCES collaborative_spaces(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_memory_shares (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            from_agent   TEXT NOT NULL,
            to_agent     TEXT NOT NULL,
            memory_id    TEXT NOT NULL,
            access_level TEXT DEFAULT 'read',
            expires_at   TIMESTAMP,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


@migration(3, "Create API tables (agents, interactions, workflows)")
def _migration_003(conn: sqlite3.Connection) -> None:
    """Create tables used by the API server."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id           TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            role         TEXT NOT NULL,
            status       TEXT DEFAULT 'active',
            capabilities TEXT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id             TEXT PRIMARY KEY,
            agent_id       TEXT,
            user_message   TEXT NOT NULL,
            agent_response TEXT NOT NULL,
            user_feedback  TEXT,
            loss           REAL,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workflows (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            description TEXT,
            status      TEXT DEFAULT 'active',
            task_count  INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


@migration(4, "Create key-value memory table")
def _migration_004(conn: sqlite3.Connection) -> None:
    """Create the key-value memory table for memory_routes."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_kv (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            agent_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            expires_at INTEGER
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_kv_agent ON memory_kv(agent_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_kv_expires ON memory_kv(expires_at)")


@migration(5, "Create rate limiting table")
def _migration_005(conn: sqlite3.Connection) -> None:
    """Create table for persistent rate limiting."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rate_limits (
            client_id   TEXT NOT NULL,
            endpoint    TEXT NOT NULL,
            window_start INTEGER NOT NULL,
            request_count INTEGER DEFAULT 1,
            PRIMARY KEY (client_id, endpoint, window_start)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_limits_window ON rate_limits(window_start)")
