"""
Agent Registry & Discovery
Service discovery and agent metadata management
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)


@dataclass
class AgentMetadata:
    """Agent metadata for discovery"""
    agent_id: str
    name: str
    version: str
    description: str = ""
    capabilities: List[str] = None
    status: str = "active"  # active, inactive, paused
    last_heartbeat: str = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    registered_at: str = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.registered_at is None:
            self.registered_at = datetime.now(timezone.utc).isoformat()
        if self.last_heartbeat is None:
            self.last_heartbeat = self.registered_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMetadata':
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def is_alive(self, timeout_seconds: int = 300) -> bool:
        """Check if agent is still alive based on heartbeat"""
        last_beat = datetime.fromisoformat(self.last_heartbeat)
        now = datetime.now(timezone.utc)
        delta = now - last_beat.replace(tzinfo=timezone.utc) if last_beat.tzinfo is None else now - last_beat
        return delta < timedelta(seconds=timeout_seconds)


class AgentRegistry:
    """Central registry for agent discovery and management"""
    
    def __init__(self):
        """Initialize agent registry"""
        self.agents: Dict[str, AgentMetadata] = {}
        self.capabilities_index: Dict[str, List[str]] = {}  # capability -> agent_ids
        self.tags_index: Dict[str, List[str]] = {}  # tag -> agent_ids
    
    def register(self, metadata: AgentMetadata) -> bool:
        """Register an agent"""
        try:
            # Store agent
            self.agents[metadata.agent_id] = metadata
            
            # Index capabilities
            for capability in metadata.capabilities:
                if capability not in self.capabilities_index:
                    self.capabilities_index[capability] = []
                if metadata.agent_id not in self.capabilities_index[capability]:
                    self.capabilities_index[capability].append(metadata.agent_id)
            
            # Index tags
            for tag in metadata.tags:
                if tag not in self.tags_index:
                    self.tags_index[tag] = []
                if metadata.agent_id not in self.tags_index[tag]:
                    self.tags_index[tag].append(metadata.agent_id)
            
            logger.info(f"Registered agent: {metadata.agent_id} ({metadata.name})")
            return True
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            return False
    
    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent"""
        try:
            if agent_id not in self.agents:
                return False
            
            metadata = self.agents[agent_id]
            del self.agents[agent_id]
            
            # Remove from capability index
            for capability in metadata.capabilities:
                if capability in self.capabilities_index:
                    if agent_id in self.capabilities_index[capability]:
                        self.capabilities_index[capability].remove(agent_id)
                    if not self.capabilities_index[capability]:
                        del self.capabilities_index[capability]
            
            # Remove from tags index
            for tag in metadata.tags:
                if tag in self.tags_index:
                    if agent_id in self.tags_index[tag]:
                        self.tags_index[tag].remove(agent_id)
                    if not self.tags_index[tag]:
                        del self.tags_index[tag]
            
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error unregistering agent: {e}")
            return False
    
    def heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat"""
        if agent_id not in self.agents:
            return False
        
        self.agents[agent_id].last_heartbeat = datetime.now(timezone.utc).isoformat()
        return True
    
    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self, only_active: bool = False) -> List[AgentMetadata]:
        """Get all registered agents"""
        agents = list(self.agents.values())
        
        if only_active:
            agents = [a for a in agents if a.status == "active" and a.is_alive()]
        
        return agents
    
    def find_by_capability(self, capability: str) -> List[AgentMetadata]:
        """Find agents with a specific capability"""
        agent_ids = self.capabilities_index.get(capability, [])
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    def find_by_tag(self, tag: str) -> List[AgentMetadata]:
        """Find agents with a specific tag"""
        agent_ids = self.tags_index.get(tag, [])
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    def search(
        self,
        query: str = None,
        capability: str = None,
        tag: str = None,
        status: str = None,
        online_only: bool = False,
    ) -> List[AgentMetadata]:
        """Search for agents with multiple criteria"""
        results = list(self.agents.values())
        
        if query:
            # Search in name and description
            query_lower = query.lower()
            results = [a for a in results 
                      if query_lower in a.name.lower() or 
                         query_lower in a.description.lower()]
        
        if capability:
            results = [a for a in results if capability in a.capabilities]
        
        if tag:
            results = [a for a in results if tag in a.tags]
        
        if status:
            results = [a for a in results if a.status == status]
        
        if online_only:
            results = [a for a in results if a.is_alive()]
        
        return results
    
    def update_status(self, agent_id: str, status: str) -> bool:
        """Update agent status"""
        if agent_id not in self.agents:
            return False
        
        self.agents[agent_id].status = status
        logger.info(f"Updated agent {agent_id} status to {status}")
        return True
    
    def add_capability(self, agent_id: str, capability: str) -> bool:
        """Add a capability to an agent"""
        if agent_id not in self.agents:
            return False
        
        metadata = self.agents[agent_id]
        if capability not in metadata.capabilities:
            metadata.capabilities.append(capability)
            
            # Update index
            if capability not in self.capabilities_index:
                self.capabilities_index[capability] = []
            if agent_id not in self.capabilities_index[capability]:
                self.capabilities_index[capability].append(agent_id)
        
        return True
    
    def remove_capability(self, agent_id: str, capability: str) -> bool:
        """Remove a capability from an agent"""
        if agent_id not in self.agents:
            return False
        
        metadata = self.agents[agent_id]
        if capability in metadata.capabilities:
            metadata.capabilities.remove(capability)
            
            # Update index
            if capability in self.capabilities_index:
                if agent_id in self.capabilities_index[capability]:
                    self.capabilities_index[capability].remove(agent_id)
                if not self.capabilities_index[capability]:
                    del self.capabilities_index[capability]
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        all_agents = list(self.agents.values())
        active_agents = [a for a in all_agents if a.status == "active"]
        online_agents = [a for a in all_agents if a.is_alive()]
        
        return {
            "total_agents": len(all_agents),
            "active_agents": len(active_agents),
            "online_agents": len(online_agents),
            "total_capabilities": len(self.capabilities_index),
            "total_tags": len(self.tags_index),
            "capabilities": list(self.capabilities_index.keys()),
            "tags": list(self.tags_index.keys()),
        }


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get or create the global agent registry"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
