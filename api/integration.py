"""
Nova Memory 2.0 - Advanced Features Integration Guide

This file shows how to integrate all advanced features into your main FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import os

# Import advanced systems
from core.advanced_features import init_nova_memory_advanced, get_nova_memory_advanced
from api.advanced_routes import router as advanced_router
from api.memory_routes import router as memory_router

# Optional GraphQL support
try:
    from api.graphql_api import schema as graphql_schema
    from starlette_graphene_django import GraphQLView
    GRAPHQL_AVAILABLE = True
except ImportError:
    GRAPHQL_AVAILABLE = False
    print("[WARNING] GraphQL not available - graphene or starlette integration not installed")

# ==============================================================================
# Lifecycle Management
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup/shutdown events.
    Handles initialization and cleanup of all advanced systems.
    """
    # Startup
    print("[STARTUP] Starting Nova Memory 2.0 Advanced Features...")
    try:
        _load_env_files()

        # Initialize all advanced systems
        system = init_nova_memory_advanced(
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=_get_int_env("REDIS_PORT", 6379),
            redis_db=_get_int_env("REDIS_DB", 0),
            redis_password=os.getenv("REDIS_PASSWORD") or None,
            cache_ttl=_get_int_env("REDIS_CACHE_TTL", 3600),
            enable_cache=_get_bool_env("NOVA_CACHE_ENABLED", False),
            enable_semantic_search=_get_bool_env("NOVA_ENABLE_SEMANTIC_SEARCH", False),
            enable_encryption=_get_bool_env("NOVA_ENABLE_ENCRYPTION", False),
            enable_messaging=_get_bool_env("NOVA_ENABLE_MESSAGING", True),
            semantic_model=os.getenv("MODEL_NAME") or os.getenv("EMBEDDING_MODEL"),
        )
        
        # Verify health
        health = system.health_check()
        print(f"[OK] System health: {health}")
        
        # Log stats
        stats = system.get_system_stats()
        print(f"[OK] System initialized with {len(stats)} subsystems")
        
    except Exception as e:
        print(f"[WARNING] Error during startup: {e}")
        print("  Features may have reduced functionality")
    
    yield
    
    # Shutdown
    print("[SHUTDOWN] Shutting down Nova Memory 2.0...")
    try:
        system = get_nova_memory_advanced()
        if system:
            print("[OK] Advanced features shutdown complete")
    except Exception as e:
        print(f"[WARNING] Error during shutdown: {e}")


# ==============================================================================
# Create FastAPI Application
# ==============================================================================

app = FastAPI(
    title="Nova Memory 2.0",
    description="Real-Time AI Agent Memory Management System with Advanced Features",
    version="2.0.0",
    lifespan=lifespan,
)

# ==============================================================================
# CORS Configuration
# ==============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ==============================================================================
# Route Registration
# ==============================================================================

# Include advanced features router
app.include_router(advanced_router)
app.include_router(memory_router)

# Include basic router if you have one
# app.include_router(basic_router)

# ==============================================================================
# GraphQL Endpoint
# ==============================================================================

# Mount GraphQL endpoint (if available)
if GRAPHQL_AVAILABLE:
    try:
        app.add_route(
            "/graphql",
            GraphQLView.as_view(schema=graphql_schema),
        )
    except Exception as e:
        print(f"⚠ GraphQL endpoint could not be mounted: {e}")

# ==============================================================================
# Environment helpers
# ==============================================================================


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _load_env_files() -> None:
    project_root = Path(__file__).resolve().parents[1]
    env_paths = [
        project_root / ".env.central",
        project_root / ".env",
    ]

    for env_path in env_paths:
        if not env_path.exists():
            continue
        try:
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        except Exception as exc:
            print(f"âš  Warning: failed to load {env_path}: {exc}")

# ==============================================================================
# Root Endpoints
# ==============================================================================

@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "name": "Nova Memory 2.0",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "graphql": "/graphql",
            "advanced_api": "/api/v2/*"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        system = get_nova_memory_advanced()
        if system:
            health_status = system.health_check()
            return {
                "status": "healthy" if all(health_status.values()) else "degraded",
                "components": health_status
            }
        else:
            return {"status": "initializing"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/stats")
async def stats():
    """System statistics endpoint."""
    try:
        system = get_nova_memory_advanced()
        if system:
            return system.get_system_stats()
        else:
            return {"error": "System not initialized"}
    except Exception as e:
        return {"error": str(e)}

# ==============================================================================
# Error Handlers
# ==============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for better error messages."""
    return {
        "status": "error",
        "message": str(exc),
        "type": type(exc).__name__
    }

# ==============================================================================
# Startup Logging
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    print("\n" + "="*80)
    print("NOVA MEMORY 2.0 - ADVANCED FEATURES STARTUP")
    print("="*80)
    print("\nAvailable Endpoints:")
    print("  📚 API Documentation: http://localhost:8000/docs")
    print("  📖 ReDoc: http://localhost:8000/redoc")
    print("  🔷 GraphQL: http://localhost:8000/graphql")
    print("  🚀 Advanced API v2: http://localhost:8000/api/v2/*")
    print("\nSystem Health:")
    
    try:
        system = get_nova_memory_advanced()
        if system:
            health = system.health_check()
            for component, status in health.items():
                icon = "✓" if status else "✗"
                print(f"  {icon} {component}")
    except Exception as e:
        print(f"  ⚠ Could not retrieve health status: {e}")
    
    print("\n" + "="*80 + "\n")

# ==============================================================================
# Advanced Features Quick Access from API
# ==============================================================================

# These example routes show how to use the advanced features

@app.get("/api/v2/examples/cache-demo")
async def cache_demo():
    """Example: Using Redis cache."""
    system = get_nova_memory_advanced()
    
    # Set a value
    system.cache.set("demo_key", {"value": "hello"}, ttl=3600)
    
    # Get the value
    result = system.cache.get("demo_key")
    
    return {
        "example": "Redis Cache",
        "result": result,
        "stats": system.cache.get_stats()
    }

@app.post("/api/v2/examples/semantic-search")
async def semantic_search_demo(query: str):
    """Example: Using semantic search."""
    system = get_nova_memory_advanced()
    
    # Simple example with hardcoded memories
    memories = [
        {"id": "1", "content": "The weather is sunny today"},
        {"id": "2", "content": "It's raining outside"},
        {"id": "3", "content": "The sky is blue"},
    ]
    
    # Search
    results = system.semantic_search.semantic_search(
        query=query,
        memories=memories,
        top_k=2
    )
    
    return {
        "query": query,
        "results": results
    }

@app.get("/api/v2/examples/agent-messaging")
async def messaging_demo():
    """Example: Using agent messaging."""
    from core.agent_messaging import send_message, get_message_broker
    
    # Get broker
    broker = get_message_broker()
    
    # Register example agents
    broker.register_agent("agent_001")
    broker.register_agent("agent_002")
    
    # Send message
    msg_id = send_message(
        sender="agent_001",
        recipient="agent_002",
        subject="greeting",
        content={"message": "Hello from agent 001!"}
    )
    
    # Get stats
    stats = broker.get_stats()
    
    return {
        "message_sent": msg_id is not None,
        "stats": stats
    }

# ==============================================================================
# Integration Tests
# ==============================================================================

@app.get("/api/v2/test/all-systems")
async def test_all_systems():
    """Test all advanced systems and report status."""
    system = get_nova_memory_advanced()
    
    results = {
        "timestamp": str(__import__('datetime').datetime.now()),
        "systems": {}
    }
    
    # Test each system
    tests = {
        "cache": lambda: bool(system.cache),
        "semantic_search": lambda: bool(system.semantic_search),
        "message_broker": lambda: bool(system.message_broker),
        "jwt_manager": lambda: bool(system.jwt_manager),
        "encryption": lambda: bool(system.encryption),
        "audit_log": lambda: bool(system.audit_log),
        "attributes": lambda: bool(system.attributes),
        "registry": lambda: bool(system.registry),
        "gc": lambda: bool(system.gc),
        "resolver": lambda: bool(system.resolver),
        "optimizer": lambda: bool(system.optimizer),
    }
    
    for name, test_func in tests.items():
        try:
            results["systems"][name] = {
                "available": test_func(),
                "status": "✓ ready"
            }
        except Exception as e:
            results["systems"][name] = {
                "available": False,
                "status": f"✗ {str(e)}"
            }
    
    # Summary
    available = sum(1 for s in results["systems"].values() if s["available"])
    total = len(results["systems"])
    
    results["summary"] = {
        "systems_available": f"{available}/{total}",
        "all_systems_ready": available == total
    }
    
    return results

# ==============================================================================
# Run Instructions
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Read configuration from environment variables
    agent_id = os.getenv("AGENT_ID", "default_agent")
    api_port = int(os.getenv("API_PORT", "8000"))
    
    print(f"""
    Starting Nova Memory 2.0 with Advanced Features
    
    Agent ID: {agent_id}
    Port: {api_port}
    
    🚀 Instructions:
    
    1. Ensure Redis is running (if using caching):
       redis-server
    
    2. Start the API server:
       uvicorn api.integration:app --reload --host 0.0.0.0 --port {api_port}
    
    3. Access the application:
       - API Docs: http://localhost:{api_port}/docs
       - GraphQL: http://localhost:{api_port}/graphql
       - Advanced API: http://localhost:{api_port}/api/v2/*
    
    4. Run the demo to test all features:
       python advanced_demo.py
    
    5. Check system health:
       curl http://localhost:{api_port}/health
    
    """)
    
    uvicorn.run(
        "api.integration:app",
        host="0.0.0.0",
        port=api_port,
        reload=False,
        log_level="info"
    )
