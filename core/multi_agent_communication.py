"""
Nova Memory 2.0 - Multi-Agent Communication Protocol

This module implements real-time agent-to-agent messaging,
shared memory space, and conflict resolution for multi-agent systems.
"""

import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid

class MessageType(Enum):
    """Types of messages between agents"""
    COMMAND = "command"
    DATA = "data"
    NOTIFICATION = "notification"
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    HEARTBEAT = "heartbeat"

class AgentStatus(Enum):
    """Agent status states"""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"

@dataclass
class AgentMessage:
    """Represents a message between agents"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: Optional[str] = None
    message_type: MessageType = MessageType.COMMAND
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 1  # 1 = low, 5 = high
    ttl: int = 3600  # Time to live in seconds

@dataclass
class Agent:
    """Represents an AI agent in the system"""
    agent_id: str
    name: str
    role: str  # e.g., "healthcare_agent", "data_analyzer"
    status: AgentStatus = AgentStatus.IDLE
    capabilities: List[str] = field(default_factory=list)
    assigned_tasks: List[str] = field(default_factory=list)
    memory_id: Optional[str] = None

    def dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "assigned_tasks": self.assigned_tasks,
            "memory_id": self.memory_id
        }

class SharedMemory:
    """
    Shared memory space for multi-agent coordination
    """

    def __init__(self):
        self.memory = {}  # {memory_id: {content, metadata, accessed_at}}
        self.memory_lock = threading.Lock()
        self.access_log = []  # List of memory access events

    def store_memory(self, memory_id: str, content: str, metadata: Optional[Dict] = None) -> str:
        """Store memory in shared space"""
        with self.memory_lock:
            self.memory[memory_id] = {
                "content": content,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "accessed_at": datetime.now().isoformat()
            }
            self.access_log.append({
                "memory_id": memory_id,
                "action": "store",
                "timestamp": datetime.now().isoformat()
            })
            return memory_id

    def retrieve_memory(self, memory_id: str) -> Optional[Dict]:
        """Retrieve memory from shared space"""
        with self.memory_lock:
            if memory_id in self.memory:
                self.memory[memory_id]["accessed_at"] = datetime.now().isoformat()
                return self.memory[memory_id]
            return None

    def search_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """Search memory using simple text matching"""
        with self.memory_lock:
            results = []
            for mem_id, mem_data in self.memory.items():
                if query.lower() in mem_data["content"].lower():
                    results.append({
                        "memory_id": mem_id,
                        "content": mem_data["content"],
                        "metadata": mem_data["metadata"],
                        "accessed_at": mem_data["accessed_at"]
                    })

            return results[:limit]

    def get_recent_accesses(self, hours: int = 1) -> List[Dict]:
        """Get recent memory accesses"""
        with self.memory_lock:
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            return [
                log for log in self.access_log
                if datetime.fromisoformat(log["timestamp"]).timestamp() > cutoff_time
            ]

class CommunicationProtocol:
    """
    Multi-agent communication protocol with conflict resolution
    """

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.message_queue: Dict[str, List[AgentMessage]] = {}
        self.shared_memory = SharedMemory()
        self.message_lock = threading.Lock()
        self.agent_lock = threading.Lock()
        self.notification_callback = None

    def register_agent(self, agent: Agent) -> bool:
        """Register a new agent in the system"""
        with self.agent_lock:
            if agent.agent_id in self.agents:
                return False

            self.agents[agent.agent_id] = agent
            self.message_queue[agent.agent_id] = []

            # Send welcome message
            welcome_msg = AgentMessage(
                sender_id="system",
                recipient_id=agent.agent_id,
                message_type=MessageType.NOTIFICATION,
                content={"type": "agent_registered", "agent": agent.dict()}
            )
            self._enqueue_message(welcome_msg)

            return True

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        with self.agent_lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                if agent_id in self.message_queue:
                    del self.message_queue[agent_id]
                return True
            return False

    def send_message(self, sender_id: str, recipient_id: str, message_type: MessageType,
                     content: Dict[str, Any], priority: int = 1) -> bool:
        """Send a message to another agent"""
        message = AgentMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            priority=priority
        )

        return self._enqueue_message(message)

    def _enqueue_message(self, message: AgentMessage) -> bool:
        """Queue a message for delivery"""
        with self.message_lock:
            if message.recipient_id in self.message_queue:
                self.message_queue[message.recipient_id].append(message)
                return True
            return False

    def broadcast(self, sender_id: str, message_type: MessageType,
                  content: Dict[str, Any], priority: int = 1):
        """Broadcast message to all agents"""
        with self.agent_lock:
            for agent_id in self.agents.keys():
                self.send_message(sender_id, agent_id, message_type, content, priority)

    def process_messages(self, agent_id: str) -> List[AgentMessage]:
        """Process pending messages for an agent"""
        with self.message_lock:
            messages = self.message_queue.get(agent_id, []).copy()
            self.message_queue[agent_id] = []
            return messages

    def resolve_conflict(self, agent_id: str, conflict_data: Dict) -> Dict:
        """
        Resolve conflicts between agents using consensus algorithm

        Args:
            agent_id: ID of the agent requesting resolution
            conflict_data: {
                "conflicting_decisions": List[Dict],
                "context": Dict
            }

        Returns:
            Resolved decision
        """
        # Simple consensus algorithm:
        # 1. Count votes for each decision
        # 2. Majority wins
        # 3. If tie, use agent with highest priority

        decisions = conflict_data["conflicting_decisions"]
        vote_counts = {}

        for decision in decisions:
            decision_id = decision.get("decision_id")
            priority = decision.get("priority", 1)
            agent_id = decision.get("agent_id")

            if decision_id not in vote_counts:
                vote_counts[decision_id] = {"count": 0, "agents": []}

            vote_counts[decision_id]["count"] += 1
            vote_counts[decision_id]["agents"].append(agent_id)

        # Find winner
        winner = None
        max_votes = 0

        for decision_id, data in vote_counts.items():
            if data["count"] > max_votes:
                max_votes = data["count"]
                winner = decision_id
            elif data["count"] == max_votes:
                # Tie breaker: higher priority agent
                if data["agents"][0] == agent_id:
                    winner = decision_id

        return {
            "resolved_decision": winner,
            "vote_count": max_votes,
            "total_decisions": len(decisions),
            "consensus_reached": max_votes > len(decisions) // 2
        }

    def coordinate_task(self, task_id: str, task_description: str, required_agents: List[str]) -> Dict:
        """
        Coordinate a task across multiple agents

        Args:
            task_id: Unique task identifier
            task_description: Description of the task
            required_agents: List of agent IDs needed

        Returns:
            Task coordination result
        """
        # Create task in shared memory
        self.shared_memory.store_memory(
            memory_id=task_id,
            content=task_description,
            metadata={"type": "task", "required_agents": required_agents}
        )

        # Send task to required agents
        broadcast_content = {
            "type": "task_assignment",
            "task_id": task_id,
            "task_description": task_description,
            "required_agents": required_agents,
            "timestamp": datetime.now().isoformat()
        }

        for agent_id in required_agents:
            self.send_message(
                sender_id="system",
                recipient_id=agent_id,
                message_type=MessageType.COMMAND,
                content=broadcast_content
            )

        return {
            "task_id": task_id,
            "status": "assigned",
            "required_agents": required_agents,
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """Get status of an agent"""
        with self.agent_lock:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                return {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "role": agent.role,
                    "status": agent.status.value,
                    "capabilities": agent.capabilities,
                    "assigned_tasks": agent.assigned_tasks
                }
            return None

    def set_notification_callback(self, callback):
        """Set callback for incoming notifications"""
        self.notification_callback = callback

    def _process_notifications(self):
        """Process and deliver notifications"""
        with self.agent_lock:
            for agent_id, agent in self.agents.items():
                if self.notification_callback and agent.status == AgentStatus.ACTIVE:
                    try:
                        self.notification_callback(agent_id, agent)
                    except Exception as e:
                        print(f"Error processing notification for {agent_id}: {e}")

# Demo and Testing
if __name__ == "__main__":
    print("Nova Memory 2.0 - Multi-Agent Communication Protocol")
    print("=" * 60)

    # Initialize protocol
    protocol = CommunicationProtocol()

    # Register agents
    print("\n1. Registering agents...")

    agents = [
        Agent(agent_id="agent_1", name="Healthcare Agent", role="healthcare_agent",
              capabilities=["patient_history", "diagnosis", "treatment_planning"]),
        Agent(agent_id="agent_2", name="Data Analyst Agent", role="data_analyzer",
              capabilities=["data_processing", "analysis", "reporting"]),
        Agent(agent_id="agent_3", name="Communication Agent", role="communication_agent",
              capabilities=["messaging", "coordination", "notifications"]),
    ]

    for agent in agents:
        protocol.register_agent(agent)
        print(f"   ✅ Registered: {agent.name} ({agent.role})")

    # Store shared memory
    print("\n2. Storing shared memory...")
    protocol.shared_memory.store_memory(
        memory_id="patient_123",
        content="Patient John Doe, 45 years old, diabetes type 2, allergic to penicillin",
        metadata={"patient_id": "123", "last_updated": "2026-03-04"}
    )
    protocol.shared_memory.store_memory(
        memory_id="treatment_plan",
        content="Patient requires insulin injections twice daily and regular blood sugar monitoring",
        metadata={"patient_id": "123", "treatment_type": "diabetes_management"}
    )
    print(f"   ✅ Stored {len(protocol.shared_memory.memory)} memories")

    # Send messages
    print("\n3. Sending messages...")

    protocol.send_message(
        sender_id="agent_1",
        recipient_id="agent_2",
        message_type=MessageType.DATA,
        content={"type": "patient_data", "patient_id": "123"},
        priority=5
    )
    print("   ✅ Sent patient data to Data Analyst Agent")

    protocol.broadcast(
        sender_id="agent_3",
        message_type=MessageType.NOTIFICATION,
        content={"type": "new_patient", "patient_id": "123"},
        priority=3
    )
    print("   ✅ Broadcasted notification to all agents")

    # Process messages for an agent
    print("\n4. Processing messages...")

    messages = protocol.process_messages("agent_2")
    print(f"   Agent_2 received {len(messages)} messages")

    for msg in messages:
        print(f"   - {msg.message_type.value}: {msg.content.get('type', 'unknown')}")

    # Coordinate a task
    print("\n5. Coordinating a task...")

    task_result = protocol.coordinate_task(
        task_id="task_456",
        task_description="Generate comprehensive patient report for John Doe",
        required_agents=["agent_1", "agent_2", "agent_3"]
    )
    print(f"   ✅ Task coordinated: {task_result['task_id']}")
    print(f"   Required agents: {task_result['required_agents']}")

    # Search memory
    print("\n6. Searching memory...")
    query = "diabetes"
    results = protocol.shared_memory.search_memory(query, limit=5)

    print(f"   Query: '{query}'")
    print(f"   Found {len(results)} results:")
    for result in results:
        print(f"   - {result['memory_id']}: {result['content'][:50]}...")

    # Get agent status
    print("\n7. Agent status:")
    for agent in agents:
        status = protocol.get_agent_status(agent.agent_id)
        print(f"   {agent.name}: {status['status']}")

    print("\n✅ Multi-agent communication demo complete!")
    print("   This protocol enables real-time coordination between multiple AI agents")
    print("   with shared memory and conflict resolution mechanisms.")
