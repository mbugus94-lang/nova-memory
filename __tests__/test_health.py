"""Health check tests for Nova Memory API."""
import pytest
from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert "version" in data
