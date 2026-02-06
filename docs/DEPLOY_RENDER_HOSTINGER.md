# Deploy TRICKSTER-ORACLE (Backend) — Render + Hostinger Subdomain

Target FQDN
- `trickster-api.gahenaxaisolutions.com`

## Why this first (before Tokens)
- Validates real-world HTTPS, CORS, latency, headers (`X-Request-ID`), and system routes.
- Prevents building Tokens on top of untested production surfaces.

## Prerequisites
- Repo is up to date locally.
- Backend has `/health`, `/ready`, `/version`.
- `.env.example` exists (generated if missing).
- CORS allowlist planned:
  - `https://tricksteranalytics.gahenaxaisolutions.com`

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
- `CORS_ORIGINS=https://tricksteranalytics.gahenaxaisolutions.com`

## Step 4 — Add custom domain in Render
Add domain:
- `trickster-api.gahenaxaisolutions.com`

Render will provide DNS instructions (usually CNAME).

## Step 5 — Configure Hostinger DNS
In Hostinger hPanel → DNS Zone:
- Create **CNAME**:
  - Host/Name: `trickster-api`
  - Target/Points to: `<service>.onrender.com` (the exact value Render shows)

Notes:
- Use the exact target Render provides.
- DNS propagation can take time.

## Step 6 — Post-deploy verification (must pass)
- `GET https://trickster-api.gahenaxaisolutions.com/health` returns 200 and includes `X-Request-ID`
- `GET https://trickster-api.gahenaxaisolutions.com/version` includes BUILD_COMMIT (or "unknown")
- Frontend calls succeed with CORS allowlist (no `*`)
- No stack traces returned in prod responses

## Rollback Plan
- Render: rollback to previous deploy from dashboard (Deploys tab).
- If domain issues: revert DNS CNAME and re-verify.
