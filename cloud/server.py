"""
Nova Memory Cloud - Main Server

Production API server with cloud features:
- API Key Authentication
- Usage Tracking
- Rate Limiting
- Multi-tenant support

Run with:
    python -m cloud.server
    # or
    uvicorn cloud.server:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.db import init_db, get_db_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Nova Memory Cloud...")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down Nova Memory Cloud...")


app = FastAPI(
    title="Nova Memory Cloud API",
    description="Cloud API for AI Agent Memory - Persistent, Searchable, Collaborative",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.memory_routes import router as memory_router
from api.advanced_routes import router as advanced_router
from cloud.routes import router as cloud_router

app.include_router(memory_router)
app.include_router(advanced_router)
app.include_router(cloud_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0", "service": "nova-memory-cloud"}


@app.get("/")
async def root():
    return {
        "name": "Nova Memory Cloud",
        "version": "2.0.0",
        "docs": "/api/docs",
        "cloud": {
            "tiers": "/api/cloud/tiers",
            "keys": "/api/cloud/keys",
            "usage": "/api/cloud/usage"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
