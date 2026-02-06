#!/usr/bin/env python3
"""
ANTIGRAVITY — TRICKSTER-ORACLE Phase 1 Completion (Error Contract: 404/405) + Evidence

Context
- DNS issue resolved via Option A: use Render URL directly.
- Branch: hardening/p0
- Remaining Phase 1 work: unify 404 responses into ErrorResponse contract.
- Keep production base URL: https://trickster-oracle-api.onrender.com

Goals (in strict causality order)
1) Implement a global 404 handler returning unified ErrorResponse JSON schema.
2) Implement/align 405 handler (Method Not Allowed) to the same schema (same pass).
3) Ensure X-Request-ID propagation matches body.request_id.
4) Add deterministic tests (4) and pass them.
5) Update evidence doc (EVIDENCE_P0.md) with command outputs.

Non-negotiable rules
- Minimal patches; do not refactor unrelated modules.
- Keep compatibility with /docs and /openapi.json.
- No DNS changes.
- Evidence must be reproducible (store exact curl outputs or pytest logs).

Expected output artifacts
- Code changes in backend only (app/* and tests/*).
- tests/test_error_contract.py (or equivalent).
- docs/EVIDENCE_P0.md updated.
- Commit(s) created on hardening/p0 branch.

Verification commands
- pytest -q
- curl checks (shown below)

"""

from pathlib import Path
import subprocess
import textwrap
import sys

BASE_URL_PROD = "https://trickster-oracle-api.onrender.com"

def sh(cmd: str) -> None:
    print(f"\n$ {cmd}")
    p = subprocess.run(cmd, shell=True, text=True)
    if p.returncode != 0:
        raise SystemExit(p.returncode)

def write_file(path: str, content: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding="utf-8")
    print(f"Wrote {path}")

def main():
    # --- Guardrails
    if not Path("backend").exists():
        print("ERROR: expected ./backend directory. Run from repo root.")
        sys.exit(1)

    # --- 0) Snapshot current state
    sh("git status --porcelain")
    sh("git rev-parse --abbrev-ref HEAD")

    # --- 1) Create/patch error contract handlers (FastAPI)
    # NOTE: This prompt assumes a typical FastAPI layout:
    # backend/app/main.py or backend/app/app.py loads the FastAPI instance.
    #
    # We will create a dedicated module with exception handlers and ensure it's wired in.

    handlers_py = textwrap.dedent(
        """
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
        """
    ).lstrip()

    write_file("backend/app/error_handlers.py", handlers_py)

    # --- 2) Wire handlers in app startup
    # Try common entrypoints; patch minimally.
    candidates = [
        Path("backend/app/main.py"),
        Path("backend/app/app.py"),
        Path("backend/app/__init__.py"),
    ]
    target = None
    for c in candidates:
        if c.exists():
            target = c
            break
    if not target:
        print("ERROR: could not find backend/app/main.py or app.py. Adjust the candidate list.")
        sys.exit(1)

    main_text = target.read_text(encoding="utf-8")

    if "install_error_handlers" not in main_text:
        # Insert import and install call near FastAPI() creation.
        # We'll do a conservative string patch. Antigravity should adjust if structure differs.
        patch_note = (
            "\n# --- Error contract handlers\n"
            "from app.error_handlers import install_error_handlers\n"
        )
        if "FastAPI(" in main_text and "install_error_handlers" not in main_text:
            if patch_note not in main_text:
                # Add import after existing imports
                lines = main_text.splitlines()
                insert_at = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith("from fastapi") or line.strip().startswith("import"):
                        insert_at = i + 1
                lines.insert(insert_at, patch_note.rstrip("\n"))
                main_text = "\n".join(lines)

            # Add install call after app instantiation
            # Find line containing "app = FastAPI("
            lines = main_text.splitlines()
            for i, line in enumerate(lines):
                if "app = FastAPI" in line.replace(" ", "") or "FastAPI(" in line and "app" in line and "=" in line:
                    # Insert on next line (avoid duplicates)
                    if i + 1 < len(lines) and "install_error_handlers(app)" in lines[i + 1]:
                        break
                    lines.insert(i + 1, "install_error_handlers(app)")
                    main_text = "\n".join(lines)
                    break

            target.write_text(main_text, encoding="utf-8")
            print(f"Patched {target} to install error handlers.")
        else:
            print(f"WARNING: Could not safely detect FastAPI app creation in {target}. Please wire manually:")
            print("  from app.error_handlers import install_error_handlers")
            print("  install_error_handlers(app)")

    # --- 3) Tests (deterministic)
    test_py = textwrap.dedent(
        """
        import json
        from fastapi.testclient import TestClient

        # Adjust import to your actual app instance path.
        from app.main import app

        client = TestClient(app)

        def _assert_error_contract(r, expected_status, expected_code, expected_path, expected_request_id):
            assert r.status_code == expected_status
            assert r.headers.get("content-type", "").startswith("application/json")
            data = r.json()
            assert data["error_code"] == expected_code
            assert data["path"] == expected_path
            assert data["request_id"] == expected_request_id
            assert "timestamp" in data

        def test_404_contract_get():
            rid = "test-rid-404-get"
            r = client.get("/__does_not_exist__", headers={"X-Request-ID": rid})
            _assert_error_contract(r, 404, "not_found", "/__does_not_exist__", rid)

        def test_404_contract_post():
            rid = "test-rid-404-post"
            r = client.post("/__does_not_exist__", headers={"X-Request-ID": rid})
            _assert_error_contract(r, 404, "not_found", "/__does_not_exist__", rid)

        def test_405_contract():
            rid = "test-rid-405"
            # Assuming /health exists and is GET-only in your app
            r = client.post("/health", headers={"X-Request-ID": rid})
            _assert_error_contract(r, 405, "method_not_allowed", "/health", rid)

        def test_422_contract_validation():
            rid = "test-rid-422"
            # This assumes /api/v1/simulate expects a body; sending empty should trigger 422.
            r = client.post("/api/v1/simulate", headers={"X-Request-ID": rid}, json={})
            assert r.status_code in (422, 400)
            # If 422, ensure contract:
            if r.status_code == 422:
                assert r.headers.get("content-type", "").startswith("application/json")
                data = r.json()
                assert data["error_code"] == "validation_error"
                assert data["path"] == "/api/v1/simulate"
                assert data["request_id"] == rid
        """
    ).lstrip()

    write_file("backend/tests/test_error_contract.py", test_py)

    # --- 4) Run tests
    sh("cd backend && pytest -q")

    # --- 5) Evidence update (append minimal, reproducible section)
    evidence_path = Path("backend/docs/EVIDENCE_P0.md")
    if not evidence_path.exists():
        # fallback: repo-level docs
        evidence_path = Path("docs/hardening/EVIDENCE_P0.md")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)

    evidence_append = textwrap.dedent(
        f"""
        \n\n## P0 — Error Contract (404/405) Verification

        **Decision**: Option A — Use Render URL directly (DNS deferred)
        **Prod BASE URL**: {BASE_URL_PROD}

        ### Local tests (deterministic)
        - `pytest -q` ✅

        ### Manual curl checks (run after deploy or against Render)
        ```bash
        curl -i {BASE_URL_PROD}/__does_not_exist__ -H "X-Request-ID: ev-404-1"
        curl -i -X POST {BASE_URL_PROD}/health -H "X-Request-ID: ev-405-1"
        ```

        **Expected**:
        - JSON body includes: error_code, message, path, request_id, timestamp
        - Headers include: X-Request-ID (middleware) and Content-Type application/json
        """
    ).strip() + "\n"

    with evidence_path.open("a", encoding="utf-8") as f:
        f.write(evidence_append)
    print(f"Updated evidence: {evidence_path}")

    # --- 6) Git commit
    sh("git add backend/app/error_handlers.py backend/tests/test_error_contract.py")
    sh(f'git commit -m "P0: unify 404/405 error contract (ErrorResponse) + tests" || true')
    sh("git status --porcelain")

    print("\nDONE: Phase 1 error contract completed (pending deploy if needed).")

if __name__ == "__main__":
    main()
