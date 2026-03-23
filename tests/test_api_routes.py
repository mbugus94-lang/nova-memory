"""
Tests for API server routes — auth, memories, agents, collaboration, health.
"""

import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment before importing the app
os.environ["ENVIRONMENT"] = "development"
os.environ["NOVA_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["NOVA_ADMIN_USERNAME"] = "testadmin"
os.environ["NOVA_ADMIN_PASSWORD"] = "testpass123"
os.environ["NOVA_AGENT_SECRET"] = "test-agent-secret"

# Use a temp database for tests
_test_fd, _test_db = tempfile.mkstemp(suffix=".db")
os.close(_test_fd)
os.unlink(_test_db)
os.environ["DATABASE_PATH"] = _test_db

from fastapi.testclient import TestClient
from core.migrations import run_migrations
from core.db import get_db_path

# Run migrations on the test database before any tests
run_migrations(get_db_path())


def _get_client():
    """Create a fresh test client."""
    from api.server import app
    return TestClient(app)


def _auth_headers(client):
    """Get auth headers by logging in as admin."""
    resp = client.post("/auth/login", data={
        "username": "testadmin",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoint(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = _get_client()

    def test_root_endpoint(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("name", data)
        self.assertIn("version", data)

    def test_health_endpoint(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")


class TestAuthEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = _get_client()

    def test_login_success(self):
        resp = self.client.post("/auth/login", data={
            "username": "testadmin",
            "password": "testpass123",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_login_wrong_password(self):
        resp = self.client.post("/auth/login", data={
            "username": "testadmin",
            "password": "wrong",
        })
        self.assertEqual(resp.status_code, 401)

    def test_agent_login(self):
        resp = self.client.post("/auth/login", data={
            "username": "agent-1",
            "password": "test-agent-secret",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)


class TestMemoryEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = _get_client()
        cls.headers = _auth_headers(cls.client)

    def test_create_memory(self):
        resp = self.client.post("/memories", json={
            "content": "Test memory content for unit test",
            "tags": ["test", "unit"],
        }, headers=self.headers)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("id", data)
        self.assertEqual(data["content"], "Test memory content for unit test")

    def test_create_memory_unauthenticated(self):
        resp = self.client.post("/memories", json={
            "content": "This should fail",
        })
        self.assertEqual(resp.status_code, 401)

    def test_get_memory(self):
        # Create a memory first
        create_resp = self.client.post("/memories", json={
            "content": "Memory to retrieve",
        }, headers=self.headers)
        mid = create_resp.json()["id"]

        resp = self.client.get(f"/memories/{mid}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["content"], "Memory to retrieve")

    def test_get_nonexistent_memory(self):
        resp = self.client.get("/memories/nonexistent-id")
        self.assertEqual(resp.status_code, 404)

    def test_list_memories(self):
        resp = self.client.get("/memories")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)

    def test_search_memories(self):
        self.client.post("/memories", json={
            "content": "Unique searchable content about Python",
            "tags": ["python"],
        }, headers=self.headers)
        resp = self.client.get("/memories?query=Python")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(len(data), 0)

    def test_update_memory(self):
        create_resp = self.client.post("/memories", json={
            "content": "Original content",
        }, headers=self.headers)
        mid = create_resp.json()["id"]

        resp = self.client.patch(f"/memories/{mid}", json={
            "content": "Updated content",
        }, headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["content"], "Updated content")

    def test_delete_memory(self):
        create_resp = self.client.post("/memories", json={
            "content": "To be deleted",
        }, headers=self.headers)
        mid = create_resp.json()["id"]

        resp = self.client.delete(f"/memories/{mid}", headers=self.headers)
        self.assertEqual(resp.status_code, 204)

    def test_context_endpoint(self):
        self.client.post("/memories", json={
            "content": "Context retrieval test about AI agents",
        }, headers=self.headers)
        resp = self.client.post("/memories/context", json={
            "query": "AI agents",
            "limit": 5,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("context", data)
        self.assertIn("sources", data)


class TestAgentEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = _get_client()
        cls.headers = _auth_headers(cls.client)

    def test_create_agent(self):
        resp = self.client.post("/agents", json={
            "id": "test-agent-1",
            "name": "Test Agent",
            "role": "assistant",
            "capabilities": ["search", "store"],
        }, headers=self.headers)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["id"], "test-agent-1")
        self.assertEqual(data["status"], "active")

    def test_duplicate_agent(self):
        self.client.post("/agents", json={
            "id": "dup-agent",
            "name": "Dup",
            "role": "test",
        }, headers=self.headers)
        resp = self.client.post("/agents", json={
            "id": "dup-agent",
            "name": "Dup 2",
            "role": "test",
        }, headers=self.headers)
        self.assertEqual(resp.status_code, 409)

    def test_list_agents(self):
        resp = self.client.get("/agents")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)


class TestInteractionEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = _get_client()

    def test_create_interaction(self):
        resp = self.client.post("/interactions", json={
            "agent_id": "test-agent",
            "user_message": "Hello",
            "agent_response": "Hi there",
            "user_feedback": "positive",
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("id", data)
        self.assertEqual(data["user_message"], "Hello")

    def test_list_interactions(self):
        resp = self.client.get("/interactions")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)


class TestCollaborationEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = _get_client()
        cls.headers = _auth_headers(cls.client)

    def test_create_space(self):
        resp = self.client.post("/collaboration/spaces", json={
            "space_name": "Test Space",
            "creator": "agent-1",
            "members": ["agent-2"],
        }, headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("space_id", data)

    def test_list_spaces(self):
        resp = self.client.get("/collaboration/spaces?agent_id=agent-1")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)


class TestWorkflowEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = _get_client()

    def test_list_workflows(self):
        resp = self.client.get("/workflows")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("workflows", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
