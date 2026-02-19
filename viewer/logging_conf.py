from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict

from starlette.requests import Request
from starlette.responses import Response


logger = logging.getLogger("viewer")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def log_event(data: Dict[str, Any]) -> None:
    logger.info(json.dumps(data, ensure_ascii=False, separators=(",", ":")))


class AccessLogMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.time()
        status_code_holder = {"status": None}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code_holder["status"] = message["status"]
            await send(message)

        await self.app(scope, receive, send_wrapper)
        latency_ms = int((time.time() - start) * 1000)

        # request_id injected via RequestIdMiddleware as header; we also try to read from scope state.
        headers = dict(scope.get("headers") or [])
        xrid = headers.get(b"x-request-id", b"").decode("utf-8") if headers else ""
        path = scope.get("path", "")
        method = scope.get("method", "")
        status = status_code_holder["status"]

        log_event(
            {
                "ts": time.time(),
                "kind": "access",
                "method": method,
                "path": path,
                "status": status,
                "latency_ms": latency_ms,
                "request_id": xrid or None,
            }
        )
