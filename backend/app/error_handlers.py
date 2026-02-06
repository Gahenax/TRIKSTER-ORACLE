from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def error_response(
    *,
    status_code: int,
    error_code: str,
    message: str,
    path: str,
    request_id: str | None,
) -> JSONResponse:
    payload: Dict[str, Any] = {
        "error_code": error_code,
        "message": message,
        "path": path,
        "request_id": request_id,
        "timestamp": _utc_iso(),
    }
    return JSONResponse(status_code=status_code, content=payload)

def install_error_handlers(app) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # This covers 404, 405 and any HTTPException thrown by Starlette/FastAPI routing.
        request_id = request.headers.get("x-request-id")
        status = int(getattr(exc, "status_code", 500) or 500)
        # Normalize codes
        if status == 404:
            code = "not_found"
            msg = "Resource not found"
        elif status == 405:
            code = "method_not_allowed"
            msg = "Method not allowed"
        elif status == 429:
            code = "rate_limit_exceeded"
            msg = "Rate limit exceeded"
        else:
            code = "http_error"
            msg = str(getattr(exc, "detail", "HTTP error"))

        return error_response(
            status_code=status,
            error_code=code,
            message=msg,
            path=str(request.url.path),
            request_id=request_id,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = request.headers.get("x-request-id")
        return error_response(
            status_code=422,
            error_code="validation_error",
            message="Request validation failed",
            path=str(request.url.path),
            request_id=request_id,
        )