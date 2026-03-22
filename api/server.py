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

import sys
import os
# Add project root to sys.path to allow importing modules from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import logging
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

# Core Imports
try:
    from enhanced_memory import EnhancedMemoryStorage
    from agent_collaboration import AgentCollaboration
    from core.security import JWTManager, Role, Permission, verify_password, hash_password
except ImportError as e:
    # Fallback for when running from different directories
    print(f"Import Error: {e}")
    # Try local import if running as script from root
    from enhanced_memory import EnhancedMemoryStorage
    from agent_collaboration import AgentCollaboration
    from core.security import JWTManager, Role, Permission, verify_password, hash_password

from core.db import get_conn, get_db_path
from core.migrations import run_migrations
from core.rate_limiter import RateLimitMiddleware

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database & Managers
# ---------------------------------------------------------------------------

DB_PATH = get_db_path()

# Instantiate Core Managers
storage = EnhancedMemoryStorage(db_path=DB_PATH)
collab = AgentCollaboration(db_path=DB_PATH)

# Secret key: MUST be set in production
_secret_key = os.getenv("NOVA_SECRET_KEY")
if not _secret_key:
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise RuntimeError(
            "NOVA_SECRET_KEY environment variable is required in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    _secret_key = "nova_dev_secret_DO_NOT_USE_IN_PRODUCTION"
    logger.warning("Using insecure development secret key. Set NOVA_SECRET_KEY in production.")

jwt_manager = JWTManager(secret_key=_secret_key, expiration_hours=24)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ---------------------------------------------------------------------------
# User store (password-based auth)
# ---------------------------------------------------------------------------

def _get_admin_credentials() -> Dict[str, str]:
    """Load admin credentials from environment or fail in production."""
    username = os.getenv("NOVA_ADMIN_USERNAME")
    password = os.getenv("NOVA_ADMIN_PASSWORD")

    if not username or not password:
        if os.getenv("ENVIRONMENT", "development").lower() == "production":
            raise RuntimeError(
                "NOVA_ADMIN_USERNAME and NOVA_ADMIN_PASSWORD must be set in production."
            )
        logger.warning("Using default admin credentials. Set NOVA_ADMIN_USERNAME/NOVA_ADMIN_PASSWORD.")
        return {"username": "admin", "password_hash": "", "salt": ""}

    pw_hash, salt = hash_password(password)
    return {"username": username, "password_hash": pw_hash, "salt": salt}


ADMIN_CREDENTIALS = _get_admin_credentials()


@contextmanager
def _get_conn():
    """Get a raw connection for tables not managed by core classes."""
    with get_conn(DB_PATH) as conn:
        yield conn


def _get_cors_origins() -> List[str]:
    """Parse CORS origins from environment variable."""
    raw = os.getenv("CORS_ORIGINS", '["*"]')
    try:
        origins = json.loads(raw)
        if isinstance(origins, list):
            return origins
    except (json.JSONDecodeError, TypeError):
        pass
    return [o.strip() for o in raw.split(",") if o.strip()]

def _init_db():
    """Run database migrations to ensure schema is up to date."""
    applied = run_migrations(DB_PATH)
    if applied:
        logger.info("Applied %d database migration(s) to %s", applied, DB_PATH)
    else:
        logger.info("Database schema up to date at %s", DB_PATH)


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
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

_cors_origins = _get_cors_origins()
if _cors_origins == ["*"]:
    logger.warning("CORS is configured to allow all origins. Restrict CORS_ORIGINS in production.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Rate limiting middleware (configurable via env vars)
app.add_middleware(RateLimitMiddleware, db_path=DB_PATH)

# ---------------------------------------------------------------------------
# Security Dependency
# ---------------------------------------------------------------------------

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt_manager.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)):
    if not token:
        return None
    return jwt_manager.verify_token(token)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class Token(BaseModel):
    access_token: str
    token_type: str

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
    updated_at: Optional[str] = None
    access_count: int = 0

class ContextRequest(BaseModel):
    query: str
    limit: int = 5
    agent_id: Optional[str] = None

class ContextResponse(BaseModel):
    context: str
    sources: List[Dict[str, Any]]

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

# Collaboration Schemas
class SpaceCreate(BaseModel):
    space_name: str
    creator: str
    members: Optional[List[str]] = None
    permissions: Optional[Dict[str, Any]] = None

class ShareMemoryRequest(BaseModel):
    from_agent: str
    to_agent: str
    memory_id: str
    access_level: str = "read"
    expires_at: Optional[str] = None

# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------

@app.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and receive a JWT token."""
    # Verify against configured admin credentials
    if form_data.username == ADMIN_CREDENTIALS["username"]:
        if ADMIN_CREDENTIALS["password_hash"]:
            # Production: verify against hashed password
            if verify_password(form_data.password, ADMIN_CREDENTIALS["password_hash"], ADMIN_CREDENTIALS["salt"]):
                access_token = jwt_manager.create_token(
                    agent_id=form_data.username,
                    role=Role.ADMIN,
                    permissions=[Permission.ADMIN_ALL]
                )
                return {"access_token": access_token, "token_type": "bearer"}
        else:
            # Development fallback only (no password hash configured)
            dev_password = os.getenv("NOVA_ADMIN_PASSWORD", "admin")
            if form_data.password == dev_password:
                access_token = jwt_manager.create_token(
                    agent_id=form_data.username,
                    role=Role.ADMIN,
                    permissions=[Permission.ADMIN_ALL]
                )
                return {"access_token": access_token, "token_type": "bearer"}

    # Allow agents to self-authenticate with agent secret
    agent_secret = os.getenv("NOVA_AGENT_SECRET", "nova_agent_secret")
    if form_data.password == agent_secret:
        access_token = jwt_manager.create_token(
            agent_id=form_data.username,
            role=Role.AGENT
        )
        return {"access_token": access_token, "token_type": "bearer"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

# ---------------------------------------------------------------------------
# System Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["System"])
async def root():
    """API root — returns version and available endpoint groups."""
    return {
        "name": "Nova Memory 2.1",
        "version": "2.1.0",
        "description": "Real-Time AI Agent Memory Management System",
        "docs": "/docs",
        "features": [
            "Enhanced Compression & Versioning",
            "Auto-Capture Interactions",
            "Multi-Agent Collaboration",
            "JWT Authentication"
        ]
    }

@app.get("/health", tags=["System"])
async def health_check():
    """Liveness probe."""
    stats = storage.get_memory_stats()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "database": "connected",
        "stats": stats
    }

# ---------------------------------------------------------------------------
# Memory Endpoints (Enhanced)
# ---------------------------------------------------------------------------

@app.post("/memories", response_model=MemoryResponse, status_code=201, tags=["Memories"])
async def create_memory(memory: MemoryCreate, current_user: dict = Depends(get_current_user)):
    """Store a new memory (Authenticated)."""
    # Use the authenticated user as author if not provided
    author = memory.author or current_user.get("agent_id")

    mid = storage.add_memory(
        content=memory.content,
        metadata=memory.metadata,
        tags=memory.tags,
        author=author
    )

    if not mid:
        raise HTTPException(status_code=500, detail="Failed to store memory")

    # Fetch back to return response
    mem_data = storage.get_memory(mid)
    return MemoryResponse(**mem_data)

@app.post("/memories/context", response_model=ContextResponse, tags=["Memories"])
async def get_memory_context(request: ContextRequest):
    """
    Swift Retrieval: Get consolidated context for an agent query.
    Returns a single string formatted for LLM injection.
    """
    results = storage.search_memories(
        query=request.query,
        limit=request.limit
    )

    context_parts = []
    for idx, res in enumerate(results, 1):
        context_parts.append(f"[Memory {idx}] (Score: High): {res['content']}")

    consolidated_context = "\n\n".join(context_parts)

    return ContextResponse(
        context=consolidated_context,
        sources=results
    )

@app.get("/memories", response_model=List[MemoryResponse], tags=["Memories"])
async def list_memories(
    query: Optional[str] = Query(None, description="Full-text search query"),
    tags: Optional[str] = Query(None, description="Comma-separated tag filter"),
    author: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List or search memories."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    if query:
        results = storage.search_memories(query, tags=tag_list, limit=limit)
    else:
        results = storage.list_memories(tags=tag_list, author=author, limit=limit, offset=offset)

    return [MemoryResponse(**r) for r in results]

@app.get("/memories/{memory_id}", response_model=MemoryResponse, tags=["Memories"])
async def get_memory(memory_id: str):
    """Retrieve a single memory by ID."""
    mem_data = storage.get_memory(memory_id)
    if not mem_data:
        raise HTTPException(status_code=404, detail="Memory not found")
    return MemoryResponse(**mem_data)

@app.patch("/memories/{memory_id}", tags=["Memories"])
async def update_memory(memory_id: str, update: MemoryUpdate, current_user: dict = Depends(get_current_user)):
    """Partially update a memory (Authenticated)."""
    success = storage.update_memory(
        memory_id=memory_id,
        content=update.content,
        metadata=update.metadata,
        tags=update.tags
    )

    if not success:
        raise HTTPException(status_code=404, detail="Memory not found or update failed")

    mem_data = storage.get_memory(memory_id)
    return MemoryResponse(**mem_data)

@app.delete("/memories/{memory_id}", status_code=204, tags=["Memories"])
async def delete_memory(memory_id: str, current_user: dict = Depends(get_current_user)):
    """Permanently delete a memory (Authenticated)."""
    success = storage.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")

# ---------------------------------------------------------------------------
# Interaction Endpoints (Auto-Capture)
# ---------------------------------------------------------------------------

@app.post("/interactions", response_model=InteractionResponse, status_code=201, tags=["Interactions"])
async def create_interaction(
    interaction: InteractionCreate,
    auto_capture: bool = Query(False, description="Automatically save as memory")
):
    """
    Log an interaction.
    If `auto_capture=True`, stores the interaction as an episodic memory.
    """
    interaction_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Loss placeholder logic
    loss = round(0.05 + (abs(hash(interaction.user_message)) % 100) / 2000, 4)
    if interaction.user_feedback == "positive":
        loss *= 0.5
    elif interaction.user_feedback == "negative":
        loss *= 1.5

    with _get_conn() as conn:
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

    # Auto-Capture Logic
    if auto_capture:
        content = f"Interaction with Agent {interaction.agent_id}:\nUser: {interaction.user_message}\nAgent: {interaction.agent_response}"
        storage.add_memory(
            content=content,
            metadata={"type": "interaction", "interaction_id": interaction_id, "loss": loss},
            tags=["interaction", "episodic", f"agent:{interaction.agent_id}"],
            author=interaction.agent_id or "system"
        )

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
    """List recent interactions."""
    with _get_conn() as conn:
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
# Collaboration Endpoints (New)
# ---------------------------------------------------------------------------

@app.post("/collaboration/spaces", tags=["Collaboration"])
async def create_collaborative_space(space: SpaceCreate, current_user: dict = Depends(get_current_user)):
    """Create a new collaborative space."""
    # Ensure creator is consistent
    creator = space.creator or current_user.get("agent_id")

    space_id = collab.create_collaborative_space(
        space_name=space.space_name,
        creator=creator,
        members=space.members,
        permissions=space.permissions
    )

    if not space_id:
        raise HTTPException(status_code=400, detail="Failed to create space (name might be taken)")

    return {"space_id": space_id, "status": "created"}

@app.get("/collaboration/spaces", tags=["Collaboration"])
async def list_spaces(agent_id: str):
    """List spaces an agent is a member of."""
    return collab.list_collaborative_spaces(agent_id)

@app.post("/collaboration/share", tags=["Collaboration"])
async def share_memory(share: ShareMemoryRequest, current_user: dict = Depends(get_current_user)):
    """Share a memory with another agent."""
    share_id = collab.share_memory_with_agent(
        from_agent=share.from_agent,
        to_agent=share.to_agent,
        memory_id=share.memory_id,
        access_level=share.access_level,
        expires_at=share.expires_at
    )

    if not share_id:
        raise HTTPException(status_code=400, detail="Failed to share memory")

    return {"share_id": share_id, "status": "shared"}

@app.get("/collaboration/shares/{agent_id}", tags=["Collaboration"])
async def get_shares(agent_id: str):
    """Get active shares for an agent."""
    return collab.get_agent_memory_shares(agent_id)

# ---------------------------------------------------------------------------
# Agent Endpoints (Legacy Wrapper)
# ---------------------------------------------------------------------------

@app.post("/agents", response_model=AgentResponse, status_code=201, tags=["Agents"])
async def create_agent(agent: AgentCreate, current_user: dict = Depends(get_current_user)):
    """Register a new agent."""
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
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
    """List all registered agents."""
    with _get_conn() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM agents WHERE status = ?", (status,))
        else:
            cursor.execute("SELECT * FROM agents ORDER BY created_at DESC")
        rows = cursor.fetchall()

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

# ---------------------------------------------------------------------------
# Workflow Endpoints (Stub/Passthrough)
# ---------------------------------------------------------------------------

@app.get("/workflows", tags=["Workflows"])
async def list_workflows():
    """List all registered workflows."""
    with _get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflows ORDER BY created_at DESC")
        rows = cursor.fetchall()

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
