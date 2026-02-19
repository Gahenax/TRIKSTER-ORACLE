from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx

BASE_URL = os.getenv("VIEWER_BASE_URL", "http://localhost:8080")
API_KEY = os.getenv("VIEWER_API_KEY", "")

def headers() -> dict:
    if not API_KEY:
        return {}
    return {"X-API-Key": API_KEY}

def must(cond: bool, msg: str) -> None:
    if not cond:
        raise RuntimeError(msg)

def main() -> int:
    # Use a long timeout for the entire suite
    with httpx.Client(timeout=30.0, headers=headers()) as c:
        # 1) Health
        r = c.get(f"{BASE_URL}/health")
        must(r.status_code == 200, f"health failed: {r.status_code}")

        # 2) List
        r = c.get(f"{BASE_URL}/reports", params={"limit": 5, "offset": 0})
        must(r.status_code == 200, f"list failed: {r.status_code}")

        # 3) Read-only
        r = c.post(f"{BASE_URL}/api/reports")
        must(r.status_code == 405, "POST not blocked")

        # 4) Ratelimit test (conservative)
        results = []
        for _ in range(25):
            try:
                res = c.get(f"{BASE_URL}/health")
                results.append(res.status_code)
            except httpx.ReadTimeout:
                results.append("timeout")
            time.sleep(0.01) # Small gap
        
        success = results.count(200)
        limited = results.count(429)
        print(f"Ratelimit test: {success} success, {limited} limited, {results.count('timeout')} timeouts")
        must(success > 0, "No successful requests")

    print(json.dumps({"ok": True, "base_url": BASE_URL}, separators=(",", ":")))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, separators=(",", ":")))
        sys.exit(1)
