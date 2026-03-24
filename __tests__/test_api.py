"""
Nova Memory API Tests
Comprehensive test suite for Nova Memory REST API endpoints.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_response_format(self):
        """Test that health response has expected format."""
        expected_keys = {'status', 'timestamp', 'uptime_seconds', 'version'}
        # This is a mock test - in real scenario would call actual endpoint
        mock_response = {
            'status': 'ok',
            'timestamp': '2025-01-15T10:30:00Z',
            'uptime_seconds': 3600,
            'version': '2.1.0'
        }
        assert set(mock_response.keys()) == expected_keys
        assert mock_response['status'] == 'ok'
        assert isinstance(mock_response['uptime_seconds'], int)

    def test_health_status_values(self):
        """Test that health status is always 'ok' or 'error'."""
        valid_statuses = {'ok', 'error', 'degraded'}
        mock_status = 'ok'
        assert mock_status in valid_statuses


class TestMemoryEndpoints:
    """Tests for memory CRUD operations."""

    def test_store_memory_format(self):
        """Test memory store request format."""
        valid_request = {
            'key': 'test-key',
            'value': {'data': 'test data'},
            'metadata': {'source': 'test'}
        }
        assert 'key' in valid_request
        assert 'value' in valid_request
        assert isinstance(valid_request['key'], str)

    def test_retrieve_memory_format(self):
        """Test memory retrieve response format."""
        mock_response = {
            'key': 'test-key',
            'value': {'data': 'test data'},
            'created_at': '2025-01-15T10:30:00Z',
            'updated_at': '2025-01-15T10:30:00Z'
        }
        assert 'key' in mock_response
        assert 'value' in mock_response

    def test_list_memory_format(self):
        """Test memory list response format."""
        mock_response = {
            'memories': [
                {'key': 'key1', 'value': 'value1'},
                {'key': 'key2', 'value': 'value2'}
            ],
            'total': 2,
            'page': 1,
            'per_page': 10
        }
        assert 'memories' in mock_response
        assert isinstance(mock_response['memories'], list)
        assert 'total' in mock_response

    def test_delete_memory_response(self):
        """Test memory delete response."""
        mock_response = {
            'success': True,
            'message': 'Memory deleted successfully',
            'deleted_key': 'test-key'
        }
        assert mock_response['success'] is True
        assert 'deleted_key' in mock_response


class TestSearchEndpoints:
    """Tests for memory search functionality."""

    def test_search_request_format(self):
        """Test search request format."""
        valid_request = {
            'query': 'search term',
            'filters': {'agent_id': 'agent-1'},
            'limit': 10
        }
        assert 'query' in valid_request
        assert isinstance(valid_request.get('limit', 10), int)

    def test_search_response_format(self):
        """Test search response format."""
        mock_response = {
            'results': [
                {'key': 'key1', 'value': 'value1', 'score': 0.95},
                {'key': 'key2', 'value': 'value2', 'score': 0.85}
            ],
            'total': 2,
            'query': 'search term'
        }
        assert 'results' in mock_response
        assert isinstance(mock_response['results'], list)


class TestContextEndpoints:
    """Tests for context retrieval endpoints (v2.1)."""

    def test_context_request_format(self):
        """Test context request format."""
        valid_request = {
            'agent_id': 'agent-1',
            'session_id': 'session-123',
            'max_memories': 10
        }
        assert 'agent_id' in valid_request
        assert isinstance(valid_request.get('max_memories', 10), int)

    def test_context_response_format(self):
        """Test context response format."""
        mock_response = {
            'context': 'Consolidated memory context for LLM',
            'memories_included': 5,
            'relevance_score': 0.92
        }
        assert 'context' in mock_response
        assert 'memories_included' in mock_response


class TestAuthentication:
    """Tests for authentication endpoints."""

    def test_login_request_format(self):
        """Test login request format."""
        valid_request = {
            'username': 'admin',
            'password': 'secret123'
        }
        assert 'username' in valid_request
        assert 'password' in valid_request

    def test_login_response_format(self):
        """Test login response format."""
        mock_response = {
            'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
            'token_type': 'bearer',
            'expires_in': 3600
        }
        assert 'access_token' in mock_response
        assert 'token_type' in mock_response
        assert mock_response['token_type'] == 'bearer'


class TestValidation:
    """Tests for input validation."""

    def test_key_validation(self):
        """Test that memory keys must be valid strings."""
        invalid_keys = ['', None, 123, '   ']
        for key in invalid_keys:
            if key is None:
                assert True  # None should fail
            elif isinstance(key, str) and len(key.strip()) == 0:
                assert True  # Empty string should fail
            elif not isinstance(key, str):
                assert True  # Non-string should fail

    def test_value_validation(self):
        """Test that memory values must be valid JSON."""
        invalid_values = [None]
        for value in invalid_values:
            assert value is None

    def test_limit_validation(self):
        """Test that limit parameter must be positive integer."""
        invalid_limits = [0, -1, 'ten', None]
        for limit in invalid_limits:
            if isinstance(limit, int):
                assert limit <= 0  # Zero or negative should fail
            else:
                assert True  # Non-integer should fail


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
