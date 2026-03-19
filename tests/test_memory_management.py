"""
Tests for core/memory_management.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory_management import (
    RetentionPolicy, MemoryGarbageCollector, ConflictResolver, MemoryOptimizer,
    detect_duplicates,
)


class TestRetentionPolicy(unittest.TestCase):

    def test_defaults(self):
        policy = RetentionPolicy()
        self.assertEqual(policy.default_ttl_days, 365)
        self.assertEqual(policy.archive_after_days, 180)
        self.assertEqual(policy.delete_after_days, 730)

    def test_custom_policy(self):
        policy = RetentionPolicy(delete_after_days=30, archive_after_days=7)
        self.assertEqual(policy.delete_after_days, 30)


class TestMemoryGarbageCollector(unittest.TestCase):

    def test_analyze_recent_memory_kept(self):
        gc = MemoryGarbageCollector()
        memory = {
            "id": "m1",
            "created_at": "2026-03-01T00:00:00",
            "access_count": 5,
        }
        analysis = gc.analyze_memory(memory)
        self.assertEqual(analysis["recommendation"], "keep")

    def test_analyze_old_memory_delete(self):
        policy = RetentionPolicy(delete_after_days=1, min_access_count=10)
        gc = MemoryGarbageCollector(retention_policy=policy)
        memory = {
            "id": "m1",
            "created_at": "2020-01-01T00:00:00",
            "access_count": 1,
        }
        analysis = gc.analyze_memory(memory)
        self.assertEqual(analysis["recommendation"], "delete")

    def test_collect_garbage(self):
        from datetime import datetime, timedelta, timezone
        old_date = (datetime.now(timezone.utc) - timedelta(days=800)).isoformat()

        policy = RetentionPolicy(delete_after_days=1, min_access_count=1, archive_after_days=1, min_size_bytes=100000)
        gc = MemoryGarbageCollector(retention_policy=policy)

        memories = [
            {"id": "old", "created_at": old_date, "access_count": 0},
            {"id": "recent", "created_at": "2026-03-01T00:00:00", "access_count": 5},
        ]

        deleted = []
        def delete_handler(m):
            deleted.append(m["id"])

        stats = gc.collect_garbage(memories, delete_handler=delete_handler)
        self.assertEqual(stats["deleted"], 1)
        self.assertEqual(stats["kept"], 1)

    def test_export_archived(self):
        import json
        gc = MemoryGarbageCollector()
        gc.archived.append({"id": "a1"})
        exported = json.loads(gc.export_archived())
        self.assertEqual(len(exported), 1)


class TestConflictResolver(unittest.TestCase):

    def test_last_write_wins_incoming(self):
        current = {"content": "old", "updated_at": "2026-01-01T00:00:00"}
        incoming = {"content": "new", "updated_at": "2026-03-01T00:00:00"}
        result = ConflictResolver.resolve_last_write_wins(current, incoming)
        self.assertEqual(result["content"], "new")

    def test_last_write_wins_current(self):
        current = {"content": "old", "updated_at": "2026-03-01T00:00:00"}
        incoming = {"content": "new", "updated_at": "2026-01-01T00:00:00"}
        result = ConflictResolver.resolve_last_write_wins(current, incoming)
        self.assertEqual(result["content"], "old")

    def test_merge_tags(self):
        current = {"content": "x", "tags": ["a", "b"]}
        incoming = {"content": "y", "tags": ["b", "c"]}
        result = ConflictResolver.resolve_merge(current, incoming)
        self.assertEqual(set(result["tags"]), {"a", "b", "c"})

    def test_merge_metadata(self):
        current = {"metadata": {"a": 1, "b": 2}}
        incoming = {"metadata": {"b": 3, "c": 4}}
        result = ConflictResolver.resolve_merge(current, incoming)
        self.assertEqual(result["metadata"]["a"], 1)
        self.assertEqual(result["metadata"]["b"], 3)
        self.assertEqual(result["metadata"]["c"], 4)

    def test_detect_conflict(self):
        v1 = {"content": "A", "updated_at": "2026-01-01T00:00:00"}
        v2 = {"content": "B", "updated_at": "2026-02-01T00:00:00"}
        self.assertTrue(ConflictResolver.detect_conflict(v1, v2))

    def test_no_conflict_same_content(self):
        v1 = {"content": "A", "updated_at": "2026-01-01T00:00:00"}
        v2 = {"content": "A", "updated_at": "2026-02-01T00:00:00"}
        self.assertFalse(ConflictResolver.detect_conflict(v1, v2))

    def test_custom_resolver(self):
        current = {"content": "old"}
        incoming = {"content": "new"}
        result = ConflictResolver.resolve_custom(current, incoming, lambda c, i: i)
        self.assertEqual(result["content"], "new")


class TestMemoryOptimizer(unittest.TestCase):

    def test_estimate_size(self):
        size = MemoryOptimizer.estimate_size({"content": "hello"})
        self.assertGreater(size, 0)

    def test_compression_ratio(self):
        ratio = MemoryOptimizer.calculate_compression_ratio(1000, 500)
        self.assertEqual(ratio, 50.0)

    def test_optimize_memory_removes_underscore_fields(self):
        memory = {"content": "test", "_temp": "value"}
        result = MemoryOptimizer.optimize_memory(memory)
        self.assertNotIn("_temp", result)


class TestDetectDuplicates(unittest.TestCase):

    def test_detects_similar(self):
        memories = [
            {"id": "1", "content": "The quick brown fox"},
            {"id": "2", "content": "The quick brown fox"},
        ]
        dupes = detect_duplicates(memories, threshold=0.9)
        self.assertGreater(len(dupes), 0)

    def test_no_duplicates_for_different(self):
        memories = [
            {"id": "1", "content": "completely different content here"},
            {"id": "2", "content": "xyz"},
        ]
        dupes = detect_duplicates(memories, threshold=0.9)
        self.assertEqual(len(dupes), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
