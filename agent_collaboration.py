#!/usr/bin/env python3
"""
Multi-Agent Collaboration for Nova Memory System v2.0
"""

import sqlite3
import json
from datetime import datetime

class AgentCollaboration:
    """Multi-agent memory collaboration system"""

    def __init__(self, db_path="nova_memory_v2.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize collaboration database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create collaborative spaces table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collaborative_spaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                space_name TEXT NOT NULL UNIQUE,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                members TEXT,
                permissions TEXT
            )
        """)

        # Create space memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS space_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                space_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                added_by TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (space_id) REFERENCES collaborative_spaces(id),
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        """)

        # Create agent memory sharing table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_memory_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_agent TEXT NOT NULL,
                to_agent TEXT NOT NULL,
                memory_id INTEGER NOT NULL,
                access_level TEXT DEFAULT "read",
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        """)

        conn.commit()
        conn.close()

        print(f"[OK] Collaboration database initialized")

    def create_collaborative_space(self, space_name, creator, members=None, permissions=None):
        """Create a new collaborative space"""
        print(f"\n[INFO] Creating collaborative space: {space_name}...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO collaborative_spaces (space_name, created_by, members, permissions)
                VALUES (?, ?, ?, ?)
            """, (
                space_name,
                creator,
                json.dumps(members) if members else json.dumps([creator]),
                json.dumps(permissions) if permissions else json.dumps({"read": True, "write": True})
            ))

            space_id = cursor.lastrowid
            conn.commit()

            print(f"[OK] Collaborative space created with ID: {space_id}")
            print(f"  - Name: {space_name}")
            print(f"  - Creator: {creator}")
            print(f"  - Members: {len(members) if members else 1}")

            return space_id
        except Exception as e:
            print(f"[ERROR] Failed to create space: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def add_memory_to_space(self, space_id, memory_id, added_by):
        """Add a memory to a collaborative space"""
        print(f"\n[INFO] Adding memory {memory_id} to space {space_id}...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO space_memories (space_id, memory_id, added_by)
                VALUES (?, ?, ?)
            """, (space_id, memory_id, added_by))

            conn.commit()

            print(f"[OK] Memory added to space")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to add memory to space: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def share_memory_with_agent(self, from_agent, to_agent, memory_id, access_level="read", expires_at=None):
        """Share a memory with another agent"""
        print(f"\n[INFO] Sharing memory {memory_id} from {from_agent} to {to_agent}...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO agent_memory_shares (from_agent, to_agent, memory_id, access_level, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (from_agent, to_agent, memory_id, access_level, expires_at))

            share_id = cursor.lastrowid
            conn.commit()

            print(f"[OK] Memory shared successfully")
            print(f"  - Share ID: {share_id}")
            print(f"  - Access level: {access_level}")

            return share_id
        except Exception as e:
            print(f"[ERROR] Failed to share memory: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def get_agent_memory_shares(self, agent_name):
        """Get all memory shares for an agent"""
        print(f"\n[INFO] Retrieving memory shares for {agent_name}...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT share_id, from_agent, memory_id, access_level, expires_at, created_at
                FROM agent_memory_shares
                WHERE to_agent = ?
            """, (agent_name,))

            shares = cursor.fetchall()

            print(f"[OK] Found {len(shares)} memory shares")

            for share_id, from_agent, memory_id, access_level, expires_at, created_at in shares:
                print(f"  - Share {share_id}: Memory {memory_id} from {from_agent} ({access_level})")

            return shares
        except Exception as e:
            print(f"[ERROR] Failed to retrieve shares: {e}")
            return []
        finally:
            conn.close()

    def list_collaborative_spaces(self, agent_name):
        """List all collaborative spaces an agent has access to"""
        print(f"\n[INFO] Listing collaborative spaces for {agent_name}...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, space_name, created_by, created_at, members
                FROM collaborative_spaces
                WHERE members LIKE ?
            """, (f'%"{agent_name}"%',))

            spaces = cursor.fetchall()

            print(f"[OK] Found {len(spaces)} collaborative spaces")

            for space_id, space_name, created_by, created_at, members in spaces:
                members_list = json.loads(members)
                print(f"  - Space {space_id}: {space_name}")
                print(f"    Creator: {created_by}")
                print(f"    Members: {len(members_list)}")

            return spaces
        except Exception as e:
            print(f"[ERROR] Failed to list spaces: {e}")
            return []
        finally:
            conn.close()

    def create_agent_memory_sync(self, agent_a, agent_b, shared_memory_id):
        """Create a memory synchronization between two agents"""
        print(f"\n[INFO] Creating memory sync between {agent_a} and {agent_b}...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Share memory from A to B
            share_a = cursor.execute("""
                INSERT INTO agent_memory_shares (from_agent, to_agent, memory_id, access_level)
                VALUES (?, ?, ?, ?)
            """, (agent_a, agent_b, shared_memory_id, "read"))

            # Share memory from B to A
            share_b = cursor.execute("""
                INSERT INTO agent_memory_shares (from_agent, to_agent, memory_id, access_level)
                VALUES (?, ?, ?, ?)
            """, (agent_b, agent_a, shared_memory_id, "read"))

            conn.commit()

            print(f"[OK] Memory sync created")
            print(f"  - Memory {shared_memory_id} shared between {agent_a} and {agent_b}")

            return True
        except Exception as e:
            print(f"[ERROR] Failed to create memory sync: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    collaboration = AgentCollaboration()

    print("="*60)
    print("MULTI-AGENT COLLABORATION - NOVA MEMORY v2.0")
    print("="*60)

    # Create collaborative space
    space_id = collaboration.create_collaborative_space(
        space_name="Nova Agents",
        creator="nexus",
        members=["nexus", "sentinel"],
        permissions={"read": True, "write": True}
    )

    # Share memory between agents
    if space_id:
        share_id = collaboration.share_memory_with_agent(
            from_agent="nexus",
            to_agent="sentinel",
            memory_id=1,
            access_level="read"
        )

        # List spaces
        spaces = collaboration.list_collaborative_spaces("sentinel")

        # List shares
        shares = collaboration.get_agent_memory_shares("sentinel")

    print("\n" + "="*60)
    print("COLLABORATION TEST COMPLETE")
    print("="*60)
