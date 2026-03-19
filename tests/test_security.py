"""
Tests for core/security.py — JWT, RBAC, encryption, audit logging.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security import (
    JWTManager, Role, Permission, ROLE_PERMISSIONS,
    EncryptionManager, AuditLog, AttributeManager,
    hash_password, verify_password,
)


class TestJWTManager(unittest.TestCase):

    def setUp(self):
        self.jwt = JWTManager(secret_key="test-secret-key-12345", expiration_hours=1)

    def test_create_and_verify_token(self):
        token = self.jwt.create_token("agent-1", Role.AGENT)
        self.assertIsNotNone(token)
        payload = self.jwt.verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["agent_id"], "agent-1")
        self.assertEqual(payload["role"], Role.AGENT.value)

    def test_expired_token_returns_none(self):
        jwt_mgr = JWTManager(secret_key="test-secret-key-12345", expiration_hours=0)
        token = jwt_mgr.create_token("agent-1", Role.AGENT)
        # Token with 0-hour expiration should expire immediately
        import time
        time.sleep(1)
        payload = jwt_mgr.verify_token(token)
        self.assertIsNone(payload)

    def test_invalid_token_returns_none(self):
        payload = self.jwt.verify_token("invalid.token.here")
        self.assertIsNone(payload)

    def test_has_permission_admin_all(self):
        token = self.jwt.create_token("admin", Role.ADMIN)
        self.assertTrue(self.jwt.has_permission(token, Permission.CREATE_MEMORY))
        self.assertTrue(self.jwt.has_permission(token, Permission.DELETE_MEMORY))
        self.assertTrue(self.jwt.has_permission(token, Permission.ADMIN_ALL))

    def test_has_permission_agent_restricted(self):
        token = self.jwt.create_token("agent-1", Role.AGENT)
        self.assertTrue(self.jwt.has_permission(token, Permission.CREATE_MEMORY))
        self.assertTrue(self.jwt.has_permission(token, Permission.READ_MEMORY))
        self.assertFalse(self.jwt.has_permission(token, Permission.DELETE_MEMORY))
        self.assertFalse(self.jwt.has_permission(token, Permission.ADMIN_ALL))

    def test_has_permission_viewer_read_only(self):
        token = self.jwt.create_token("viewer-1", Role.VIEWER)
        self.assertTrue(self.jwt.has_permission(token, Permission.READ_MEMORY))
        self.assertFalse(self.jwt.has_permission(token, Permission.CREATE_MEMORY))

    def test_custom_permissions(self):
        token = self.jwt.create_token(
            "custom-agent", Role.AGENT,
            permissions=[Permission.CREATE_MEMORY, Permission.DELETE_MEMORY],
        )
        self.assertTrue(self.jwt.has_permission(token, Permission.DELETE_MEMORY))

    def test_role_permissions_mapping(self):
        for role in Role:
            self.assertIn(role, ROLE_PERMISSIONS)


class TestPasswordHashing(unittest.TestCase):

    def test_hash_and_verify(self):
        pw_hash, salt = hash_password("my_password")
        self.assertTrue(verify_password("my_password", pw_hash, salt))
        self.assertFalse(verify_password("wrong_password", pw_hash, salt))

    def test_different_salts(self):
        pw_hash1, salt1 = hash_password("password")
        pw_hash2, salt2 = hash_password("password")
        self.assertNotEqual(salt1, salt2)
        self.assertNotEqual(pw_hash1, pw_hash2)


class TestEncryptionManager(unittest.TestCase):

    def test_encrypt_and_decrypt(self):
        enc = EncryptionManager()
        plaintext = "secret memory content"
        ciphertext = enc.encrypt(plaintext)
        self.assertNotEqual(ciphertext, plaintext)
        decrypted = enc.decrypt(ciphertext)
        self.assertEqual(decrypted, plaintext)

    def test_with_provided_key(self):
        key = EncryptionManager().encryption_key
        enc = EncryptionManager(key=key.decode())
        plaintext = "test content"
        self.assertEqual(enc.decrypt(enc.encrypt(plaintext)), plaintext)

    def test_unavailable_returns_plain(self):
        enc = EncryptionManager.__new__(EncryptionManager)
        enc.available = False
        self.assertEqual(enc.encrypt("hello"), "hello")
        self.assertEqual(enc.decrypt("hello"), "hello")


class TestAuditLog(unittest.TestCase):

    def test_log_and_retrieve(self):
        log = AuditLog()
        log.log("create", "agent-1", "memory-001")
        log.log("read", "agent-2", "memory-001")
        log.log("delete", "agent-1", "memory-002")

        all_logs = log.get_logs()
        self.assertEqual(len(all_logs), 3)

    def test_filter_by_actor(self):
        log = AuditLog()
        log.log("create", "agent-1", "memory-001")
        log.log("read", "agent-2", "memory-001")

        agent1_logs = log.get_logs(actor="agent-1")
        self.assertEqual(len(agent1_logs), 1)
        self.assertEqual(agent1_logs[0]["actor"], "agent-1")

    def test_filter_by_action(self):
        log = AuditLog()
        log.log("create", "agent-1", "m1")
        log.log("delete", "agent-1", "m2")

        create_logs = log.get_logs(action="create")
        self.assertEqual(len(create_logs), 1)

    def test_max_entries_bound(self):
        log = AuditLog(max_entries=5)
        for i in range(10):
            log.log("test", "agent", f"resource-{i}")
        self.assertEqual(len(log.entries), 5)

    def test_export_json(self):
        import json
        log = AuditLog()
        log.log("create", "agent-1", "m1")
        exported = json.loads(log.export())
        self.assertEqual(len(exported), 1)


class TestAttributeManager(unittest.TestCase):

    def test_set_and_get_attributes(self):
        mgr = AttributeManager()
        mgr.set_attributes("agent-1", "resource-1", {"department": "engineering"})
        attrs = mgr.get_attributes("agent-1", "resource-1")
        self.assertEqual(attrs["department"], "engineering")

    def test_can_access(self):
        mgr = AttributeManager()
        mgr.set_attributes("agent-1", "resource-1", {"department": "engineering", "level": 3})
        self.assertTrue(mgr.can_access("agent-1", "resource-1", {"department": "engineering"}))
        self.assertFalse(mgr.can_access("agent-1", "resource-1", {"department": "sales"}))

    def test_nonexistent_returns_empty(self):
        mgr = AttributeManager()
        self.assertEqual(mgr.get_attributes("no-agent", "no-resource"), {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
