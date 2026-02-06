from __future__ import annotations
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# In-memory store (will be Redis in Phase 4)
_idempotency_store: Dict[str, tuple[Response, datetime]] = {}
IDEMPOTENCY_TTL = timedelta(hours=24)

class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only apply to POST/PUT/PATCH/DELETE
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return await call_next(request)

        # Get idempotency key from header
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            # No key provided, proceed normally
            return await call_next(request)

        # Check if we've seen this key before
        if idempotency_key in _idempotency_store:
            cached_response, timestamp = _idempotency_store[idempotency_key]
            # Check TTL
            if datetime.now() - timestamp < IDEMPOTENCY_TTL:
                # Return cached response
                return Response(
                    content=cached_response.body,
                    status_code=cached_response.status_code,
                    headers=dict(cached_response.headers),
                    media_type=cached_response.media_type
                )
            else:
                # Expired, remove from cache
                del _idempotency_store[idempotency_key]

        # Process request
        response = await call_next(request)

        # Cache successful responses (200-299)
        if 200 <= response.status_code < 300:
            _idempotency_store[idempotency_key] = (response, datetime.now())

        return response
