"""
Nova Memory 2.0 — Agent Framework Adapters

Drop-in memory adapters for popular AI agent frameworks:
  - LangChain  (BaseMemory-compatible)
  - AutoGen    (ConversableAgent memory hook)
  - CrewAI     (Tool-compatible memory wrapper)
  - Generic    (dict-based interface for any framework)

All adapters share the same underlying EnhancedMemoryStorage backend,
so memories are persisted, searchable, and versioned regardless of which
framework is used.

Installation:
    pip install langchain          # for LangChainMemoryAdapter
    pip install pyautogen          # for AutoGenMemoryHook
    pip install crewai             # for CrewAIMemoryTool

Each adapter works standalone even if the target framework is not installed
— it simply falls back to the generic interface and logs a warning.
"""

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is on path when running directly from integrations/
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Generic adapter (always available)
# ---------------------------------------------------------------------------

class GenericMemoryAdapter:
    """
    Framework-agnostic memory adapter backed by EnhancedMemoryStorage.

    This is the base class for all framework-specific adapters and can
    also be used directly in any custom agent framework.
    """

    def __init__(self, db_path: str = "nova_memory_v2.db", agent_id: str = "default"):
        from enhanced_memory import EnhancedMemoryStorage
        self.storage = EnhancedMemoryStorage(db_path=db_path)
        self.agent_id = agent_id
        self._session_memories: List[str] = []  # IDs added in this session

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    def save(self, content: str, metadata: Optional[Dict] = None, tags: Optional[List[str]] = None) -> Optional[str]:
        """Persist a memory and return its ID."""
        mid = self.storage.add_memory(
            content=content,
            metadata=metadata,
            tags=tags,
            author=self.agent_id,
        )
        if mid:
            self._session_memories.append(mid)
        return mid

    def load(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant memories and return the top-k results."""
        return self.storage.search_memories(query, limit=top_k)

    def load_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID."""
        return self.storage.get_memory(memory_id)

    def clear_session(self) -> int:
        """Delete all memories created in this session. Returns count deleted."""
        count = 0
        for mid in self._session_memories:
            if self.storage.delete_memory(mid):
                count += 1
        self._session_memories.clear()
        return count

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Return storage statistics."""
        return self.storage.get_memory_stats()


# ---------------------------------------------------------------------------
# LangChain adapter
# ---------------------------------------------------------------------------

try:
    from langchain.memory import BaseMemory
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False
    BaseMemory = object  # type: ignore


class LangChainMemoryAdapter(BaseMemory if _LANGCHAIN_AVAILABLE else object):
    """
    LangChain-compatible memory backend using Nova Memory.

    Drop-in replacement for ConversationBufferMemory or any BaseMemory
    subclass.  Persists all conversation turns to SQLite with full-text
    search.

    Usage::

        from integrations.agent_framework_adapters import LangChainMemoryAdapter
        from langchain.chains import ConversationChain
        from langchain.llms import OpenAI

        memory = LangChainMemoryAdapter(agent_id="my_agent")
        chain = ConversationChain(llm=OpenAI(), memory=memory)
    """

    memory_key: str = "history"

    def __init__(self, db_path: str = "nova_memory_v2.db", agent_id: str = "langchain_agent"):
        if _LANGCHAIN_AVAILABLE:
            super().__init__()
        self._adapter = GenericMemoryAdapter(db_path=db_path, agent_id=agent_id)
        self._history: List[Tuple[str, str]] = []

    @property
    def memory_variables(self) -> List[str]:
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load relevant memories for the current input."""
        query = inputs.get("input", inputs.get("human_input", ""))
        if query:
            results = self._adapter.load(query, top_k=5)
            history_text = "\n".join(
                f"[{r['created_at']}] {r['content']}" for r in results
            )
        else:
            history_text = "\n".join(f"Human: {h}\nAI: {a}" for h, a in self._history[-5:])

        return {self.memory_key: history_text}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Persist a conversation turn."""
        human = inputs.get("input", inputs.get("human_input", ""))
        ai = outputs.get("response", outputs.get("output", ""))

        if human and ai:
            self._history.append((human, ai))
            self._adapter.save(
                content=f"Human: {human}\nAI: {ai}",
                metadata={"type": "conversation_turn", "timestamp": datetime.now(timezone.utc).isoformat()},
                tags=["conversation", "langchain"],
            )

    def clear(self) -> None:
        """Clear in-memory history (does not delete persisted memories)."""
        self._history.clear()


# ---------------------------------------------------------------------------
# AutoGen adapter
# ---------------------------------------------------------------------------

class AutoGenMemoryHook:
    """
    Memory hook for Microsoft AutoGen agents.

    Attach to a ConversableAgent to give it persistent, searchable memory:

    Usage::

        from integrations.agent_framework_adapters import AutoGenMemoryHook

        hook = AutoGenMemoryHook(agent_id="autogen_assistant")
        assistant = autogen.AssistantAgent(
            name="assistant",
            system_message=hook.build_system_message("You are a helpful assistant."),
        )

        # After each reply, persist the interaction:
        hook.on_message_received(sender="user", message="Hello")
        hook.on_reply_generated(reply="Hi there!")
    """

    def __init__(self, db_path: str = "nova_memory_v2.db", agent_id: str = "autogen_agent"):
        self._adapter = GenericMemoryAdapter(db_path=db_path, agent_id=agent_id)
        self.agent_id = agent_id

    def build_system_message(self, base_message: str) -> str:
        """
        Inject a memory-awareness instruction into the agent's system message.
        """
        return (
            f"{base_message}\n\n"
            "You have access to a persistent memory system. "
            "When you recall information from previous conversations, "
            "prefix it with '[Memory]'. "
            "Important facts will be automatically stored for future reference."
        )

    def on_message_received(self, sender: str, message: str) -> None:
        """Call this whenever the agent receives a message."""
        self._adapter.save(
            content=f"[FROM {sender}] {message}",
            metadata={"type": "received_message", "sender": sender},
            tags=["autogen", "received"],
        )

    def on_reply_generated(self, reply: str) -> None:
        """Call this whenever the agent generates a reply."""
        self._adapter.save(
            content=f"[REPLY] {reply}",
            metadata={"type": "generated_reply"},
            tags=["autogen", "reply"],
        )

    def recall(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for a given query."""
        return self._adapter.load(query, top_k=top_k)

    def recall_as_text(self, query: str, top_k: int = 5) -> str:
        """Return relevant memories as a formatted string for injection into prompts."""
        memories = self.recall(query, top_k=top_k)
        if not memories:
            return "No relevant memories found."
        lines = [f"- {m['content']}" for m in memories]
        return "Relevant memories:\n" + "\n".join(lines)


# ---------------------------------------------------------------------------
# CrewAI adapter
# ---------------------------------------------------------------------------

class CrewAIMemoryTool:
    """
    CrewAI-compatible memory tool for Nova Memory.

    Exposes ``save_memory`` and ``search_memory`` as CrewAI Tool-compatible
    callables.  If CrewAI is installed, the tools are wrapped as proper
    ``crewai.Tool`` objects; otherwise plain callables are returned.

    Usage::

        from integrations.agent_framework_adapters import CrewAIMemoryTool

        memory_tool = CrewAIMemoryTool(agent_id="crewai_agent")
        tools = memory_tool.get_tools()  # pass to CrewAI Agent

        agent = Agent(
            role="Researcher",
            goal="Research and remember key facts",
            tools=tools,
        )
    """

    def __init__(self, db_path: str = "nova_memory_v2.db", agent_id: str = "crewai_agent"):
        self._adapter = GenericMemoryAdapter(db_path=db_path, agent_id=agent_id)
        self.agent_id = agent_id

    def _save_memory_fn(self, content: str) -> str:
        """Save a memory. Input: plain text string."""
        mid = self._adapter.save(
            content=content,
            tags=["crewai"],
            metadata={"type": "crewai_memory"},
        )
        return f"Memory saved with ID: {mid}" if mid else "Failed to save memory."

    def _search_memory_fn(self, query: str) -> str:
        """Search memories. Input: search query string."""
        results = self._adapter.load(query, top_k=5)
        if not results:
            return "No relevant memories found."
        lines = [f"[{i+1}] {r['content']}" for i, r in enumerate(results)]
        return "\n".join(lines)

    def get_tools(self) -> List[Any]:
        """
        Return a list of tools compatible with CrewAI.

        If CrewAI is installed, returns proper ``crewai.Tool`` objects.
        Otherwise returns plain dicts describing the tools.
        """
        try:
            from crewai import Tool
            return [
                Tool(
                    name="save_memory",
                    description="Save important information to persistent memory for future recall.",
                    func=self._save_memory_fn,
                ),
                Tool(
                    name="search_memory",
                    description="Search persistent memory for relevant information.",
                    func=self._search_memory_fn,
                ),
            ]
        except ImportError:
            logger.info("crewai not installed — returning plain callables")
            return [
                {"name": "save_memory",   "func": self._save_memory_fn,   "description": "Save to memory"},
                {"name": "search_memory", "func": self._search_memory_fn, "description": "Search memory"},
            ]


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    test_db = "/tmp/nova_adapters_test.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    print("=" * 60)
    print("AGENT FRAMEWORK ADAPTERS — NOVA MEMORY v2.0")
    print("=" * 60)

    # Generic adapter
    print("\n[1] Generic Adapter")
    generic = GenericMemoryAdapter(db_path=test_db, agent_id="test_agent")
    mid = generic.save("The capital of France is Paris.", tags=["geography"])
    print(f"    Saved memory: {mid}")
    results = generic.load("France capital")
    print(f"    Search 'France capital' → {len(results)} result(s)")

    # LangChain adapter
    print("\n[2] LangChain Adapter")
    lc = LangChainMemoryAdapter(db_path=test_db, agent_id="langchain_agent")
    lc.save_context(
        {"input": "What is the capital of France?"},
        {"response": "The capital of France is Paris."},
    )
    vars_ = lc.load_memory_variables({"input": "France"})
    print(f"    Memory variables loaded: {len(vars_['history'])} chars")

    # AutoGen adapter
    print("\n[3] AutoGen Adapter")
    ag = AutoGenMemoryHook(db_path=test_db, agent_id="autogen_agent")
    ag.on_message_received("user", "Tell me about Paris.")
    ag.on_reply_generated("Paris is the capital and largest city of France.")
    recall = ag.recall_as_text("Paris")
    print(f"    Recall result: {recall[:80]}...")

    # CrewAI adapter
    print("\n[4] CrewAI Adapter")
    crew = CrewAIMemoryTool(db_path=test_db, agent_id="crewai_agent")
    tools = crew.get_tools()
    print(f"    Tools available: {[t['name'] if isinstance(t, dict) else t.name for t in tools]}")
    save_fn = tools[0]["func"] if isinstance(tools[0], dict) else tools[0].func
    result = save_fn("Paris has a population of approximately 2.1 million in the city proper.")
    print(f"    Save result: {result}")

    print("\n" + "=" * 60)
    print("ADAPTERS TEST COMPLETE")
    print("=" * 60)
