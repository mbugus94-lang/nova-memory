"""Health check routes for Nova Memory API."""
import time
from fastapi import APIRouter
from pydantic import BaseModel
import os

router = APIRouter()

# Track start time for uptime calculation
start_time = time.time()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: int
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthResponse(
        status="ok",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        uptime_seconds=int(time.time() - start_time),
        version=os.environ.get("APP_VERSION", "2.1.0")
    )
