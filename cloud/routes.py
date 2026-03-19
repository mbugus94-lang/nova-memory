"""
Nova Memory Cloud - Cloud API Routes

REST API for managing API keys, usage, and cloud features.
"""

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import time

from cloud.api_keys import APIKeyManager, TIER_LIMITS, APIKey
from core.db import get_db_path


router = APIRouter(prefix="/api/cloud", tags=["Cloud API"])

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_api_key(api_key: str = Header(None)) -> APIKey:
    """Dependency to get and verify API key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Use X-API-Key header."
        )
    
    manager = APIKeyManager()
    key = manager.verify_api_key(api_key)
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key."
        )
    
    if not key.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key has been revoked."
        )
    
    can_proceed, message = manager.check_rate_limit(key)
    if not can_proceed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {message}"
        )
    
    return key


class CreateAPIKeyRequest(BaseModel):
    name: str
    tier: str = "free"


class APIKeyResponse(BaseModel):
    id: str
    name: str
    tier: str
    monthly_requests: int
    monthly_tokens: int
    created_at: str
    expires_at: Optional[str] = None
    is_active: bool


class APIKeyWithSecret(BaseModel):
    id: str
    name: str
    tier: str
    api_key: str
    monthly_requests: int
    monthly_tokens: int
    created_at: str


class UsageStatsResponse(BaseModel):
    total_requests: int
    total_tokens: int
    avg_latency_ms: float
    active_days: int
    top_endpoints: List[dict]


class TierInfo(BaseModel):
    name: str
    rpm: int
    monthly_requests: int
    monthly_tokens: int
    max_memories: int
    features: List[str]


@router.get("/tiers", response_model=List[TierInfo])
async def list_tiers():
    """List available pricing tiers"""
    return [
        TierInfo(name=tier, **limits)
        for tier, limits in TIER_LIMITS.items()
    ]


@router.post("/keys", response_model=APIKeyWithSecret)
async def create_api_key(
    request: CreateAPIKeyRequest,
    user_id: str = "default_user"
):
    """Create a new API key"""
    if request.tier not in TIER_LIMITS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier. Available: {list(TIER_LIMITS.keys())}"
        )
    
    manager = APIKeyManager()
    key_id, raw_key = manager.create_api_key(request.name, user_id, request.tier)
    
    key = manager.verify_api_key(raw_key)
    
    return APIKeyWithSecret(
        id=key.id,
        name=key.name,
        tier=key.tier,
        api_key=raw_key,
        monthly_requests=key.monthly_requests,
        monthly_tokens=key.monthly_tokens,
        created_at=key.created_at.isoformat()
    )


@router.get("/keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_key: APIKey = Depends(get_current_api_key)
):
    """List all API keys for the authenticated user"""
    manager = APIKeyManager()
    keys = manager.list_api_keys(current_key.user_id)
    
    return [
        APIKeyResponse(
            id=k.id,
            name=k.name,
            tier=k.tier,
            monthly_requests=k.monthly_requests,
            monthly_tokens=k.monthly_tokens,
            created_at=k.created_at.isoformat(),
            expires_at=k.expires_at.isoformat() if k.expires_at else None,
            is_active=k.is_active
        )
        for k in keys
    ]


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_key: APIKey = Depends(get_current_api_key)
):
    """Revoke an API key"""
    manager = APIKeyManager()
    
    keys = manager.list_api_keys(current_key.user_id)
    if not any(k.id == key_id for k in keys):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    success = manager.revoke_api_key(key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )
    
    return {"status": "revoked", "key_id": key_id}


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    days: int = 30,
    current_key: APIKey = Depends(get_current_api_key)
):
    """Get usage statistics for the current API key"""
    manager = APIKeyManager()
    stats = manager.get_usage_stats(current_key.id, days)
    
    return UsageStatsResponse(**stats)


@router.get("/limits")
async def get_limits(current_key: APIKey = Depends(get_current_api_key)):
    """Get rate limits for the current API key"""
    manager = APIKeyManager()
    limits = manager.get_tier_limits(current_key.tier)
    used = {
        "requests": current_key.monthly_requests,
        "tokens": current_key.monthly_tokens
    }
    
    return {
        "tier": current_key.tier,
        "limits": limits,
        "used": used,
        "remaining": {
            "requests": max(0, limits["monthly_requests"] - used["requests"]) if limits["monthly_requests"] > 0 else -1,
            "tokens": max(0, limits["monthly_tokens"] - used["tokens"]) if limits["monthly_tokens"] > 0 else -1
        }
    }


@router.get("/me")
async def get_current_key_info(current_key: APIKey = Depends(get_current_api_key)):
    """Get information about the current API key"""
    manager = APIKeyManager()
    limits = manager.get_tier_limits(current_key.tier)
    
    return {
        "id": current_key.id,
        "name": current_key.name,
        "tier": current_key.tier,
        "created_at": current_key.created_at.isoformat(),
        "is_active": current_key.is_active,
        "limits": limits
    }
