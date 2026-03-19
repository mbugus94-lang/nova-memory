"""
Tests for core/agent_registry.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_registry import AgentRegistry, AgentMetadata


class TestAgentMetadata(unittest.TestCase):

    def test_create_metadata(self):
        meta = AgentMetadata(
            agent_id="agent-1",
            name="Test Agent",
            version="1.0.0",
            description="A test agent",
            capabilities=["search", "store"],
            tags=["test"],
        )
        self.assertEqual(meta.agent_id, "agent-1")
        self.assertEqual(meta.status, "active")
        self.assertIsNotNone(meta.registered_at)

    def test_to_dict(self):
        meta = AgentMetadata(agent_id="a1", name="Agent", version="1.0")
        d = meta.to_dict()
        self.assertEqual(d["agent_id"], "a1")
        self.assertIn("capabilities", d)

    def test_from_dict(self):
        data = {"agent_id": "a1", "name": "Agent", "version": "1.0", "description": "test"}
        meta = AgentMetadata.from_dict(data)
        self.assertEqual(meta.agent_id, "a1")

    def test_is_alive(self):
        meta = AgentMetadata(agent_id="a1", name="Agent", version="1.0")
        self.assertTrue(meta.is_alive(timeout_seconds=300))


class TestAgentRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = AgentRegistry()

    def test_register_agent(self):
        meta = AgentMetadata(agent_id="a1", name="Agent 1", version="1.0", capabilities=["search"])
        result = self.registry.register(meta)
        self.assertTrue(result)

    def test_get_agent(self):
        meta = AgentMetadata(agent_id="a1", name="Agent 1", version="1.0")
        self.registry.register(meta)
        agent = self.registry.get_agent("a1")
        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, "Agent 1")

    def test_get_nonexistent_agent(self):
        agent = self.registry.get_agent("ghost")
        self.assertIsNone(agent)

    def test_unregister_agent(self):
        meta = AgentMetadata(agent_id="a1", name="Agent 1", version="1.0", capabilities=["search"])
        self.registry.register(meta)
        result = self.registry.unregister("a1")
        self.assertTrue(result)
        self.assertIsNone(self.registry.get_agent("a1"))

    def test_heartbeat(self):
        meta = AgentMetadata(agent_id="a1", name="Agent 1", version="1.0")
        self.registry.register(meta)
        result = self.registry.heartbeat("a1")
        self.assertTrue(result)

    def test_heartbeat_nonexistent(self):
        result = self.registry.heartbeat("ghost")
        self.assertFalse(result)

    def test_find_by_capability(self):
        self.registry.register(AgentMetadata(
            agent_id="a1", name="Search Agent", version="1.0", capabilities=["search"]
        ))
        self.registry.register(AgentMetadata(
            agent_id="a2", name="Store Agent", version="1.0", capabilities=["store"]
        ))
        results = self.registry.find_by_capability("search")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].agent_id, "a1")

    def test_find_by_tag(self):
        self.registry.register(AgentMetadata(
            agent_id="a1", name="A1", version="1.0", tags=["ml"]
        ))
        results = self.registry.find_by_tag("ml")
        self.assertEqual(len(results), 1)

    def test_search_by_query(self):
        self.registry.register(AgentMetadata(
            agent_id="a1", name="Memory Agent", version="1.0", description="Handles memory"
        ))
        results = self.registry.search(query="memory")
        self.assertEqual(len(results), 1)

    def test_get_stats(self):
        self.registry.register(AgentMetadata(agent_id="a1", name="A1", version="1.0", capabilities=["c1"]))
        stats = self.registry.get_stats()
        self.assertEqual(stats["total_agents"], 1)
        self.assertEqual(stats["total_capabilities"], 1)

    def test_update_status(self):
        self.registry.register(AgentMetadata(agent_id="a1", name="A1", version="1.0"))
        result = self.registry.update_status("a1", "paused")
        self.assertTrue(result)
        self.assertEqual(self.registry.get_agent("a1").status, "paused")

    def test_add_remove_capability(self):
        meta = AgentMetadata(agent_id="a1", name="A1", version="1.0")
        self.registry.register(meta)
        self.registry.add_capability("a1", "new_cap")
        self.assertIn("new_cap", self.registry.get_agent("a1").capabilities)
        self.registry.remove_capability("a1", "new_cap")
        self.assertNotIn("new_cap", self.registry.get_agent("a1").capabilities)


if __name__ == "__main__":
    unittest.main(verbosity=2)
