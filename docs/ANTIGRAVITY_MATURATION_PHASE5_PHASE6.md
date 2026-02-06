TRICKSTER-ORACLE — MATURATION WORK ORDER (Phase 5/6 prerequisites)

REPO_ROOT: C:\Users\USUARIO\.gemini\antigravity\playground\TRIKSTER-ORACLE
BACKEND_ROOT (guess): C:\Users\USUARIO\.gemini\antigravity\playground\TRIKSTER-ORACLE\backend
APP_ROOT (guess): C:\Users\USUARIO\.gemini\antigravity\playground\TRIKSTER-ORACLE\backend\app
FASTAPI_ENTRY (guess): C:\Users\USUARIO\.gemini\antigravity\playground\TRIKSTER-ORACLE\backend\app\main.py

STRICT ORDER OF OPERATIONS:


[A1] Add Request-ID middleware + JSON structured logging per request (observability baseline)

Actions:
 - Create app/middleware/request_id.py: generate X-Request-ID if missing; attach to response.
 - Create app/logging.py: configure JSON logger with request_id, path, method, status_code, duration_ms, cache_hit.
 - Wire middleware + logger in FastAPI entry.
 - Ensure no stack traces leak in prod: add ENV guard for exception handlers if needed.

Evidence required:
 - curl -i shows X-Request-ID header returned
 - logs show request_id, duration_ms, status_code in JSON
 - pytest still passes

Risk notes:
 - Be careful not to log secrets or full payloads.


[A2] Add readiness endpoints: /health, /ready, /version

Actions:
 - Create app/routes/system.py with routers for health/ready/version
 - Expose git commit via env BUILD_COMMIT (fallback 'unknown')
 - ready checks: minimal (can return 200 if app booted) or include optional db ping if available

Evidence required:
 - curl /health returns 200 + JSON
 - curl /version includes build_commit

Risk notes:
 - Do not expose internal config in /ready.


[B1] Define deterministic cache policy + response contract for /simulate (cache metadata)

Actions:
 - Create app/cache/policy.py with stable request fingerprint (hash of normalized payload).
 - Make /simulate respond with: result + meta.cache_hit + meta.fingerprint + meta.model_version
 - If cache exists, return cached result (no recompute).

Evidence required:
 - Two identical requests: second returns meta.cache_hit=true
 - Unit tests added for fingerprint stability

Risk notes:
 - Normalization must be consistent (sorted keys, stable float formatting).


[B2] Idempotency: X-Idempotency-Key prevents duplicate charging/computation

Actions:
 - Create app/idempotency/store.py (in-memory first; if DB exists, persist).
 - On /simulate: if idempotency key seen for (user_id, endpoint), return stored response.
 - Include meta.idempotency_replay flag.

Evidence required:
 - Repeated POST with same X-Idempotency-Key returns identical response and idempotency_replay=true

Risk notes:
 - In-memory store resets on restart; acceptable for now, document limitation.


[C1] Token ledger (no monetization yet): define models + atomic spend hooks

Actions:
 - Create app/tokens/models.py: LedgerEntry, BalanceView
 - Create app/tokens/ledger.py: grant_daily, spend, refund, get_balance
 - Implement minimal persistence: SQLite via SQLModel/SQLAlchemy if already present; otherwise JSON file store in /var/data or backend/data.
 - Add endpoint /api/balance and enforce spend in /simulate with 402 when insufficient.

Evidence required:
 - curl /api/balance returns balance
 - simulate consumes tokens and balance decreases
 - insufficient balance returns 402 with structured error + request_id

Risk notes:
 - If no DB exists, JSON store must be lock-safe (file lock) to avoid corruption.


[D1] Rate limiting: policy + middleware hook (actor-aware)

Actions:
 - Define actor identity: use anon signed cookie or header X-Actor-ID; fallback to IP.
 - Create app/ratelimit/policy.py: limits per actor per endpoint
 - Create app/ratelimit/middleware.py: enforce and return 429 with Retry-After
 - Apply to /simulate and any expensive endpoints

Evidence required:
 - Burst requests exceed limit and return 429 with Retry-After
 - Within limit requests succeed

Risk notes:
 - Prefer token bucket; keep initial implementation simple and documented.


[E1] Deploy readiness: env config, CORS allowlist, production logging guardrails

Actions:
 - Create app/config.py reading env: ENV, CORS_ORIGINS, BUILD_COMMIT, DATA_DIR
 - Wire CORS middleware with allowlist (no '*')
 - Add Procfile / render.yaml / Dockerfile depending on current strategy
 - Document deployment steps in docs/DEPLOY_RENDER.md

Evidence required:
 - App boots with ENV=prod and CORS configured
 - Docs include copy/paste Render steps

Risk notes:
 - CORS misconfig breaks frontend; include staging config.


VERIFICATION COMMANDS (must record evidence):
1) Unit tests:
   cd "C:\Users\USUARIO\.gemini\antigravity\playground\TRIKSTER-ORACLE\backend" && pytest -q

2) Run dev server:
   cd "C:\Users\USUARIO\.gemini\antigravity\playground\TRIKSTER-ORACLE\backend" && uvicorn app.main:app --reload
   (If entry differs, use the discovered module path)

3) Smoke endpoints:
   curl -i http://127.0.0.1:8000/health
   curl -i http://127.0.0.1:8000/ready
   curl -i http://127.0.0.1:8000/version

4) Simulate request (example):
   curl -s -X POST http://127.0.0.1:8000/api/simulate \
     -H "Content-Type: application/json" \
     -H "X-Actor-ID: anon_test_1" \
     -H "X-Idempotency-Key: idem-001" \
     -d '{"sport":"soccer","event_id":"LIV_vs_CITY_2026","iterations":50000,"confidence_level":0.99}' | jq

   Repeat same request and confirm:
     meta.cache_hit OR meta.idempotency_replay becomes true

5) Token enforcement:
   curl -s http://127.0.0.1:8000/api/balance -H "X-Actor-ID: anon_test_1" | jq
   (simulate should decrement)

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