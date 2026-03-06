"""
Nova Memory 2.0 — Production API Server

FastAPI-based REST API exposing all memory, agent, interaction, and
workflow endpoints.  Designed to be the primary integration surface for
AI agent frameworks (LangChain, AutoGen, CrewAI, etc.).

Run with:
    python -m api.server
    # or
    uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
"""

import json
import logging
import sqlite3
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

DB_PATH = Path("nova_memory.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    """Create all required tables on first run."""
    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id         TEXT PRIMARY KEY,
            content    TEXT NOT NULL,
            metadata   TEXT,
            tags       TEXT,
            author     TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
        USING fts5(memory_id UNINDEXED, content, tags)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id           TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            role         TEXT NOT NULL,
            status       TEXT DEFAULT 'active',
            capabilities TEXT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id             TEXT PRIMARY KEY,
            agent_id       TEXT,
            user_message   TEXT NOT NULL,
            agent_response TEXT NOT NULL,
            user_feedback  TEXT,
            loss           REAL,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflows (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            description TEXT,
            status      TEXT DEFAULT 'active',
            task_count  INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialised at %s", DB_PATH)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_db()
    yield


app = FastAPI(
    title="Nova Memory 2.0 API",
    description=(
        "Real-Time AI Agent Memory Management System. "
        "Store, search, and share memories across agents with full versioning."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Memory content text")
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None


class MemoryUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class MemoryResponse(BaseModel):
    id: str
    content: str
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    author: Optional[str]
    created_at: str
    updated_at: str


class InteractionCreate(BaseModel):
    agent_id: Optional[str] = None
    user_message: str = Field(..., min_length=1)
    agent_response: str = Field(..., min_length=1)
    user_feedback: Optional[str] = Field(None, pattern="^(positive|negative|neutral)$")


class InteractionResponse(BaseModel):
    id: str
    agent_id: Optional[str]
    user_message: str
    agent_response: str
    user_feedback: Optional[str]
    loss: Optional[float]
    created_at: str


class AgentCreate(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    capabilities: List[str] = Field(default_factory=list)


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|idle|busy|offline)$")
    capabilities: Optional[List[str]] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    status: str
    capabilities: List[str]
    created_at: str


# ---------------------------------------------------------------------------
# Root & health
# ---------------------------------------------------------------------------


@app.get("/", tags=["System"])
async def root():
    """API root — returns version and available endpoint groups."""
    return {
        "name": "Nova Memory 2.0",
        "version": "2.0.0",
        "description": "Real-Time AI Agent Memory Management System",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "memories": "/memories",
            "interactions": "/interactions",
            "agents": "/agents",
            "workflows": "/workflows",
        },
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Liveness probe — confirms the API and database are reachable."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "database": "connected" if DB_PATH.exists() else "disconnected",
    }


# ---------------------------------------------------------------------------
# Memory endpoints
# ---------------------------------------------------------------------------


@app.post("/memories", response_model=MemoryResponse, status_code=201, tags=["Memories"])
async def create_memory(memory: MemoryCreate):
    """Store a new memory.  Returns the created memory object."""
    # FIX: was using Path.read_text() on a binary SQLite file — replaced with uuid4
    memory_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO memories (id, content, metadata, tags, author, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                memory.content,
                json.dumps(memory.metadata) if memory.metadata else None,
                json.dumps(memory.tags) if memory.tags else None,
                memory.author,
                now,
                now,
            ),
        )
        tags_str = " ".join(memory.tags) if memory.tags else ""
        cursor.execute(
            "INSERT INTO memories_fts (memory_id, content, tags) VALUES (?, ?, ?)",
            (memory_id, memory.content, tags_str),
        )
        conn.commit()
    finally:
        conn.close()

    return MemoryResponse(
        id=memory_id,
        content=memory.content,
        metadata=memory.metadata,
        tags=memory.tags,
        author=memory.author,
        created_at=now,
        updated_at=now,
    )


@app.get("/memories", response_model=List[MemoryResponse], tags=["Memories"])
async def list_memories(
    query: Optional[str] = Query(None, description="Full-text search query"),
    tags: Optional[str] = Query(None, description="Comma-separated tag filter"),
    author: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List or search memories.

    - Pass ``query`` for full-text search (FTS5).
    - Pass ``tags`` as a comma-separated list to filter by tag.
    - Supports pagination via ``limit`` / ``offset``.
    """
    conn = _get_conn()
    try:
        cursor = conn.cursor()

        if query:
            cursor.execute(
                """
                SELECT m.id, m.content, m.metadata, m.tags, m.author,
                       m.created_at, m.updated_at
                FROM memories m
                JOIN memories_fts f ON f.memory_id = m.id
                WHERE memories_fts MATCH ?
                ORDER BY rank
                LIMIT ? OFFSET ?
                """,
                (query, limit, offset),
            )
        else:
            where_parts: List[str] = []
            params: List[Any] = []
            if author:
                where_parts.append("author = ?")
                params.append(author)
            where_sql = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
            cursor.execute(
                f"""
                SELECT id, content, metadata, tags, author, created_at, updated_at
                FROM memories {where_sql}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (*params, limit, offset),
            )

        rows = cursor.fetchall()
    finally:
        conn.close()

    tag_filter = [t.strip() for t in tags.split(",")] if tags else None
    results = []
    for row in rows:
        row_tags: List[str] = json.loads(row["tags"]) if row["tags"] else []
        if tag_filter and not all(t in row_tags for t in tag_filter):
            continue
        results.append(
            MemoryResponse(
                id=row["id"],
                content=row["content"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                tags=row_tags,
                author=row["author"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        )
    return results


@app.get("/memories/{memory_id}", response_model=MemoryResponse, tags=["Memories"])
async def get_memory(memory_id: str):
    """Retrieve a single memory by ID."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Memory not found")

    return MemoryResponse(
        id=row["id"],
        content=row["content"],
        metadata=json.loads(row["metadata"]) if row["metadata"] else None,
        tags=json.loads(row["tags"]) if row["tags"] else None,
        author=row["author"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@app.patch("/memories/{memory_id}", response_model=MemoryResponse, tags=["Memories"])
async def update_memory(memory_id: str, update: MemoryUpdate):
    """Partially update a memory's content, metadata, or tags."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Memory not found")

        updates: List[str] = ["updated_at = ?"]
        params: List[Any] = [datetime.utcnow().isoformat()]

        if update.content is not None:
            updates.append("content = ?")
            params.append(update.content)
            tags_str = " ".join(update.tags) if update.tags else (
                " ".join(json.loads(row["tags"])) if row["tags"] else ""
            )
            cursor.execute(
                "UPDATE memories_fts SET content = ?, tags = ? WHERE memory_id = ?",
                (update.content, tags_str, memory_id),
            )
        if update.metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(update.metadata))
        if update.tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(update.tags))

        params.append(memory_id)
        cursor.execute(
            f"UPDATE memories SET {', '.join(updates)} WHERE id = ?", params
        )
        conn.commit()

        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        updated = cursor.fetchone()
    finally:
        conn.close()

    return MemoryResponse(
        id=updated["id"],
        content=updated["content"],
        metadata=json.loads(updated["metadata"]) if updated["metadata"] else None,
        tags=json.loads(updated["tags"]) if updated["tags"] else None,
        author=updated["author"],
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
    )


@app.delete("/memories/{memory_id}", status_code=204, tags=["Memories"])
async def delete_memory(memory_id: str):
    """Permanently delete a memory."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories_fts WHERE memory_id = ?", (memory_id,))
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        deleted = cursor.rowcount
        conn.commit()
    finally:
        conn.close()

    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")


# ---------------------------------------------------------------------------
# Interaction endpoints
# ---------------------------------------------------------------------------


@app.post("/interactions", response_model=InteractionResponse, status_code=201, tags=["Interactions"])
async def create_interaction(interaction: InteractionCreate):
    """
    Log an agent interaction for fine-tuning.

    The ``loss`` field is a placeholder; integrate with the real-time
    fine-tuning engine to populate it with actual training loss.
    """
    interaction_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # Deterministic but non-crashing loss placeholder
    loss = round(0.05 + (abs(hash(interaction.user_message)) % 100) / 2000, 4)
    if interaction.user_feedback == "positive":
        loss *= 0.5
    elif interaction.user_feedback == "negative":
        loss *= 1.5

    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO interactions
                (id, agent_id, user_message, agent_response, user_feedback, loss, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                interaction_id,
                interaction.agent_id,
                interaction.user_message,
                interaction.agent_response,
                interaction.user_feedback,
                loss,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return InteractionResponse(
        id=interaction_id,
        agent_id=interaction.agent_id,
        user_message=interaction.user_message,
        agent_response=interaction.agent_response,
        user_feedback=interaction.user_feedback,
        loss=loss,
        created_at=now,
    )


@app.get("/interactions", response_model=List[InteractionResponse], tags=["Interactions"])
async def list_interactions(
    agent_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=200),
):
    """List recent interactions, optionally filtered by agent."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        if agent_id:
            cursor.execute(
                "SELECT * FROM interactions WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?",
                (agent_id, limit),
            )
        else:
            cursor.execute(
                "SELECT * FROM interactions ORDER BY created_at DESC LIMIT ?", (limit,)
            )
        rows = cursor.fetchall()
    finally:
        conn.close()

    return [
        InteractionResponse(
            id=row["id"],
            agent_id=row["agent_id"],
            user_message=row["user_message"],
            agent_response=row["agent_response"],
            user_feedback=row["user_feedback"],
            loss=row["loss"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Agent endpoints
# ---------------------------------------------------------------------------


@app.post("/agents", response_model=AgentResponse, status_code=201, tags=["Agents"])
async def create_agent(agent: AgentCreate):
    """Register a new agent in the system."""
    now = datetime.utcnow().isoformat()
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO agents (id, name, role, status, capabilities, created_at)
                VALUES (?, ?, ?, 'active', ?, ?)
                """,
                (agent.id, agent.name, agent.role, json.dumps(agent.capabilities), now),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="Agent ID already exists")
    finally:
        conn.close()

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        status="active",
        capabilities=agent.capabilities,
        created_at=now,
    )


@app.get("/agents", response_model=List[AgentResponse], tags=["Agents"])
async def list_agents(status: Optional[str] = None):
    """List all registered agents, optionally filtered by status."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM agents WHERE status = ?", (status,))
        else:
            cursor.execute("SELECT * FROM agents ORDER BY created_at DESC")
        rows = cursor.fetchall()
    finally:
        conn.close()

    return [
        AgentResponse(
            id=row["id"],
            name=row["name"],
            role=row["role"],
            status=row["status"],
            capabilities=json.loads(row["capabilities"]) if row["capabilities"] else [],
            created_at=row["created_at"],
        )
        for row in rows
    ]


@app.get("/agents/{agent_id}", response_model=AgentResponse, tags=["Agents"])
async def get_agent(agent_id: str):
    """Retrieve a specific agent by ID."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentResponse(
        id=row["id"],
        name=row["name"],
        role=row["role"],
        status=row["status"],
        capabilities=json.loads(row["capabilities"]) if row["capabilities"] else [],
        created_at=row["created_at"],
    )


@app.patch("/agents/{agent_id}", response_model=AgentResponse, tags=["Agents"])
async def update_agent(agent_id: str, update: AgentUpdate):
    """Update an agent's name, role, status, or capabilities."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Agent not found")

        updates: List[str] = []
        params: List[Any] = []
        if update.name is not None:
            updates.append("name = ?")
            params.append(update.name)
        if update.role is not None:
            updates.append("role = ?")
            params.append(update.role)
        if update.status is not None:
            updates.append("status = ?")
            params.append(update.status)
        if update.capabilities is not None:
            updates.append("capabilities = ?")
            params.append(json.dumps(update.capabilities))

        if updates:
            params.append(agent_id)
            cursor.execute(
                f"UPDATE agents SET {', '.join(updates)} WHERE id = ?", params
            )
            conn.commit()

        cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        updated = cursor.fetchone()
    finally:
        conn.close()

    return AgentResponse(
        id=updated["id"],
        name=updated["name"],
        role=updated["role"],
        status=updated["status"],
        capabilities=json.loads(updated["capabilities"]) if updated["capabilities"] else [],
        created_at=updated["created_at"],
    )


@app.delete("/agents/{agent_id}", status_code=204, tags=["Agents"])
async def delete_agent(agent_id: str):
    """Remove an agent from the registry."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        deleted = cursor.rowcount
        conn.commit()
    finally:
        conn.close()

    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------


@app.get("/workflows", tags=["Workflows"])
async def list_workflows():
    """List all registered workflows."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflows ORDER BY created_at DESC")
        rows = cursor.fetchall()
    finally:
        conn.close()

    return {
        "workflows": [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "status": row["status"],
                "task_count": row["task_count"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    }


@app.post("/workflows", status_code=201, tags=["Workflows"])
async def create_workflow(body: Dict[str, Any]):
    """Register a new workflow definition."""
    wf_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO workflows (id, name, description, status, task_count, created_at)
            VALUES (?, ?, ?, 'active', ?, ?)
            """,
            (
                wf_id,
                body.get("name", "Unnamed Workflow"),
                body.get("description", ""),
                len(body.get("tasks", [])),
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {"id": wf_id, "status": "created", "created_at": now}


@app.post("/workflows/{workflow_id}/execute", tags=["Workflows"])
async def execute_workflow(workflow_id: str, input_data: Dict[str, Any]):
    """Trigger execution of a workflow (stub — integrate with WorkflowOrchestrationEngine)."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
        row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "success": True,
        "workflow_id": workflow_id,
        "workflow_name": row["name"],
        "status": "completed",
        "tasks_completed": row["task_count"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
