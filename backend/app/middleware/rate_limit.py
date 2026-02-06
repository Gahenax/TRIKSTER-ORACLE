from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
import os

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["30/minute"],  # Default for undecorated endpoints
    storage_uri="memory://"  # In-memory (will migrate to Redis in Phase 4)
)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handler for 429 Too Many Requests
    Integrates with unified error contract
    """
    from datetime import datetime, timezone

    request_id = request.headers.get("x-request-id")

    # Extract rate limit info from exception
    retry_after = getattr(exc, 'retry_after', None) or 60

    payload = {
        "error_code": "rate_limit_exceeded",
        "message": f"Rate limit exceeded. Try again in {int(retry_after)} seconds.",
        "path": str(request.url.path),
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    headers = {
        "Retry-After": str(int(retry_after)),
        "X-RateLimit-Limit": request.headers.get("X-RateLimit-Limit", "unknown"),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(int(retry_after)),
    }

    return JSONResponse(
        status_code=429,
        content=payload,
        headers=headers
    )

# Rate limit tiers (can be used as decorators)
TIER_SYSTEM = "100/minute"      # /health, /ready, /version
TIER_MUTATING = "10/minute"     # POST /simulate, DELETE /cache/clear
TIER_READ = "30/minute"         # GET endpoints (default)
