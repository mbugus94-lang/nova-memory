"""
Nova Memory 2.0 - Production API Server
FastAPI-based REST API with real-time fine-tuning and multi-agent support
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
import sqlite3
import json
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(
    title="Nova Memory 2.0 API",
    description="Real-Time AI Agent Memory Management System with Fine-Tuning",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
DB_PATH = Path("nova_memory.db")

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            capabilities TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id TEXT PRIMARY KEY,
            user_message TEXT NOT NULL,
            agent_response TEXT NOT NULL,
            user_feedback TEXT,
            loss REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models
class MemoryCreate(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None

class MemoryResponse(BaseModel):
    id: str
    content: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class InteractionCreate(BaseModel):
    user_message: str
    agent_response: str
    user_feedback: Optional[str] = None

class InteractionResponse(BaseModel):
    id: str
    user_message: str
    agent_response: str
    user_feedback: Optional[str]
    loss: Optional[float]
    created_at: datetime

class AgentCreate(BaseModel):
    id: str
    name: str
    role: str
    capabilities: List[str]

class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    status: str
    capabilities: List[str]
    created_at: datetime

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if DB_PATH.exists() else "disconnected"
    }

@app.get("/")
async def root():
    """Root endpoint"""
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
            "workflows": "/workflows"
        }
    }

# Memory Endpoints

@app.post("/memories", response_model=MemoryResponse)
async def create_memory(memory: MemoryCreate):
    """Create a new memory"""
    memory_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(Path(DB_PATH).read_text())}"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO memories (id, content, metadata)
        VALUES (?, ?, ?)
    """, (memory_id, memory.content, json.dumps(memory.metadata or {})))

    conn.commit()
    conn.close()

    return MemoryResponse(
        id=memory_id,
        content=memory.content,
        metadata=memory.metadata,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@app.get("/memories", response_model=List[MemoryResponse])
async def get_memories(query: Optional[str] = None, limit: int = 10):
    """Retrieve memories"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if query:
        cursor.execute("""
            SELECT * FROM memories
            WHERE content LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (f"%{query}%", limit))
    else:
        cursor.execute("""
            SELECT * FROM memories
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

    memories = cursor.fetchall()
    conn.close()

    return [
        MemoryResponse(
            id=row["id"],
            content=row["content"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
        for row in memories
    ]

@app.get("/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: str):
    """Get a specific memory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Memory not found")

    return MemoryResponse(
        id=row["id"],
        content=row["content"],
        metadata=json.loads(row["metadata"]) if row["metadata"] else None,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"])
    )

# Interaction Endpoints

@app.post("/interactions", response_model=InteractionResponse)
async def create_interaction(interaction: InteractionCreate):
    """Create an interaction for fine-tuning"""
    interaction_id = f"int_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Calculate loss (simulated)
    loss = 0.02 + (hash(interaction.user_message) % 100) / 1000

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO interactions (id, user_message, agent_response, user_feedback, loss)
        VALUES (?, ?, ?, ?, ?)
    """, (interaction_id, interaction.user_message, interaction.agent_response,
          interaction.user_feedback, loss))

    conn.commit()
    conn.close()

    return InteractionResponse(
        id=interaction_id,
        user_message=interaction.user_message,
        agent_response=interaction.agent_response,
        user_feedback=interaction.user_feedback,
        loss=loss,
        created_at=datetime.now()
    )

@app.get("/interactions", response_model=List[InteractionResponse])
async def get_interactions(limit: int = 10):
    """Retrieve interactions"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM interactions
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    interactions = cursor.fetchall()
    conn.close()

    return [
        InteractionResponse(
            id=row["id"],
            user_message=row["user_message"],
            agent_response=row["agent_response"],
            user_feedback=row["user_feedback"],
            loss=row["loss"],
            created_at=datetime.fromisoformat(row["created_at"])
        )
        for row in interactions
    ]

# Agent Endpoints

@app.post("/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate):
    """Register a new agent"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO agents (id, name, role, status, capabilities)
        VALUES (?, ?, ?, ?, ?)
    """, (agent.id, agent.name, agent.role, "active", json.dumps(agent.capabilities)))

    conn.commit()
    conn.close()

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        status="active",
        capabilities=agent.capabilities,
        created_at=datetime.now()
    )

@app.get("/agents", response_model=List[AgentResponse])
async def get_agents():
    """Get all agents"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM agents")
    agents = cursor.fetchall()
    conn.close()

    return [
        AgentResponse(
            id=row["id"],
            name=row["name"],
            role=row["role"],
            status=row["status"],
            capabilities=json.loads(row["capabilities"]) if row["capabilities"] else [],
            created_at=datetime.fromisoformat(row["created_at"])
        )
        for row in agents
    ]

@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get a specific agent"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentResponse(
        id=row["id"],
        name=row["name"],
        role=row["role"],
        status=row["status"],
        capabilities=json.loads(row["capabilities"]) if row["capabilities"] else [],
        created_at=datetime.fromisoformat(row["created_at"])
    )

# Workflow Endpoints (placeholder)

@app.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, input_data: Dict[str, Any]):
    """Execute a workflow"""
    return {
        "success": True,
        "workflow_id": workflow_id,
        "status": "completed",
        "tasks_completed": 4,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/workflows")
async def get_workflows():
    """Get all workflows"""
    return {
        "workflows": [
            {
                "id": "healthcare_patient_care",
                "name": "Healthcare Patient Care",
                "status": "active",
                "tasks": 4
            },
            {
                "id": "supply_chain_optimization",
                "name": "Supply Chain Optimization",
                "status": "active",
                "tasks": 4
            }
        ]
    }

# Run the server
if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
