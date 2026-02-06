"""
Request ID Middleware
Generates unique X-Request-ID for each request for observability and tracing.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates a unique request ID for each incoming request.
    If X-Request-ID header exists, it's used; otherwise a new UUID is generated.
    The request ID is attached to the response headers and made available to downstream handlers.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Attach request ID to request state for access in route handlers
        request.state.request_id = request_id
        
        # Record start time for duration calculation
        start_time = time.time()
        
        # Process request
        response: Response = await call_next(request)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Attach metadata to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(duration_ms)
        
        # Also attach duration to request state for logging
        request.state.duration_ms = duration_ms
        
        return response
