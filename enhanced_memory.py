#!/usr/bin/env python3
"""
Enhanced Memory Storage for Nova Memory System v2.0

Core persistent memory layer for AI agents:
- Compressed, versioned memory storage backed by SQLite
- Full-text search across all memories
- Access-count tracking and LRU eviction hints
- Update, delete, and tag-based filtering
- Thread-safe connection handling via context managers
"""

import sqlite3
import json
import zlib
import uuid
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EnhancedMemoryStorage:
    """
    Persistent, compressed memory storage with versioning for AI agents.

    Each memory is zlib-compressed before storage to reduce disk footprint.
    All reads automatically decompress and increment the access counter so
    agents can identify frequently-used memories.
    """

    def __init__(self, db_path: str = "nova_memory_v2.db"):
        self.db_path = db_path
        self._init_database()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @contextmanager
    def _get_conn(self):
        """Yield a SQLite connection and guarantee cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Create all required tables if they do not already exist."""
        with self._get_conn() as conn:
            cursor = conn.cursor()

            cursor.execute("""
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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_versions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id   TEXT NOT NULL,
                    version     INTEGER NOT NULL,
                    content     TEXT NOT NULL,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (memory_id) REFERENCES memories(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_name TEXT NOT NULL,
                    backup_data TEXT NOT NULL,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    size_bytes  INTEGER
                )
            """)

            # FTS virtual table for full-text search (plain-text content mirror)
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
                USING fts5(memory_id UNINDEXED, content, tags)
            """)

            conn.commit()
        logger.info("Enhanced database initialised: %s", self.db_path)
        print(f"[OK] Enhanced database initialised: {self.db_path}")

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        memory_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Store a new memory with optional metadata and tags.

        Args:
            content:   Plain-text content to store.
            metadata:  Arbitrary JSON-serialisable dict.
            tags:      List of string labels for filtering.
            author:    Identifier of the agent/user creating the memory.
            memory_id: Optional explicit ID; auto-generated if omitted.

        Returns:
            The memory ID on success, ``None`` on failure.
        """
        if not content or not content.strip():
            logger.warning("add_memory called with empty content – skipped.")
            return None

        mid = memory_id or str(uuid.uuid4())
        original_size = len(content.encode("utf-8"))
        compressed = zlib.compress(content.encode("utf-8"), level=6)
        compressed_size = len(compressed)

        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO memories
                        (id, content, compressed, compressed_size, original_size,
                         metadata, tags, author)
                    VALUES (?, ?, 1, ?, ?, ?, ?, ?)
                    """,
                    (
                        mid,
                        compressed.hex(),
                        compressed_size,
                        original_size,
                        json.dumps(metadata) if metadata else None,
                        json.dumps(tags) if tags else None,
                        author,
                    ),
                )
                # Version history
                cursor.execute(
                    "INSERT INTO memory_versions (memory_id, version, content) VALUES (?, 1, ?)",
                    (mid, content),
                )
                # FTS index
                tags_str = " ".join(tags) if tags else ""
                cursor.execute(
                    "INSERT INTO memories_fts (memory_id, content, tags) VALUES (?, ?, ?)",
                    (mid, content, tags_str),
                )
                conn.commit()

            ratio = (compressed_size / original_size * 100) if original_size else 0
            print(f"[OK] Memory stored  id={mid}  original={original_size}B  "
                  f"compressed={compressed_size}B  ratio={ratio:.1f}%")
            return mid

        except Exception as exc:
            logger.exception("add_memory failed: %s", exc)
            print(f"[ERROR] Failed to add memory: {exc}")
            return None

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory by ID, incrementing its access counter.

        Returns a dict with keys: id, content, metadata, tags, author,
        access_count, last_accessed, version, created_at, updated_at.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, content, compressed, metadata, tags, author,
                           access_count, last_accessed, version, created_at, updated_at
                    FROM memories WHERE id = ?
                    """,
                    (memory_id,),
                )
                row = cursor.fetchone()
                if not row:
                    print(f"[WARN] Memory not found: {memory_id}")
                    return None

                # Decompress
                if row["compressed"]:
                    raw = bytes.fromhex(row["content"])
                    content = zlib.decompress(raw).decode("utf-8")
                else:
                    content = row["content"]

                # Update access tracking
                cursor.execute(
                    """
                    UPDATE memories
                    SET access_count = access_count + 1,
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (memory_id,),
                )
                conn.commit()

            return {
                "id": row["id"],
                "content": content,
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                "tags": json.loads(row["tags"]) if row["tags"] else None,
                "author": row["author"],
                "access_count": row["access_count"] + 1,
                "last_accessed": datetime.utcnow().isoformat(),
                "version": row["version"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

        except Exception as exc:
            logger.exception("get_memory failed: %s", exc)
            print(f"[ERROR] Failed to retrieve memory: {exc}")
            return None

    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Update an existing memory's content and/or metadata.

        A new version snapshot is written to memory_versions before the
        update so the full history is preserved.

        Returns ``True`` on success.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT content, compressed, version FROM memories WHERE id = ?",
                    (memory_id,),
                )
                row = cursor.fetchone()
                if not row:
                    print(f"[WARN] update_memory: id={memory_id} not found")
                    return False

                # Snapshot current version
                if row["compressed"]:
                    old_content = zlib.decompress(bytes.fromhex(row["content"])).decode("utf-8")
                else:
                    old_content = row["content"]
                new_version = row["version"] + 1
                cursor.execute(
                    "INSERT INTO memory_versions (memory_id, version, content) VALUES (?, ?, ?)",
                    (memory_id, row["version"], old_content),
                )

                updates: List[str] = ["version = ?", "updated_at = CURRENT_TIMESTAMP"]
                params: List[Any] = [new_version]

                if content is not None:
                    compressed = zlib.compress(content.encode("utf-8"), level=6)
                    updates += ["content = ?", "compressed = 1",
                                "compressed_size = ?", "original_size = ?"]
                    params += [compressed.hex(), len(compressed), len(content.encode("utf-8"))]
                    # Refresh FTS
                    tags_str = " ".join(tags) if tags else ""
                    cursor.execute(
                        "UPDATE memories_fts SET content = ?, tags = ? WHERE memory_id = ?",
                        (content, tags_str, memory_id),
                    )

                if metadata is not None:
                    updates.append("metadata = ?")
                    params.append(json.dumps(metadata))

                if tags is not None:
                    updates.append("tags = ?")
                    params.append(json.dumps(tags))

                params.append(memory_id)
                cursor.execute(
                    f"UPDATE memories SET {', '.join(updates)} WHERE id = ?",
                    params,
                )
                conn.commit()

            print(f"[OK] Memory updated  id={memory_id}  new_version={new_version}")
            return True

        except Exception as exc:
            logger.exception("update_memory failed: %s", exc)
            print(f"[ERROR] Failed to update memory: {exc}")
            return False

    def delete_memory(self, memory_id: str) -> bool:
        """
        Permanently delete a memory and all its version history.

        Returns ``True`` on success.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memory_versions WHERE memory_id = ?", (memory_id,))
                cursor.execute("DELETE FROM memories_fts WHERE memory_id = ?", (memory_id,))
                cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
                deleted = cursor.rowcount
                conn.commit()

            if deleted:
                print(f"[OK] Memory deleted  id={memory_id}")
                return True
            print(f"[WARN] delete_memory: id={memory_id} not found")
            return False

        except Exception as exc:
            logger.exception("delete_memory failed: %s", exc)
            print(f"[ERROR] Failed to delete memory: {exc}")
            return False

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_memories(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Full-text search across memory content and tags.

        Uses SQLite FTS5 for fast ranked retrieval.  Optionally filters by
        one or more tags (all provided tags must be present).

        Args:
            query:  Search string (FTS5 syntax supported).
            tags:   Optional list of tags to filter by.
            limit:  Maximum number of results to return.

        Returns:
            List of memory dicts sorted by relevance.
        """
        if not query or not query.strip():
            return self.list_memories(limit=limit)

        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                # FTS5 match
                cursor.execute(
                    """
                    SELECT m.id, m.content, m.compressed, m.metadata, m.tags,
                           m.author, m.access_count, m.created_at
                    FROM memories m
                    JOIN memories_fts f ON f.memory_id = m.id
                    WHERE memories_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (query, limit * 2),  # over-fetch to allow tag filtering
                )
                rows = cursor.fetchall()

            results = []
            for row in rows:
                if row["compressed"]:
                    content = zlib.decompress(bytes.fromhex(row["content"])).decode("utf-8")
                else:
                    content = row["content"]

                row_tags: List[str] = json.loads(row["tags"]) if row["tags"] else []

                # Tag filter
                if tags:
                    if not all(t in row_tags for t in tags):
                        continue

                results.append({
                    "id": row["id"],
                    "content": content,
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                    "tags": row_tags,
                    "author": row["author"],
                    "access_count": row["access_count"],
                    "created_at": row["created_at"],
                })
                if len(results) >= limit:
                    break

            print(f"[OK] search_memories query='{query}'  found={len(results)}")
            return results

        except Exception as exc:
            logger.exception("search_memories failed: %s", exc)
            print(f"[ERROR] search_memories failed: {exc}")
            return []

    def list_memories(
        self,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List memories with optional tag/author filters.

        Returns memories ordered by most recently created.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                where_clauses: List[str] = []
                params: List[Any] = []

                if author:
                    where_clauses.append("author = ?")
                    params.append(author)

                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                cursor.execute(
                    f"""
                    SELECT id, content, compressed, metadata, tags, author,
                           access_count, created_at, updated_at
                    FROM memories
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (*params, limit, offset),
                )
                rows = cursor.fetchall()

            results = []
            for row in rows:
                if row["compressed"]:
                    content = zlib.decompress(bytes.fromhex(row["content"])).decode("utf-8")
                else:
                    content = row["content"]

                row_tags: List[str] = json.loads(row["tags"]) if row["tags"] else []
                if tags and not all(t in row_tags for t in tags):
                    continue

                results.append({
                    "id": row["id"],
                    "content": content,
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                    "tags": row_tags,
                    "author": row["author"],
                    "access_count": row["access_count"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                })

            return results

        except Exception as exc:
            logger.exception("list_memories failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Backup / restore
    # ------------------------------------------------------------------

    def create_backup(self, backup_name: str) -> Optional[int]:
        """
        Snapshot the entire database into the backups table.

        Returns the backup row ID on success.
        """
        try:
            with open(self.db_path, "rb") as fh:
                backup_data = fh.read()
            size_bytes = len(backup_data)

            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO backups (backup_name, backup_data, size_bytes) VALUES (?, ?, ?)",
                    (backup_name, backup_data.hex(), size_bytes),
                )
                backup_id = cursor.lastrowid
                conn.commit()

            print(f"[OK] Backup created  id={backup_id}  name={backup_name}  "
                  f"size={size_bytes/1024:.1f} KB")
            return backup_id

        except Exception as exc:
            logger.exception("create_backup failed: %s", exc)
            print(f"[ERROR] Failed to create backup: {exc}")
            return None

    def restore_backup(self, backup_id: int) -> bool:
        """
        Restore the database from a stored backup snapshot.

        Returns ``True`` on success.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT backup_data FROM backups WHERE id = ?", (backup_id,)
                )
                row = cursor.fetchone()

            if not row:
                print(f"[WARN] Backup not found: {backup_id}")
                return False

            backup_data = bytes.fromhex(row["backup_data"])
            with open(self.db_path, "wb") as fh:
                fh.write(backup_data)

            print(f"[OK] Backup restored  id={backup_id}")
            return True

        except Exception as exc:
            logger.exception("restore_backup failed: %s", exc)
            print(f"[ERROR] Failed to restore backup: {exc}")
            return False

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_memory_stats(self) -> Optional[Dict[str, Any]]:
        """Return aggregate statistics about the memory store."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) AS cnt FROM memories")
                total = cursor.fetchone()["cnt"]

                cursor.execute(
                    "SELECT COALESCE(SUM(original_size),0) AS s FROM memories"
                )
                total_original = cursor.fetchone()["s"]

                cursor.execute(
                    "SELECT COALESCE(SUM(compressed_size),0) AS s FROM memories"
                )
                total_compressed = cursor.fetchone()["s"]

                cursor.execute(
                    """
                    SELECT id, access_count FROM memories
                    ORDER BY access_count DESC LIMIT 5
                    """
                )
                top = cursor.fetchall()

            saved = total_original - total_compressed
            ratio = (saved / total_original * 100) if total_original else 0

            stats = {
                "total_memories": total,
                "total_storage_bytes": total_original,
                "compressed_storage_bytes": total_compressed,
                "storage_saved_bytes": saved,
                "compression_ratio_pct": round(ratio, 2),
                "top_memories": [(r["id"], r["access_count"]) for r in top],
            }
            print(
                f"[OK] Stats  total={total}  "
                f"original={total_original/1024:.1f}KB  "
                f"compressed={total_compressed/1024:.1f}KB  "
                f"saved={ratio:.1f}%"
            )
            return stats

        except Exception as exc:
            logger.exception("get_memory_stats failed: %s", exc)
            print(f"[ERROR] Failed to get statistics: {exc}")
            return None


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    test_db = "/tmp/nova_test.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    storage = EnhancedMemoryStorage(db_path=test_db)

    print("\n" + "=" * 60)
    print("ENHANCED MEMORY STORAGE — NOVA MEMORY v2.0")
    print("=" * 60)

    # Add memories
    mid1 = storage.add_memory(
        "User prefers concise responses about Python programming.",
        metadata={"type": "preference"},
        tags=["preference", "python"],
        author="agent_alpha",
    )
    mid2 = storage.add_memory(
        "The project deadline is 2026-04-01 for the Nova Memory release.",
        metadata={"type": "fact"},
        tags=["deadline", "project"],
        author="agent_beta",
    )

    # Retrieve
    mem = storage.get_memory(mid1)
    print(f"\nRetrieved: {mem['content'][:60]}  access_count={mem['access_count']}")

    # Search
    results = storage.search_memories("Python")
    print(f"Search 'Python' → {len(results)} result(s)")

    # Update
    storage.update_memory(mid1, content="User strongly prefers concise Python answers.")
    updated = storage.get_memory(mid1)
    print(f"Updated content: {updated['content']}")

    # Stats
    storage.get_memory_stats()

    # Backup
    storage.create_backup("smoke_test_backup")

    # Delete
    storage.delete_memory(mid2)
    print(f"After delete, list has {len(storage.list_memories())} memories")

    print("\n" + "=" * 60)
    print("SMOKE TEST COMPLETE")
    print("=" * 60)
