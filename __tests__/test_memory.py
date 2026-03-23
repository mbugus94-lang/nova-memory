"""Memory management tests for Nova Memory API."""
import pytest
from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


def test_create_memory():
    """Test creating a memory entry."""
    payload = {
        "agent_id": "test-agent-001",
        "key": "user_preference",
        "value": {"theme": "dark"},
        "scope": "global",
        "ttl_seconds": 3600
    }
    response = client.post("/api/v2/memory", json=payload)
    assert response.status_code in [200, 201]


def test_get_memory():
    """Test retrieving a memory entry."""
    # First create a memory
    payload = {
        "agent_id": "test-agent-002",
        "key": "test_key",
        "value": {"data": "test"},
        "scope": "global"
    }
    client.post("/api/v2/memory", json=payload)
    
    # Then retrieve it
    response = client.get("/api/v2/memory", params={
        "agent_id": "test-agent-002",
        "key": "test_key"
    })
    assert response.status_code == 200


def test_memory_not_found():
    """Test retrieving a non-existent memory."""
    response = client.get("/api/v2/memory", params={
        "agent_id": "nonexistent",
        "key": "nonexistent"
    })
    assert response.status_code == 404
