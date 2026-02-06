#!/usr/bin/env python3
"""
ANTIGRAVITY PROMPT (Python) — Deploy TRICKSTER-ORACLE to Cloud (Render) + Subdomain in Hostinger

GOAL
- Prepare a production-grade deployment plan BEFORE implementing Tokens.
- Target: expose backend as https://<SUBDOMAIN>.<DOMAIN> using Hostinger DNS (CNAME) pointing to Render.
- Generate all required repo artifacts: render.yaml (or render blueprint), start command, env template,
  deploy docs, and verification checklist.

IMPORTANT
- This script DOES NOT deploy automatically (no cloud credentials). It generates deterministic files + commands
  so Antigravity can execute the deployment with minimal ambiguity.

USAGE
  python tools/antigravity_deploy_render_hostinger.py \
    --repo "c:/Users/USUARIO/.gemini/antigravity/playground/TRIKSTER-ORACLE" \
    --domain "gahenaxaisolutions.com" \
    --subdomain "trickster-api" \
    --service-name "trickster-oracle-api" \
    --cors-origin "https://tricksteranalytics.gahenaxaisolutions.com"

OUTPUTS (created/updated)
- docs/DEPLOY_RENDER_HOSTINGER.md
- docs/DEPLOY_CHECKLIST.md
- render.yaml (optional blueprint)
- backend/.env.example (if missing)
- docs/POST_DEPLOY_VERIFICATION.md
- tools/verify_deploy.sh (curl-based)

NON-NEGOTIABLE RULES
1) No refactors. Only create/modify deployment-related files.
2) Do not hardcode secrets. Use env vars only.
3) CORS must be allowlist-based (no '*') for prod.
4) Health endpoints must exist: /health, /ready, /version
"""

from __future__ import annotations

import argparse
import os
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def exists_any(root: Path, rels: list[str]) -> Optional[Path]:
    for r in rels:
        p = root / r
        if p.exists():
            return p
    return None


def find_fastapi_entry(backend: Path) -> Optional[str]:
    """
    Best-effort detection of ASGI app import path for uvicorn:
    - Looks for 'FastAPI(' and 'app = FastAPI(' patterns in common files.
    Returns a uvicorn import string like 'app.main:app' or None.
    """
    candidates = []
    for pat in ["app/main.py", "main.py", "app.py", "app/__init__.py"]:
        p = backend / pat
        if p.exists():
            candidates.append(p)
    # also scan a few .py files under app/ for FastAPI(
    app_dir = backend / "app"
    if app_dir.exists():
        for p in app_dir.rglob("*.py"):
            candidates.append(p)

    seen = set()
    for p in candidates:
        if p in seen:
            continue
        seen.add(p)
        try:
            s = read_text(p)
        except Exception:
            continue
        if "FastAPI(" not in s:
            continue
        # common: app = FastAPI(...)
        if re.search(r"\bapp\s*=\s*FastAPI\(", s):
            rel = p.relative_to(backend).as_posix()
            mod = rel[:-3].replace("/", ".")  # strip .py
            return f"{mod}:app"

    return None


def ensure_env_example(backend: Path, cors_origin: str) -> None:
    env_example = backend / ".env.example"
    if env_example.exists():
        return
    content = textwrap.dedent(f"""\
    # Example env for TRICKSTER-ORACLE (do not commit real secrets)
    ENV=prod
    BUILD_COMMIT=unknown
    DATA_DIR=/var/data
    # Allowlist: comma-separated
    CORS_ORIGINS={cors_origin}
    # Optional (future):
    # TOKEN_STORE_PATH=/var/data/token_ledger.json
    # RATE_LIMIT_ENABLED=1
    """)
    write_text(env_example, content)


def render_yaml_template(service_name: str, backend_dir: str, start_cmd: str) -> str:
    # Render Blueprint format (render.yaml)
    # Minimal: one web service
    return textwrap.dedent(f"""\
    services:
      - type: web
        name: {service_name}
        env: python
        plan: free
        rootDir: {backend_dir}
        buildCommand: pip install -e .
        startCommand: {start_cmd}
        healthCheckPath: /health
        envVars:
          - key: ENV
            value: prod
          - key: BUILD_COMMIT
            value: unknown
          - key: DATA_DIR
            value: /var/data
          - key: CORS_ORIGINS
            value: ""
    """)


def deploy_docs(domain: str, subdomain: str, service_name: str, cors_origin: str) -> str:
    fqdn = f"{subdomain}.{domain}"
    return textwrap.dedent(f"""\
    # Deploy TRICKSTER-ORACLE (Backend) — Render + Hostinger Subdomain

    Target FQDN
    - `{fqdn}`

    ## Why this first (before Tokens)
    - Validates real-world HTTPS, CORS, latency, headers (`X-Request-ID`), and system routes.
    - Prevents building Tokens on top of untested production surfaces.

    ## Prerequisites
    - Repo is up to date locally.
    - Backend has `/health`, `/ready`, `/version`.
    - `.env.example` exists (generated if missing).
    - CORS allowlist planned:
      - `{cors_origin}`

    ## Step 1 — Prepare Render service
    Option A (recommended): Render Blueprint
    1) Commit `render.yaml` to repo.
    2) In Render: New → Blueprint → connect repo → deploy.

    Option B: Manual Web Service
    1) New → Web Service
    2) Environment: Python
    3) Root directory: `backend/`
    4) Build command: `pip install -e .`
    5) Start command: (see below)

    ## Step 2 — Start command
    Use:
    - `uvicorn <IMPORT_PATH> --host 0.0.0.0 --port $PORT`

    ## Step 3 — Environment variables (Render dashboard)
    Set:
    - `ENV=prod`
    - `BUILD_COMMIT=<git sha>` (optional)
    - `DATA_DIR=/var/data`
    - `CORS_ORIGINS={cors_origin}`

    ## Step 4 — Add custom domain in Render
    Add domain:
    - `{fqdn}`

    Render will provide DNS instructions (usually CNAME).

    ## Step 5 — Configure Hostinger DNS
    In Hostinger hPanel → DNS Zone:
    - Create **CNAME**:
      - Host/Name: `{subdomain}`
      - Target/Points to: `<service>.onrender.com` (the exact value Render shows)

    Notes:
    - Use the exact target Render provides.
    - DNS propagation can take time.

    ## Step 6 — Post-deploy verification (must pass)
    - `GET https://{fqdn}/health` returns 200 and includes `X-Request-ID`
    - `GET https://{fqdn}/version` includes BUILD_COMMIT (or "unknown")
    - Frontend calls succeed with CORS allowlist (no `*`)
    - No stack traces returned in prod responses

    ## Rollback Plan
    - Render: rollback to previous deploy from dashboard (Deploys tab).
    - If domain issues: revert DNS CNAME and re-verify.

    """).strip() + "\n"


def verification_script(domain: str, subdomain: str) -> str:
    fqdn = f"{subdomain}.{domain}"
    return textwrap.dedent(f"""\
    #!/usr/bin/env bash
    set -euo pipefail

    BASE="https://{fqdn}"

    echo "[*] Checking health..."
    curl -i "$BASE/health" | sed -n '1,20p'

    echo
    echo "[*] Checking ready..."
    curl -i "$BASE/ready" | sed -n '1,20p'

    echo
    echo "[*] Checking version..."
    curl -i "$BASE/version" | sed -n '1,50p'

    echo
    echo "[*] Checking Request-ID preservation..."
    curl -i "$BASE/health" -H "X-Request-ID: audit-fixed-001" | sed -n '1,25p'

    echo
    echo "[OK] If all returned 200 and X-Request-ID is present/preserved, deploy surface is healthy."
    """)


def checklist_md(domain: str, subdomain: str) -> str:
    fqdn = f"{subdomain}.{domain}"
    return textwrap.dedent(f"""\
    # DEPLOY CHECKLIST — TRICKSTER-ORACLE (Render + Hostinger)

    ## Before Deploy
    - [ ] Repo identity verified: `git remote -v`
    - [ ] Backend tests pass: `pytest -q`
    - [ ] System routes exist: `/health`, `/ready`, `/version`
    - [ ] `X-Request-ID` middleware returns header on responses
    - [ ] `.env.example` exists (no secrets committed)
    - [ ] CORS allowlist decided (no `*`)

    ## Render Setup
    - [ ] Web Service created (rootDir backend)
    - [ ] Build command correct (`pip install -e .`)
    - [ ] Start command correct (uvicorn host 0.0.0.0 port $PORT)
    - [ ] Env vars set: ENV, BUILD_COMMIT, DATA_DIR, CORS_ORIGINS
    - [ ] Health check path set: `/health`

    ## Domain + DNS
    - [ ] Custom domain added in Render: `{fqdn}`
    - [ ] Hostinger DNS CNAME created for `{subdomain}` pointing to Render-provided target
    - [ ] TLS active (Render indicates certificate issued)

    ## Post Deploy
    - [ ] `curl -i https://{fqdn}/health` returns 200 and `X-Request-ID`
    - [ ] `curl -i https://{fqdn}/version` returns build metadata
    - [ ] Frontend can call API (CORS ok)
    - [ ] Logs show request_id and duration_ms (no secrets)

    ## Greenlight for Tokens
    - [ ] Latency observed (p95 acceptable)
    - [ ] No CORS/HTTPS surprises
    - [ ] Ready to merge B1–E1 then implement Phase 5 tokens
    """)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--domain", required=True)
    ap.add_argument("--subdomain", required=True)
    ap.add_argument("--service-name", required=True)
    ap.add_argument("--cors-origin", required=True)
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"[FAIL] Repo path does not exist: {repo}")
        return 2

    backend = repo / "backend"
    if not backend.exists():
        print(f"[WARN] backend/ not found. Will still generate docs, but Antigravity must adjust paths.")
        backend = repo

    import_path = find_fastapi_entry(backend) or "app.main:app"
    start_cmd = f"uvicorn {import_path} --host 0.0.0.0 --port $PORT"

    # Generate artifacts
    ensure_env_example(backend, args.cors_origin)

    # render.yaml at repo root (preferred)
    render_yaml = render_yaml_template(
        service_name=args.service_name,
        backend_dir="backend" if (repo / "backend").exists() else ".",
        start_cmd=start_cmd,
    )
    write_text(repo / "render.yaml", render_yaml)

    # Docs
    write_text(repo / "docs" / "DEPLOY_RENDER_HOSTINGER.md",
               deploy_docs(args.domain, args.subdomain, args.service_name, args.cors_origin))
    write_text(repo / "docs" / "DEPLOY_CHECKLIST.md", checklist_md(args.domain, args.subdomain))
    write_text(repo / "docs" / "POST_DEPLOY_VERIFICATION.md",
               "Use tools/verify_deploy.sh after DNS + TLS are active.\n")

    # Verification script
    verify_sh = repo / "tools" / "verify_deploy.sh"
    write_text(verify_sh, verification_script(args.domain, args.subdomain))
    # Make it executable on *nix; on Windows harmless
    try:
        os.chmod(verify_sh, 0o755)
    except Exception:
        pass

    # Print next actions for Antigravity
    print("[OK] Generated deployment artifacts:")
    print(f" - {repo / 'render.yaml'}")
    print(f" - {repo / 'docs' / 'DEPLOY_RENDER_HOSTINGER.md'}")
    print(f" - {repo / 'docs' / 'DEPLOY_CHECKLIST.md'}")
    print(f" - {backend / '.env.example'}")
    print(f" - {verify_sh}")
    print()
    print("[NEXT] Antigravity must now:")
    print(" 1) Commit these files.")
    print(" 2) In Render: create Blueprint/Web Service and set env vars.")
    print(" 3) Add custom domain in Render.")
    print(" 4) In Hostinger DNS: add CNAME for subdomain pointing to Render target.")
    print(" 5) After TLS active: run tools/verify_deploy.sh")
    print()
    print(f"[INFO] Suggested Render start command:\n  {start_cmd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
