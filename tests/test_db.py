"""
Tests for core/migrations.py — migration system.
"""

import os
import sys
import sqlite3
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.migrations import run_migrations, MIGRATIONS


class TestMigrations(unittest.TestCase):

    def setUp(self):
        self.fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        os.unlink(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_run_migrations_creates_tables(self):
        count = run_migrations(self.db_path)
        self.assertGreater(count, 0)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verify core tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        self.assertIn("memories", tables)
        self.assertIn("memory_versions", tables)
        self.assertIn("collaborative_spaces", tables)
        self.assertIn("agents", tables)
        self.assertIn("interactions", tables)
        self.assertIn("memory_kv", tables)
        self.assertIn("_migrations", tables)

    def test_migrations_are_idempotent(self):
        count1 = run_migrations(self.db_path)
        count2 = run_migrations(self.db_path)
        self.assertGreater(count1, 0)
        self.assertEqual(count2, 0)

    def test_migration_tracking(self):
        run_migrations(self.db_path)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT version, description FROM _migrations ORDER BY version")
        rows = cursor.fetchall()
        conn.close()
        self.assertEqual(len(rows), len(MIGRATIONS))


class TestDBModule(unittest.TestCase):

    def test_resolve_db_path_default(self):
        from core.db import resolve_db_path
        path = resolve_db_path()
        self.assertIsInstance(path, str)
        self.assertTrue(path.endswith(".db"))

    def test_get_conn_context_manager(self):
        from core.db import get_conn
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(path)

        try:
            with get_conn(path) as conn:
                conn.execute("CREATE TABLE test (id INTEGER)")
                conn.commit()

            with get_conn(path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                self.assertIn("test", tables)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_db_exists(self):
        from core.db import db_exists
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(path)
        self.assertFalse(db_exists(path))

        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.commit()
        conn.close()
        self.assertTrue(db_exists(path))
        os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
