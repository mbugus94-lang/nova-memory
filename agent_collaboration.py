#!/usr/bin/env python3
"""
Multi-Agent Collaboration for Nova Memory System v2.0

Provides:
- Collaborative memory spaces shared across multiple agents
- Agent-to-agent memory sharing with access-level control
- Expiry-aware share retrieval (expired shares are filtered out)
- Bidirectional memory synchronisation between agent pairs
"""

import sqlite3
import json
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentCollaboration:
    """Thread-safe multi-agent memory collaboration system."""

    def __init__(self, db_path: str = "nova_memory_v2.db"):
        self.db_path = db_path
        self._init_database()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @contextmanager
    def _get_conn(self):
        """Yield a SQLite connection with row_factory and auto-cleanup."""
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
        """Create collaboration tables if they do not already exist."""
        with self._get_conn() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collaborative_spaces (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    space_name  TEXT NOT NULL UNIQUE,
                    created_by  TEXT NOT NULL,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    members     TEXT,
                    permissions TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS space_memories (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    space_id   INTEGER NOT NULL,
                    memory_id  TEXT NOT NULL,
                    added_by   TEXT NOT NULL,
                    added_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (space_id) REFERENCES collaborative_spaces(id)
                )
            """)

            # FIX: column was named 'id' in DB but queried as 'share_id' — unified to 'id'
            cursor.execute("""
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

            conn.commit()
        print("[OK] Collaboration database initialised")

    # ------------------------------------------------------------------
    # Collaborative spaces
    # ------------------------------------------------------------------

    def create_collaborative_space(
        self,
        space_name: str,
        creator: str,
        members: Optional[List[str]] = None,
        permissions: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """
        Create a named collaborative memory space.

        Args:
            space_name:   Unique name for the space.
            creator:      Agent ID of the creator (auto-added to members).
            members:      List of agent IDs with access (creator always included).
            permissions:  Dict describing read/write rights.

        Returns:
            Space ID on success, ``None`` on failure.
        """
        all_members: List[str] = list({creator, *(members or [])})
        default_perms = {"read": True, "write": True}

        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO collaborative_spaces
                        (space_name, created_by, members, permissions)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        space_name,
                        creator,
                        json.dumps(all_members),
                        json.dumps(permissions or default_perms),
                    ),
                )
                space_id = cursor.lastrowid
                conn.commit()

            print(
                f"[OK] Space created  id={space_id}  name={space_name}  "
                f"members={len(all_members)}"
            )
            return space_id

        except Exception as exc:
            logger.exception("create_collaborative_space failed: %s", exc)
            print(f"[ERROR] Failed to create space: {exc}")
            return None

    def add_member_to_space(self, space_id: int, agent_id: str) -> bool:
        """Add an agent to an existing collaborative space."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT members FROM collaborative_spaces WHERE id = ?", (space_id,)
                )
                row = cursor.fetchone()
                if not row:
                    print(f"[WARN] Space {space_id} not found")
                    return False
                members: List[str] = json.loads(row["members"])
                if agent_id not in members:
                    members.append(agent_id)
                    cursor.execute(
                        "UPDATE collaborative_spaces SET members = ? WHERE id = ?",
                        (json.dumps(members), space_id),
                    )
                    conn.commit()
            print(f"[OK] Agent '{agent_id}' added to space {space_id}")
            return True
        except Exception as exc:
            logger.exception("add_member_to_space failed: %s", exc)
            return False

    def add_memory_to_space(
        self, space_id: int, memory_id: str, added_by: str
    ) -> bool:
        """Link an existing memory into a collaborative space."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO space_memories (space_id, memory_id, added_by)
                    VALUES (?, ?, ?)
                    """,
                    (space_id, memory_id, added_by),
                )
                conn.commit()
            print(f"[OK] Memory {memory_id} added to space {space_id}")
            return True
        except Exception as exc:
            logger.exception("add_memory_to_space failed: %s", exc)
            print(f"[ERROR] Failed to add memory to space: {exc}")
            return False

    def list_collaborative_spaces(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        Return all collaborative spaces the given agent belongs to.

        Membership is determined by a JSON array stored in the ``members``
        column, so the query uses a LIKE pattern match.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, space_name, created_by, created_at, members
                    FROM collaborative_spaces
                    WHERE members LIKE ?
                    """,
                    (f'%"{agent_name}"%',),
                )
                rows = cursor.fetchall()

            spaces = []
            for row in rows:
                members_list: List[str] = json.loads(row["members"])
                spaces.append({
                    "id": row["id"],
                    "space_name": row["space_name"],
                    "created_by": row["created_by"],
                    "created_at": row["created_at"],
                    "members": members_list,
                    "member_count": len(members_list),
                })

            print(f"[OK] Found {len(spaces)} space(s) for '{agent_name}'")
            return spaces

        except Exception as exc:
            logger.exception("list_collaborative_spaces failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Memory sharing
    # ------------------------------------------------------------------

    def share_memory_with_agent(
        self,
        from_agent: str,
        to_agent: str,
        memory_id: str,
        access_level: str = "read",
        expires_at: Optional[str] = None,
    ) -> Optional[int]:
        """
        Grant another agent access to a specific memory.

        Args:
            from_agent:   Sharing agent ID.
            to_agent:     Receiving agent ID.
            memory_id:    ID of the memory to share.
            access_level: ``"read"`` or ``"write"``.
            expires_at:   ISO-8601 timestamp after which the share expires.

        Returns:
            Share row ID on success, ``None`` on failure.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO agent_memory_shares
                        (from_agent, to_agent, memory_id, access_level, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (from_agent, to_agent, memory_id, access_level, expires_at),
                )
                share_id = cursor.lastrowid
                conn.commit()

            print(
                f"[OK] Share created  id={share_id}  "
                f"{from_agent} -> {to_agent}  memory={memory_id}  level={access_level}"
            )
            return share_id

        except Exception as exc:
            logger.exception("share_memory_with_agent failed: %s", exc)
            print(f"[ERROR] Failed to share memory: {exc}")
            return None

    def get_agent_memory_shares(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        Return all non-expired memory shares directed at ``agent_name``.

        Expired shares (where ``expires_at`` is in the past) are excluded
        automatically.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                # FIX: was SELECT share_id — column is actually 'id'
                cursor.execute(
                    """
                    SELECT id AS share_id, from_agent, memory_id,
                           access_level, expires_at, created_at
                    FROM agent_memory_shares
                    WHERE to_agent = ?
                      AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                    ORDER BY created_at DESC
                    """,
                    (agent_name,),
                )
                rows = cursor.fetchall()

            shares = []
            for row in rows:
                shares.append({
                    "share_id": row["share_id"],
                    "from_agent": row["from_agent"],
                    "memory_id": row["memory_id"],
                    "access_level": row["access_level"],
                    "expires_at": row["expires_at"],
                    "created_at": row["created_at"],
                })

            print(f"[OK] Found {len(shares)} active share(s) for '{agent_name}'")
            return shares

        except Exception as exc:
            logger.exception("get_agent_memory_shares failed: %s", exc)
            print(f"[ERROR] Failed to retrieve shares: {exc}")
            return []

    def revoke_share(self, share_id: int) -> bool:
        """Revoke a memory share by its ID."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM agent_memory_shares WHERE id = ?", (share_id,)
                )
                deleted = cursor.rowcount
                conn.commit()
            if deleted:
                print(f"[OK] Share {share_id} revoked")
                return True
            print(f"[WARN] Share {share_id} not found")
            return False
        except Exception as exc:
            logger.exception("revoke_share failed: %s", exc)
            return False

    def create_agent_memory_sync(
        self, agent_a: str, agent_b: str, shared_memory_id: str
    ) -> bool:
        """
        Create a bidirectional memory share between two agents.

        Both agents receive a ``"read"`` share of the given memory.

        Returns ``True`` if both shares were created successfully.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO agent_memory_shares
                        (from_agent, to_agent, memory_id, access_level)
                    VALUES (?, ?, ?, 'read')
                    """,
                    (agent_a, agent_b, shared_memory_id),
                )
                cursor.execute(
                    """
                    INSERT INTO agent_memory_shares
                        (from_agent, to_agent, memory_id, access_level)
                    VALUES (?, ?, ?, 'read')
                    """,
                    (agent_b, agent_a, shared_memory_id),
                )
                conn.commit()

            print(
                f"[OK] Bidirectional sync  {agent_a} <-> {agent_b}  memory={shared_memory_id}"
            )
            return True

        except Exception as exc:
            logger.exception("create_agent_memory_sync failed: %s", exc)
            print(f"[ERROR] Failed to create memory sync: {exc}")
            return False


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    test_db = "/tmp/nova_collab_test.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    collaboration = AgentCollaboration(db_path=test_db)

    print("\n" + "=" * 60)
    print("MULTI-AGENT COLLABORATION — NOVA MEMORY v2.0")
    print("=" * 60)

    space_id = collaboration.create_collaborative_space(
        space_name="Nova Agents",
        creator="nexus",
        members=["nexus", "sentinel"],
        permissions={"read": True, "write": True},
    )

    if space_id:
        collaboration.add_memory_to_space(space_id, "mem-001", "nexus")

        share_id = collaboration.share_memory_with_agent(
            from_agent="nexus",
            to_agent="sentinel",
            memory_id="mem-001",
            access_level="read",
        )

        spaces = collaboration.list_collaborative_spaces("sentinel")
        print(f"Sentinel is in {len(spaces)} space(s)")

        shares = collaboration.get_agent_memory_shares("sentinel")
        print(f"Sentinel has {len(shares)} active share(s)")

        if share_id:
            collaboration.revoke_share(share_id)
            shares_after = collaboration.get_agent_memory_shares("sentinel")
            print(f"After revoke: {len(shares_after)} share(s)")

        collaboration.create_agent_memory_sync("nexus", "sentinel", "mem-002")

    print("\n" + "=" * 60)
    print("COLLABORATION TEST COMPLETE")
    print("=" * 60)
