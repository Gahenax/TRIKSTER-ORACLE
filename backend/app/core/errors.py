"""
Global exception handlers for unified error responses.

Handles:
- HTTPException (4xx/5xx from route code)
- RequestValidationError (422 from Pydantic validation)
- Generic Exception (500 catch-all)

All errors return ErrorResponse model with request_id.
Stack traces are never exposed in production (ENV != 'development').
"""
import os
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from app.schemas.error import ErrorResponse
from app.logging import get_logger

logger = get_logger(__name__)


def _get_request_id(request: Request) -> str:
    """
    Extract request_id from request state or X-Request-ID header.
    
    Request state is set by RequestIDMiddleware.
    Fallback to header if state not available.
    """
    # Try request.state.request_id first (set by middleware)
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    
    # Fallback to header
    return request.headers.get("X-Request-ID", "unknown")


def _is_production() -> bool:
    """Check if running in production environment."""
    env = os.environ.get("ENV", "development").lower()
    return env in ["production", "prod", "staging"]


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPException (raised via raise HTTPException).
    
    Maps status code to error_code and returns unified ErrorResponse.
    """
    request_id = _get_request_id(request)
    
    # Map status code to error code
    status_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        413: "PAYLOAD_TOO_LARGE",
        415: "UNSUPPORTED_MEDIA_TYPE",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    
    error_code = status_code_map.get(exc.status_code, "HTTP_ERROR")
    
    # If detail is a dict, use it as details; else use as message
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", "An error occurred")
        details = exc.detail.get("details")
    else:
        message = str(exc.detail)
        details = None
    
    error_response = ErrorResponse(
        error_code=error_code,
        message=message,
        request_id=request_id,
        details=details
    )
    
    # Log error (INFO for 4xx, WARNING for 5xx)
    log_level = "info" if exc.status_code < 500 else "warning"
    logger.log(
        getattr(logger, log_level).__self__.level,
        f"{error_code}: {message}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
        headers={"Content-Type": "application/json"}
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors (422).
    
    Converts Pydantic validation error to unified ErrorResponse.
    """
    request_id = _get_request_id(request)
    
    # Extract validation errors
    validation_errors = exc.errors()
    
    # Format details
    details = {
        "validation_errors": [
            {
                "loc": list(err["loc"]),
                "msg": err["msg"],
                "type": err["type"],
            }
            for err in validation_errors
        ]
    }
    
    error_response = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        request_id=request_id,
        details=details
    )
    
    logger.info(
        f"Validation error: {len(validation_errors)} fields",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "validation_errors": len(validation_errors),
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
        headers={"Content-Type": "application/json"}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions (500).
    
    NEVER exposes stack traces in production.
    Logs full exception details for debugging.
    """
    request_id = _get_request_id(request)
    
    # Log full exception (with stack trace)
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
        exc_info=True  # Include stack trace in logs
    )
    
    # In development, include exception type in details
    details = None
    if not _is_production():
        details = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            # Never include full stack trace even in dev (too verbose)
        }
    
    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An internal server error occurred",
        request_id=request_id,
        details=details
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
        headers={"Content-Type": "application/json"}
    )
