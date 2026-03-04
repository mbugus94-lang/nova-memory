#!/usr/bin/env python3
"""
Enhanced Memory Storage for Nova Memory System v2.0
"""

import sqlite3
import json
import hashlib
import zlib
from datetime import datetime
from pathlib import Path

class EnhancedMemoryStorage:
    """Enhanced memory storage with versioning and compression"""

    def __init__(self, db_path="nova_memory_v2.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database with enhanced schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create enhanced memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER DEFAULT 1,
                content TEXT NOT NULL,
                compressed BOOLEAN DEFAULT 0,
                compressed_size INTEGER DEFAULT 0,
                original_size INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                tags TEXT,
                author TEXT,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            )
        """)

        # Create memory version table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                version INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        """)

        # Create backup table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_name TEXT NOT NULL,
                backup_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                size_bytes INTEGER
            )
        """)

        conn.commit()
        conn.close()

        print(f"[OK] Enhanced database initialized: {self.db_path}")

    def add_memory(self, content, metadata=None, tags=None, author=None):
        """Add a new memory with versioning"""
        print(f"\n[INFO] Adding memory...")

        # Calculate sizes
        original_size = len(content.encode('utf-8'))

        # Compress content
        compressed = zlib.compress(content.encode('utf-8'))
        compressed_size = len(compressed)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert main memory
            cursor.execute("""
                INSERT INTO memories (content, compressed, compressed_size, original_size, metadata, tags, author)
                VALUES (?, 1, ?, ?, ?, ?, ?)
            """, (
                compressed.hex(),
                compressed_size,
                original_size,
                json.dumps(metadata) if metadata else None,
                json.dumps(tags) if tags else None,
                author
            ))

            memory_id = cursor.lastrowid

            # Insert version 1
            cursor.execute("""
                INSERT INTO memory_versions (memory_id, version, content)
                VALUES (?, 1, ?)
            """, (memory_id, content))

            conn.commit()

            print(f"[OK] Memory added with ID: {memory_id}")
            print(f"  - Original size: {original_size} bytes")
            print(f"  - Compressed size: {compressed_size} bytes")
            print(f"  - Compression ratio: {(compressed_size/original_size)*100:.2f}%")

            return memory_id
        except Exception as e:
            print(f"[ERROR] Failed to add memory: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def get_memory(self, memory_id):
        """Get memory with decompression"""
        print(f"\n[INFO] Retrieving memory {memory_id}...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT content, compressed, metadata, tags, author, access_count, last_accessed
                FROM memories
                WHERE id = ?
            """, (memory_id,))

            row = cursor.fetchone()

            if row:
                compressed_hex, compressed, metadata, tags, author, access_count, last_accessed = row

                # Decompress if needed
                if compressed:
                    content_bytes = bytes.fromhex(compressed_hex)
                    content = zlib.decompress(content_bytes).decode('utf-8')
                else:
                    content = compressed_hex

                print(f"[OK] Memory retrieved successfully")

                return {
                    'id': memory_id,
                    'content': content,
                    'metadata': json.loads(metadata) if metadata else None,
                    'tags': json.loads(tags) if tags else None,
                    'author': author,
                    'access_count': access_count,
                    'last_accessed': last_accessed
                }
            else:
                print(f"[ERROR] Memory not found: {memory_id}")
                return None
        except Exception as e:
            print(f"[ERROR] Failed to retrieve memory: {e}")
            return None
        finally:
            conn.close()

    def create_backup(self, backup_name):
        """Create a full database backup"""
        print(f"\n[INFO] Creating backup: {backup_name}...")

        try:
            # Read database file
            with open(self.db_path, 'rb') as f:
                backup_data = f.read()

            size_bytes = len(backup_data)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO backups (backup_name, backup_data, size_bytes)
                VALUES (?, ?, ?)
            """, (backup_name, backup_data.hex(), size_bytes))

            backup_id = cursor.lastrowid
            conn.commit()
            conn.close()

            print(f"[OK] Backup created with ID: {backup_id}")
            print(f"  - Size: {size_bytes:,} bytes ({size_bytes/1024/1024:.2f} MB)")

            return backup_id
        except Exception as e:
            print(f"[ERROR] Failed to create backup: {e}")
            return None

    def restore_backup(self, backup_id):
        """Restore from backup"""
        print(f"\n[INFO] Restoring backup {backup_id}...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT backup_data
                FROM backups
                WHERE id = ?
            """, (backup_id,))

            row = cursor.fetchone()

            if row:
                backup_data_hex = row[0]
                backup_data = bytes.fromhex(backup_data_hex)

                # Write backup to database file
                with open(self.db_path, 'wb') as f:
                    f.write(backup_data)

                print(f"[OK] Backup restored successfully")
                return True
            else:
                print(f"[ERROR] Backup not found: {backup_id}")
                return False
        except Exception as e:
            print(f"[ERROR] Failed to restore backup: {e}")
            return False
        finally:
            conn.close()

    def get_memory_stats(self):
        """Get memory statistics"""
        print(f"\n[INFO] Retrieving memory statistics...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Total memories
            cursor.execute("SELECT COUNT(*) FROM memories")
            total_memories = cursor.fetchone()[0]

            # Total storage
            cursor.execute("SELECT SUM(original_size) FROM memories")
            total_original_size = cursor.fetchone()[0] or 0

            # Total compressed storage
            cursor.execute("SELECT SUM(compressed_size) FROM memories")
            total_compressed_size = cursor.fetchone()[0] or 0

            # Storage saved
            storage_saved = total_original_size - total_compressed_size
            compression_ratio = (storage_saved / total_original_size * 100) if total_original_size > 0 else 0

            # Most accessed memories
            cursor.execute("""
                SELECT id, access_count
                FROM memories
                ORDER BY access_count DESC
                LIMIT 5
            """)
            top_memories = cursor.fetchall()

            print(f"[OK] Memory statistics:")
            print(f"  - Total memories: {total_memories}")
            print(f"  - Total storage: {total_original_size:,} bytes ({total_original_size/1024/1024:.2f} MB)")
            print(f"  - Compressed storage: {total_compressed_size:,} bytes ({total_compressed_size/1024/1024:.2f} MB)")
            print(f"  - Storage saved: {storage_saved:,} bytes ({storage_saved/1024/1024:.2f} MB)")
            print(f"  - Compression ratio: {compression_ratio:.2f}%")

            if top_memories:
                print(f"  - Top memories:")
                for memory_id, access_count in top_memories:
                    print(f"    * Memory {memory_id}: {access_count} accesses")

            return {
                'total_memories': total_memories,
                'total_storage': total_original_size,
                'compressed_storage': total_compressed_size,
                'storage_saved': storage_saved,
                'compression_ratio': compression_ratio,
                'top_memories': top_memories
            }
        except Exception as e:
            print(f"[ERROR] Failed to get statistics: {e}")
            return None
        finally:
            conn.close()

if __name__ == "__main__":
    storage = EnhancedMemoryStorage()

    print("="*60)
    print("ENHANCED MEMORY STORAGE - NOVA MEMORY v2.0")
    print("="*60)

    # Test adding memory
    memory_id = storage.add_memory(
        content="This is a test memory for Nova Memory System v2.0",
        metadata={"type": "test", "author": "Nova"},
        tags=["test", "v2.0", "demo"]
    )

    # Test getting memory
    if memory_id:
        memory = storage.get_memory(memory_id)
        if memory:
            print(f"\n  Retrieved memory: {memory['content'][:50]}...")

    # Test backup
    backup_id = storage.create_backup("test_backup")

    # Test statistics
    stats = storage.get_memory_stats()

    print("\n" + "="*60)
    print("ENHANCED STORAGE TEST COMPLETE")
    print("="*60)
