from __future__ import annotations

import time
import json
from dataclasses import dataclass
from typing import Dict, Tuple
from starlette.types import ASGIApp, Receive, Scope, Send


@dataclass
class Bucket:
    tokens: float
    last_refill: float


class RateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        rps: float = 5.0,
        burst: float = 20.0,
        paths: Tuple[str, ...] = ("/reports", "/reports/", "/health", "/attestation"),
    ):
        self.app = app
        self.rps = float(rps)
        self.burst = float(burst)
        self.paths = paths
        self.buckets: Dict[str, Bucket] = {}

    def _refill(self, b: Bucket, now: float) -> None:
        elapsed = max(0.0, now - b.last_refill)
        b.tokens = min(self.burst, b.tokens + elapsed * self.rps)
        b.last_refill = now

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not any(path == p or path.startswith(p.rstrip("/") + "/") for p in self.paths):
            await self.app(scope, receive, send)
            return

        # Simple IP key logic from scope
        client = scope.get("client")
        key = client[0] if client else "unknown"
        
        now = time.time()
        bucket = self.buckets.get(key)
        if bucket is None:
            bucket = Bucket(tokens=self.burst, last_refill=now)
            self.buckets[key] = bucket

        self._refill(bucket, now)
        if bucket.tokens < 1.0:
            # 429 Error
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [(b"content-type", b"application/json")]
            })
            await send({
                "type": "http.response.body",
                "body": json.dumps({"detail": "rate_limited"}).encode("utf-8")
            })
            return

        bucket.tokens -= 1.0
        await self.app(scope, receive, send)
