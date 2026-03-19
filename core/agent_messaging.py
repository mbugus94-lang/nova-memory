"""
Agent-to-Agent Messaging System
Enables direct communication between agents with pub/sub and request/response patterns
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
import uuid
from enum import Enum
from dataclasses import dataclass, asdict
import queue
import threading

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Message types for inter-agent communication"""
    NOTIFICATION = "notification"      # One-way message
    REQUEST = "request"                # Expects a response
    RESPONSE = "response"              # Response to a request
    EVENT = "event"                    # Broadcast event
    COMMAND = "command"                # Command to execute
    STATUS = "status"                  # Status update


class MessagePriority(int, Enum):
    """Message priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Message:
    """Inter-agent message structure"""
    id: str
    type: MessageType
    sender: str
    recipient: str
    subject: str
    content: Any
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: str = None
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        data = asdict(self)
        data['type'] = self.type.value
        data['priority'] = self.priority.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        data = data.copy()
        if isinstance(data.get('type'), str):
            data['type'] = MessageType(data['type'])
        if isinstance(data.get('priority'), int):
            data['priority'] = MessagePriority(data['priority'])
        return cls(**data)


class MessageBroker:
    """Central message broker for agent communication"""

    def __init__(self):
        """Initialize message broker"""
        self.subscriptions: Dict[str, List[str]] = {}  # topic -> [agent_ids]
        self.agent_inboxes: Dict[str, queue.Queue] = {}  # agent_id -> message_queue
        self.request_handlers: Dict[str, Callable] = {}  # request_type -> handler
        self.message_history: List[Message] = []
        self.max_history = 1000
        self.lock = threading.RLock()

    def register_agent(self, agent_id: str) -> None:
        """Register an agent with the broker"""
        with self.lock:
            if agent_id not in self.agent_inboxes:
                self.agent_inboxes[agent_id] = queue.Queue()
                logger.info(f"Agent registered: {agent_id}")

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        with self.lock:
            if agent_id in self.agent_inboxes:
                del self.agent_inboxes[agent_id]
            # Remove from subscriptions
            for topic in list(self.subscriptions.keys()):
                if agent_id in self.subscriptions[topic]:
                    self.subscriptions[topic].remove(agent_id)
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
            logger.info(f"Agent unregistered: {agent_id}")

    def publish(self, message: Message) -> bool:
        """Publish a message to recipient(s)"""
        with self.lock:
            # Add to history
            self._add_to_history(message)

            # Send to specific recipient
            if message.recipient in self.agent_inboxes:
                self.agent_inboxes[message.recipient].put(message)
                logger.debug(f"Message published: {message.id} to {message.recipient}")
                return True
            else:
                logger.warning(f"Recipient not found: {message.recipient}")
                return False

    def broadcast(self, message: Message, topic: str) -> int:
        """Broadcast a message to all subscribers of a topic"""
        with self.lock:
            # Add to history
            self._add_to_history(message)

            subscribers = self.subscriptions.get(topic, [])
            count = 0

            for agent_id in subscribers:
                if agent_id != message.sender:  # Don't send to self
                    message.recipient = agent_id
                    if agent_id in self.agent_inboxes:
                        self.agent_inboxes[agent_id].put(message)
                        count += 1

            logger.info(f"Message broadcast: {message.id} to {count} agents on topic {topic}")
            return count

    def subscribe(self, agent_id: str, topic: str) -> None:
        """Subscribe an agent to a topic"""
        with self.lock:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = []
            if agent_id not in self.subscriptions[topic]:
                self.subscriptions[topic].append(agent_id)
                logger.info(f"Agent {agent_id} subscribed to topic {topic}")

    def unsubscribe(self, agent_id: str, topic: str) -> None:
        """Unsubscribe an agent from a topic"""
        with self.lock:
            if topic in self.subscriptions:
                if agent_id in self.subscriptions[topic]:
                    self.subscriptions[topic].remove(agent_id)
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
                logger.info(f"Agent {agent_id} unsubscribed from topic {topic}")

    def receive(self, agent_id: str, timeout: float = 0.1) -> Optional[Message]:
        """Receive next message for an agent"""
        if agent_id not in self.agent_inboxes:
            return None

        try:
            message = self.agent_inboxes[agent_id].get(timeout=timeout)
            logger.debug(f"Message received by {agent_id}: {message.id}")
            return message
        except queue.Empty:
            return None

    def receive_all(self, agent_id: str) -> List[Message]:
        """Receive all available messages for an agent"""
        messages = []
        while True:
            msg = self.receive(agent_id, timeout=0)
            if msg is None:
                break
            messages.append(msg)
        return messages

    def register_handler(self, request_type: str, handler: Callable) -> None:
        """Register a handler for a request type"""
        self.request_handlers[request_type] = handler
        logger.info(f"Request handler registered: {request_type}")

    def handle_request(self, message: Message) -> Optional[Message]:
        """Handle a request message and return response"""
        subject_parts = message.subject.split(":")
        request_type = subject_parts[0] if subject_parts else message.subject

        handler = self.request_handlers.get(request_type)
        if not handler:
            logger.warning(f"No handler for request type: {request_type}")
            return None

        try:
            response_content = handler(message.content)
            response = Message(
                id=str(uuid.uuid4()),
                type=MessageType.RESPONSE,
                sender=message.recipient,
                recipient=message.sender,
                subject=f"response:{message.subject}",
                content=response_content,
                reply_to=message.id,
                priority=message.priority,
            )
            return response
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return None

    def get_history(
        self,
        agent_id: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 100,
    ) -> List[Message]:
        """Get message history with optional filtering"""
        with self.lock:
            filtered = self.message_history

            if agent_id:
                filtered = [m for m in filtered
                          if m.sender == agent_id or m.recipient == agent_id]

            if message_type:
                filtered = [m for m in filtered if m.type == message_type]

            return filtered[-limit:]

    def clear_history(self) -> None:
        """Clear message history"""
        with self.lock:
            self.message_history.clear()
            logger.info("Message history cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get broker statistics"""
        with self.lock:
            inbox_sizes = {
                agent: self.agent_inboxes[agent].qsize()
                for agent in self.agent_inboxes
            }
            return {
                "registered_agents": len(self.agent_inboxes),
                "topics": len(self.subscriptions),
                "inbox_sizes": inbox_sizes,
                "history_size": len(self.message_history),
                "subscriptions": {
                    topic: len(agents)
                    for topic, agents in self.subscriptions.items()
                },
            }

    def _add_to_history(self, message: Message) -> None:
        """Add message to history, maintaining max size"""
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)


# Global broker instance
_broker: Optional[MessageBroker] = None


def get_message_broker() -> MessageBroker:
    """Get or create the global message broker"""
    global _broker
    if _broker is None:
        _broker = MessageBroker()
    return _broker


def create_message(
    sender: str,
    recipient: str,
    subject: str,
    content: Any,
    message_type: MessageType = MessageType.NOTIFICATION,
    priority: MessagePriority = MessagePriority.NORMAL,
    reply_to: Optional[str] = None,
) -> Message:
    """Helper to create a message"""
    return Message(
        id=str(uuid.uuid4()),
        type=message_type,
        sender=sender,
        recipient=recipient,
        subject=subject,
        content=content,
        priority=priority,
        reply_to=reply_to,
    )


def send_message(
    sender: str,
    recipient: str,
    subject: str,
    content: Any,
    priority: MessagePriority = MessagePriority.NORMAL,
) -> bool:
    """Send a message from one agent to another"""
    broker = get_message_broker()
    broker.register_agent(sender)
    broker.register_agent(recipient)

    message = create_message(
        sender=sender,
        recipient=recipient,
        subject=subject,
        content=content,
        message_type=MessageType.NOTIFICATION,
        priority=priority,
    )

    return broker.publish(message)


def broadcast_event(
    sender: str,
    topic: str,
    event_type: str,
    data: Any,
) -> int:
    """Broadcast an event to all subscribers of a topic"""
    broker = get_message_broker()
    broker.register_agent(sender)

    message = create_message(
        sender=sender,
        recipient="",  # Will be set during broadcast
        subject=f"event:{event_type}",
        content=data,
        message_type=MessageType.EVENT,
    )

    return broker.broadcast(message, topic)
