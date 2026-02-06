#!/usr/bin/env python3
"""
ANTIGRAVITY PROMPT (Python) — TRICKSTER-ORACLE
Objective: Mature foundations BEFORE implementing Phase 5 (Tokens/Rate Limit) and Phase 6 (Deploy)

This script is a "gatekeeper roadmap" + patch plan Antigravity can execute deterministically.
It assumes FastAPI backend (common in Trickster) and a repo layout like:
  TRIKSTER-ORACLE/
    backend/
      app/
        main.py  (or app/main.py)
      tests/
      pyproject.toml (or requirements.txt)

If your paths differ, Antigravity must locate equivalents by search patterns.

NON-NEGOTIABLES
1) No speculative refactors.
2) Implement in causality order:
   A) Observability & Contracts
   B) Idempotency & Cache Policy
   C) Token Ledger model (NO monetization UI yet)
   D) Rate limiting policy stubs + enforcement hooks
   E) Deploy readiness endpoints + env config
3) Provide evidence: tests passing + curl proofs + file diffs summary.
"""

from __future__ import annotations

import os
import re
import json
import time
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple


# -----------------------------
# Utilities (safe filesystem ops)
# -----------------------------

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def ensure_line_in_file(p: Path, needle: str, line_to_add: str) -> bool:
    """Returns True if modified."""
    s = read_text(p)
    if needle in s:
        return False
    s2 = s + ("" if s.endswith("\n") else "\n") + line_to_add + "\n"
    write_text(p, s2)
    return True

def find_files(root: Path, patterns: Iterable[str]) -> list[Path]:
    out = []
    for pat in patterns:
        out.extend(root.rglob(pat))
    # Deduplicate
    uniq = []
    seen = set()
    for p in out:
        if p.resolve() not in seen:
            uniq.append(p)
            seen.add(p.resolve())
    return uniq

def grep(root: Path, regex: str) -> list[Tuple[Path, int, str]]:
    rx = re.compile(regex)
    hits = []
    for p in root.rglob("*.py"):
        try:
            lines = read_text(p).splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            if rx.search(line):
                hits.append((p, i, line))
    return hits

def best_guess_backend_root(repo_root: Path) -> Path:
    # Prefer /backend if exists
    b = repo_root / "backend"
    if b.exists():
        return b
    # Otherwise try heuristics
    for cand in ["api", "server", "services"]:
        c = repo_root / cand
        if c.exists():
            return c
    return repo_root

def best_guess_app_root(backend_root: Path) -> Path:
    for cand in ["app", "src", "trickster_oracle", "server", "api"]:
        c = backend_root / cand
        if c.exists():
            return c
    return backend_root

def find_fastapi_entry(app_root: Path) -> Optional[Path]:
    # Look for common entry points with FastAPI() usage
    candidates = find_files(app_root, ["main.py", "app.py", "__init__.py"])
    for p in candidates:
        try:
            s = read_text(p)
        except Exception:
            continue
        if "FastAPI(" in s:
            return p
    # fallback: any py file containing FastAPI(
    for p in app_root.rglob("*.py"):
        try:
            s = read_text(p)
        except Exception:
            continue
        if "FastAPI(" in s:
            return p
    return None


# -----------------------------
# Patch Plan (what Antigravity must implement)
# -----------------------------

@dataclass
class PatchStep:
    id: str
    goal: str
    actions: list[str]
    evidence: list[str]
    risk_notes: list[str]


def build_patch_plan() -> list[PatchStep]:
    return [
        PatchStep(
            id="A1",
            goal="Add Request-ID middleware + JSON structured logging per request (observability baseline)",
            actions=[
                "Create app/middleware/request_id.py: generate X-Request-ID if missing; attach to response.",
                "Create app/logging.py: configure JSON logger with request_id, path, method, status_code, duration_ms, cache_hit.",
                "Wire middleware + logger in FastAPI entry.",
                "Ensure no stack traces leak in prod: add ENV guard for exception handlers if needed."
            ],
            evidence=[
                "curl -i shows X-Request-ID header returned",
                "logs show request_id, duration_ms, status_code in JSON",
                "pytest still passes"
            ],
            risk_notes=[
                "Be careful not to log secrets or full payloads."
            ]
        ),
        PatchStep(
            id="A2",
            goal="Add readiness endpoints: /health, /ready, /version",
            actions=[
                "Create app/routes/system.py with routers for health/ready/version",
                "Expose git commit via env BUILD_COMMIT (fallback 'unknown')",
                "ready checks: minimal (can return 200 if app booted) or include optional db ping if available"
            ],
            evidence=[
                "curl /health returns 200 + JSON",
                "curl /version includes build_commit"
            ],
            risk_notes=[
                "Do not expose internal config in /ready."
            ]
        ),
        PatchStep(
            id="B1",
            goal="Define deterministic cache policy + response contract for /simulate (cache metadata)",
            actions=[
                "Create app/cache/policy.py with stable request fingerprint (hash of normalized payload).",
                "Make /simulate respond with: result + meta.cache_hit + meta.fingerprint + meta.model_version",
                "If cache exists, return cached result (no recompute)."
            ],
            evidence=[
                "Two identical requests: second returns meta.cache_hit=true",
                "Unit tests added for fingerprint stability"
            ],
            risk_notes=[
                "Normalization must be consistent (sorted keys, stable float formatting)."
            ]
        ),
        PatchStep(
            id="B2",
            goal="Idempotency: X-Idempotency-Key prevents duplicate charging/computation",
            actions=[
                "Create app/idempotency/store.py (in-memory first; if DB exists, persist).",
                "On /simulate: if idempotency key seen for (user_id, endpoint), return stored response.",
                "Include meta.idempotency_replay flag."
            ],
            evidence=[
                "Repeated POST with same X-Idempotency-Key returns identical response and idempotency_replay=true"
            ],
            risk_notes=[
                "In-memory store resets on restart; acceptable for now, document limitation."
            ]
        ),
        PatchStep(
            id="C1",
            goal="Token ledger (no monetization yet): define models + atomic spend hooks",
            actions=[
                "Create app/tokens/models.py: LedgerEntry, BalanceView",
                "Create app/tokens/ledger.py: grant_daily, spend, refund, get_balance",
                "Implement minimal persistence: SQLite via SQLModel/SQLAlchemy if already present; otherwise JSON file store in /var/data or backend/data.",
                "Add endpoint /api/balance and enforce spend in /simulate with 402 when insufficient."
            ],
            evidence=[
                "curl /api/balance returns balance",
                "simulate consumes tokens and balance decreases",
                "insufficient balance returns 402 with structured error + request_id"
            ],
            risk_notes=[
                "If no DB exists, JSON store must be lock-safe (file lock) to avoid corruption."
            ]
        ),
        PatchStep(
            id="D1",
            goal="Rate limiting: policy + middleware hook (actor-aware)",
            actions=[
                "Define actor identity: use anon signed cookie or header X-Actor-ID; fallback to IP.",
                "Create app/ratelimit/policy.py: limits per actor per endpoint",
                "Create app/ratelimit/middleware.py: enforce and return 429 with Retry-After",
                "Apply to /simulate and any expensive endpoints"
            ],
            evidence=[
                "Burst requests exceed limit and return 429 with Retry-After",
                "Within limit requests succeed"
            ],
            risk_notes=[
                "Prefer token bucket; keep initial implementation simple and documented."
            ]
        ),
        PatchStep(
            id="E1",
            goal="Deploy readiness: env config, CORS allowlist, production logging guardrails",
            actions=[
                "Create app/config.py reading env: ENV, CORS_ORIGINS, BUILD_COMMIT, DATA_DIR",
                "Wire CORS middleware with allowlist (no '*')",
                "Add Procfile / render.yaml / Dockerfile depending on current strategy",
                "Document deployment steps in docs/DEPLOY_RENDER.md"
            ],
            evidence=[
                "App boots with ENV=prod and CORS configured",
                "Docs include copy/paste Render steps"
            ],
            risk_notes=[
                "CORS misconfig breaks frontend; include staging config."
            ]
        ),
    ]


# -----------------------------
# Antigravity Execution Stub
# (This file describes WHAT to do. Antigravity will implement actual patches.)
# -----------------------------

def generate_antigravity_work_order(repo_root: Path) -> str:
    backend_root = best_guess_backend_root(repo_root)
    app_root = best_guess_app_root(backend_root)
    entry = find_fastapi_entry(app_root)

    plan = build_patch_plan()

    loc_hint = f"""
REPO_ROOT: {repo_root}
BACKEND_ROOT (guess): {backend_root}
APP_ROOT (guess): {app_root}
FASTAPI_ENTRY (guess): {entry if entry else 'NOT FOUND - must search for FastAPI() usage'}
"""

    checks = textwrap.dedent(f"""
    VERIFICATION COMMANDS (must record evidence):
    1) Unit tests:
       cd "{backend_root}" && pytest -q

    2) Run dev server:
       cd "{backend_root}" && uvicorn app.main:app --reload
       (If entry differs, use the discovered module path)

    3) Smoke endpoints:
       curl -i http://127.0.0.1:8000/health
       curl -i http://127.0.0.1:8000/ready
       curl -i http://127.0.0.1:8000/version

    4) Simulate request (example):
       curl -s -X POST http://127.0.0.1:8000/api/simulate \\
         -H "Content-Type: application/json" \\
         -H "X-Actor-ID: anon_test_1" \\
         -H "X-Idempotency-Key: idem-001" \\
         -d '{{"sport":"soccer","event_id":"LIV_vs_CITY_2026","iterations":50000,"confidence_level":0.99}}' | jq

       Repeat same request and confirm:
         meta.cache_hit OR meta.idempotency_replay becomes true

    5) Token enforcement:
       curl -s http://127.0.0.1:8000/api/balance -H "X-Actor-ID: anon_test_1" | jq
       (simulate should decrement)
    """)

    output = ["TRICKSTER-ORACLE — MATURATION WORK ORDER (Phase 5/6 prerequisites)\n"]
    output.append(loc_hint.strip() + "\n")
    output.append("STRICT ORDER OF OPERATIONS:\n")
    for step in plan:
        output.append(f"\n[{step.id}] {step.goal}\n")
        output.append("Actions:\n" + "\n".join([f" - {a}" for a in step.actions]) + "\n")
        output.append("Evidence required:\n" + "\n".join([f" - {e}" for e in step.evidence]) + "\n")
        output.append("Risk notes:\n" + "\n".join([f" - {r}" for r in step.risk_notes]) + "\n")

    output.append("\n" + checks.strip() + "\n")

    output.append(textwrap.dedent("""
    OUTPUT FORMAT (Antigravity must deliver):
    1) DIFF SUMMARY
       - List files created/changed with brief purpose

    2) ROOT CAUSE / WHY NOW
       - 5-8 bullets explaining why these are prerequisites for Tokens/Deploy

    3) EVIDENCE
       - Test output summary (pass/fail)
       - curl outputs (headers must show X-Request-ID)
       - Demonstration of idempotency replay
       - Demonstration of 402 (no tokens) and 429 (rate limit) cases

    4) RISK NOTES + LIMITATIONS
       - e.g. in-memory idempotency store resets on restart

    5) NEXT ROADMAP
       - Now that prerequisites exist, define Phase 5 and Phase 6 implementation tasks
    """).strip())

    return "\n".join(output)


def main() -> int:
    # Antigravity should run this from the repo root or pass REPO_ROOT env var
    repo_root = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    work_order = generate_antigravity_work_order(repo_root)

    # Save the work order into docs so it is versioned
    docs_dir = repo_root / "docs"
    out_file = docs_dir / "ANTIGRAVITY_MATURATION_PHASE5_PHASE6.md"
    write_text(out_file, work_order)

    print(f"[OK] Work order generated: {out_file}")
    print("\n--- SNIPPET (top) ---\n")
    print("\n".join(work_order.splitlines()[:60]))
    print("\n--- END SNIPPET ---\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
