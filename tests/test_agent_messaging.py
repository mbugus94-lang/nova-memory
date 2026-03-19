"""
Tests for core/agent_messaging.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_messaging import (
    MessageBroker, MessageType, create_message, send_message,
)


class TestMessage(unittest.TestCase):

    def test_create_message(self):
        msg = create_message(
            sender="agent-1",
            recipient="agent-2",
            subject="test",
            content={"data": "hello"},
        )
        self.assertEqual(msg.sender, "agent-1")
        self.assertEqual(msg.recipient, "agent-2")
        self.assertIsNotNone(msg.id)

    def test_to_dict(self):
        msg = create_message("a1", "a2", "subject", {"key": "value"})
        d = msg.to_dict()
        self.assertEqual(d["sender"], "a1")
        self.assertEqual(d["type"], "notification")
        self.assertEqual(d["priority"], 1)

    def test_from_dict(self):
        msg = create_message("a1", "a2", "subject", {"key": "value"})
        from core.agent_messaging import Message
        restored = Message.from_dict(msg.to_dict())
        self.assertEqual(restored.id, msg.id)
        self.assertEqual(restored.sender, "a1")


class TestMessageBroker(unittest.TestCase):

    def setUp(self):
        self.broker = MessageBroker()

    def test_register_agent(self):
        self.broker.register_agent("agent-1")
        self.assertIn("agent-1", self.broker.agent_inboxes)

    def test_publish_message(self):
        self.broker.register_agent("sender")
        self.broker.register_agent("receiver")
        msg = create_message("sender", "receiver", "hello", {"msg": "hi"})
        result = self.broker.publish(msg)
        self.assertTrue(result)

    def test_receive_message(self):
        self.broker.register_agent("receiver")
        msg = create_message("sender", "receiver", "hello", "content")
        self.broker.publish(msg)
        received = self.broker.receive("receiver", timeout=1.0)
        self.assertIsNotNone(received)
        self.assertEqual(received.subject, "hello")

    def test_receive_all(self):
        self.broker.register_agent("receiver")
        for i in range(3):
            msg = create_message("sender", "receiver", f"msg-{i}", i)
            self.broker.publish(msg)
        messages = self.broker.receive_all("receiver")
        self.assertEqual(len(messages), 3)

    def test_publish_to_nonexistent_returns_false(self):
        self.broker.register_agent("sender")
        msg = create_message("sender", "ghost", "hello", "content")
        result = self.broker.publish(msg)
        self.assertFalse(result)

    def test_broadcast(self):
        self.broker.register_agent("sender")
        self.broker.register_agent("agent-1")
        self.broker.register_agent("agent-2")
        self.broker.subscribe("agent-1", "topic-1")
        self.broker.subscribe("agent-2", "topic-1")

        msg = create_message("sender", "*", "event", {"data": "test"}, MessageType.EVENT)
        count = self.broker.broadcast(msg, "topic-1")
        self.assertEqual(count, 2)

    def test_subscribe_and_unsubscribe(self):
        self.broker.register_agent("agent-1")
        self.broker.subscribe("agent-1", "topic-1")
        self.assertIn("topic-1", self.broker.subscriptions)
        self.broker.unsubscribe("agent-1", "topic-1")
        self.assertNotIn("topic-1", self.broker.subscriptions)

    def test_message_history(self):
        self.broker.register_agent("receiver")
        msg = create_message("sender", "receiver", "hello", "content")
        self.broker.publish(msg)
        history = self.broker.get_history(agent_id="receiver")
        self.assertEqual(len(history), 1)

    def test_get_stats(self):
        self.broker.register_agent("agent-1")
        stats = self.broker.get_stats()
        self.assertEqual(stats["registered_agents"], 1)

    def test_unregister_agent(self):
        self.broker.register_agent("agent-1")
        self.broker.unregister_agent("agent-1")
        self.assertNotIn("agent-1", self.broker.agent_inboxes)


class TestSendMessage(unittest.TestCase):

    def test_send_message_helper(self):
        result = send_message("agent-1", "agent-2", "greeting", {"msg": "hello"})
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
