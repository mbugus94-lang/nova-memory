"""
Rate Limiting Middleware for Nova Memory API.
Uses a sliding window approach backed by SQLite for persistence.
"""

import os
import time
import sqlite3
import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using a sliding window algorithm.

    Configuration (via environment):
        RATE_LIMIT_ENABLED: Enable/disable (default: false)
        RATE_LIMIT_REQUESTS: Max requests per window (default: 100)
        RATE_LIMIT_PERIOD: Window size in seconds (default: 60)
    """

    def __init__(self, app, db_path: Optional[str] = None):
        super().__init__(app)
        self.enabled = _get_bool_env("RATE_LIMIT_ENABLED", False)
        self.max_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.period_seconds = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
        self.db_path = db_path or os.getenv("DATABASE_PATH", "nova_memory_v2.db")

        if self.enabled:
            self._init_table()
            logger.info(
                "Rate limiting enabled: %d requests per %ds",
                self.max_requests,
                self.period_seconds,
            )

    def _init_table(self):
        """Ensure rate_limits table exists."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    client_id    TEXT NOT NULL,
                    endpoint     TEXT NOT NULL,
                    window_start INTEGER NOT NULL,
                    request_count INTEGER DEFAULT 1,
                    PRIMARY KEY (client_id, endpoint, window_start)
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Failed to init rate limiting table: %s", e)
            self.enabled = False

    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Try authenticated user first
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return f"token:{auth[7:16]}"  # First 8 chars of token

        # Fall back to IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _check_rate_limit(self, client_id: str, endpoint: str) -> tuple[bool, dict]:
        """
        Check if client is within rate limits.

        Returns (is_allowed, headers_dict).
        """
        window_start = int(time.time()) // self.period_seconds * self.period_seconds

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Clean old windows
            cursor.execute(
                "DELETE FROM rate_limits WHERE window_start < ?",
                (window_start - self.period_seconds,),
            )

            # Get or create counter
            cursor.execute(
                "SELECT request_count FROM rate_limits WHERE client_id = ? AND endpoint = ? AND window_start = ?",
                (client_id, endpoint, window_start),
            )
            row = cursor.fetchone()

            if row:
                count = row[0] + 1
                cursor.execute(
                    "UPDATE rate_limits SET request_count = ? WHERE client_id = ? AND endpoint = ? AND window_start = ?",
                    (count, client_id, endpoint, window_start),
                )
            else:
                count = 1
                cursor.execute(
                    "INSERT INTO rate_limits (client_id, endpoint, window_start, request_count) VALUES (?, ?, ?, 1)",
                    (client_id, endpoint, window_start),
                )

            conn.commit()
            conn.close()

            remaining = max(0, self.max_requests - count)
            headers = {
                "X-RateLimit-Limit": str(self.max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(window_start + self.period_seconds),
            }

            return count <= self.max_requests, headers

        except Exception as e:
            logger.error("Rate limit check failed: %s", e)
            return True, {}  # Allow on error

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for health and root endpoints
        if request.url.path in ("/health", "/", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        client_id = self._get_client_id(request)
        endpoint = f"{request.method}:{request.url.path}"

        is_allowed, headers = self._check_rate_limit(client_id, endpoint)

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": headers.get("X-RateLimit-Reset"),
                },
                headers=headers,
            )

        response = await call_next(request)
        for key, value in headers.items():
            response.headers[key] = value
        return response
