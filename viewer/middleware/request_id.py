from __future__ import annotations

import uuid
from starlette.types import ASGIApp, Receive, Scope, Send


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Find or generate Request ID
        request_id = ""
        for name, value in scope.get("headers", []):
            if name == b"x-request-id":
                request_id = value.decode("utf-8")
                break
        
        if not request_id:
            request_id = str(uuid.uuid4())
            # Inject into scope headers for downstream middlewares
            headers = list(scope.get("headers", []))
            headers.append((b"x-request-id", request_id.encode("utf-8")))
            scope["headers"] = headers

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                # Add X-Request-Id to response headers
                headers.append((b"x-request-id", request_id.encode("utf-8")))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
