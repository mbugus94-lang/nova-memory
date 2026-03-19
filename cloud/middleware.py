"""
Nova Memory Cloud - Usage Tracking Middleware

Middleware to track API usage and enforce rate limits.
"""

import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from cloud.api_keys import APIKeyManager


class CloudUsageMiddleware(BaseHTTPMiddleware):
    """Middleware to track API usage and enforce rate limits"""
    
    PUBLIC_ENDPOINTS = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/cloud/tiers",
        "/api/cloud/keys",
    ]
    
    CLOUD_ENDPOINTS = [
        "/api/cloud/",
    ]
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        path = request.url.path
        
        if any(path.startswith(endpoint) for endpoint in self.PUBLIC_ENDPOINTS):
            return await call_next(request)
        
        if any(path.startswith(endpoint) for endpoint in self.CLOUD_ENDPOINTS):
            return await call_next(request)
        
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "API key required. Use X-API-Key header."}
            )
        
        manager = APIKeyManager()
        key = manager.verify_api_key(api_key)
        
        if not key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired API key."}
            )
        
        if not key.is_active:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "API key has been revoked."}
            )
        
        can_proceed, message = manager.check_rate_limit(key)
        if not can_proceed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": f"Rate limit exceeded: {message}"}
            )
        
        request.state.api_key = key
        request.state.api_key_id = key.id
        
        try:
            response = await call_next(request)
        except Exception as e:
            raise e
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        tokens = int(request.headers.get("X-Tokens-Used", 0))
        
        manager.record_usage(
            api_key_id=key.id,
            endpoint=path,
            method=request.method,
            tokens=tokens,
            latency_ms=latency_ms
        )
        
        response.headers["X-RateLimit-Limit"] = str(manager.get_tier_limits(key.tier)["rpm"])
        response.headers["X-RateLimit-Remaining"] = str(
            manager.get_tier_limits(key.tier)["monthly_requests"] - key.monthly_requests
        )
        
        return response
