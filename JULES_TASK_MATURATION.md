# [JULES] Implement Maturation Prerequisites (B1-E1) for Phase 5/6

**Assigned to**: Jules (AI Assistant)  
**Priority**: High  
**Estimated Time**: 6-8 hours  
**Depends on**: A1 (Request ID) + A2 (System Routes) - Already completed ✅

---

## Context

TRICKSTER-ORACLE needs maturation work before Phase 5 (Tokens) and Phase 6 (Deployment) can proceed. Steps A1 and A2 are complete. You need to implement B1-E1 as specified in the work order.

**Work Order Reference**: `docs/ANTIGRAVITY_MATURATION_PHASE5_PHASE6.md`

---

## Your Tasks

### [B1] Cache Policy + Response Contract

**Goal**: Make cache behavior deterministic and expose metadata in responses.

**Files to create**:
1. `app/cache/policy.py`
   - Function: `generate_fingerprint(payload: dict) -> str`
   - Normalize payload (sorted keys, stable float formatting)
   - Return SHA256 hash of canonical JSON
   - Include unit tests for stability

**Files to modify**:
2. `app/api/routes.py` (existing `/simulate endpoint`)
   - Add to response schema: `meta.cache_hit`, `meta.fingerprint`, `meta.model_version`
   - Use fingerprint-based cache key
   - If cache hit, return with `cache_hit=true`

**Evidence required**:
- ✅ Two identical requests: second returns `meta.cache_hit=true`
- ✅ Unit test: same payload → same fingerprint (different order of keys)
- ✅ pytest passes

---

### [B2] Idempotency Store

**Goal**: Prevent duplicate computation/charging on retries.

**Files to create**:
1. `app/idempotency/__init__.py`
2. `app/idempotency/store.py`
   - Class: `IdempotencyStore` (in-memory dict for demo)
   - Methods: `get(key)`, `set(key, response, ttl)`
   - TTL tracking (auto-expire after 24h)

**Files to modify**:
3. `app/api/routes.py` (`/simulate` endpoint)
   - Read `X-Idempotency-Key` header (optional)
   - If key exists in store, return stored response with `meta.idempotency_replay=true`
   - Otherwise, process request and store result

**Evidence required**:
- ✅ Repeated POST with same `X-Idempotency-Key` returns identical response
- ✅ Response includes `meta.idempotency_replay=true` on replay
- ✅ pytest passes

**Risk Note**: In-memory store resets on restart (acceptable for demo, document limitation)

---

### [C1] Token Ledger (Backend Only, No UI)

**Goal**: Backend foundation for token system (no frontend work yet).

**Files to create**:
1. `app/tokens/__init__.py`
2. `app/tokens/models.py`
   ```python
   class LedgerEntry(BaseModel):
       actor_id: str
       amount: int  # positive=grant, negative=spend
       reason: str  # "daily_grant", "simulation", "refund"
       timestamp: datetime
       request_id: Optional[str]
   
   class BalanceView(BaseModel):
       actor_id: str
       balance: int
       last_updated: datetime
   ```

3. `app/tokens/ledger.py`
   - `grant_daily(actor_id: str, amount: int = 5) -> int`  # Returns new balance
   - `spend(actor_id: str, amount: int, reason: str, request_id: str) -> int`  # Atomic, raises InsufficientTokensError if balance < amount
   - `refund(actor_id: str, amount: int, reason: str) -> int`
   - `get_balance(actor_id: str) -> int`

4. `app/tokens/store.py`
   - Use **JSON file** persistence: `backend/data/tokens.json`
   - File locking (use `fcntl` or `filelock` library) to avoid corruption
   - Schema: `{"balances": {"actor_123": 5}, "ledger": [...]}`

5. `app/api/tokens.py`
   - Router: `/api/balance`
   - GET: Read `X-Actor-ID` header (required), return `BalanceView`

**Files to modify**:
6. `app/api/routes.py` (`/simulate` endpoint)
   - Before processing: check balance via `get_balance(actor_id)`
   - If insufficient: return **402 Payment Required** with structured error
   - After processing: call `spend(actor_id, amount=1, reason="simulation", request_id=...)`

7. `app/main.py`
   - Include router: `app.include_router(tokens.router)`

**Evidence required**:
- ✅ `curl /api/balance -H "X-Actor-ID: test_user"` returns balance
- ✅ Simulate request decrements balance
- ✅ Insufficient balance returns 402 with `request_id` in error
- ✅ pytest passes

**Risk Note**: JSON store must use file locking to prevent race conditions.

---

### [D1] Rate Limiting Middleware

**Goal**: Protect expensive endpoints from abuse.

**Files to create**:
1. `app/ratelimit/__init__.py`
2. `app/ratelimit/policy.py`
   - Token bucket algorithm (simple implementation)
   - Class: `RateLimitPolicy`
     - `__init__(requests_per_minute: int, burst: int)`
     - `check(actor_id: str) -> bool`  # Returns True if allowed
     - In-memory buckets: `dict[actor_id, (tokens, last_refill_time)]`

3. `app/ratelimit/middleware.py`
   - Middleware: `RateLimitMiddleware`
   - Apply to paths matching `/api/simulate`, `/api/*` (configurable)
   - On limit exceeded: return **429 Too Many Requests** with `Retry-After` header
   - Actor identity: `X-Actor-ID` header → fallback to `request.client.host` (IP)

**Files to modify**:
4. `app/main.py`
   - Add middleware: `app.add_middleware(RateLimitMiddleware, policy=...)`
   - Config: 10 requests/minute, burst=15 (for demo)

**Evidence required**:
- ✅ Burst requests exceed limit → 429 with `Retry-After` header
- ✅ Within limit requests succeed
- ✅ pytest passes

**Risk Note**: Keep implementation simple and well-documented (token bucket).

---

### [E1] Deploy Readiness

**Goal**: Environment config and deployment docs.

**Files to create**:
1. `app/config.py`
   ```python
   from pydantic import BaseSettings
   
   class Settings(BaseSettings):
       env: str = "development"  # development, staging, production
       cors_origins: str = "*"   # Comma-separated URLs
       build_commit: str = "unknown"
       data_dir: str = "./data"
       log_level: str = "INFO"
       max_simulations_demo: int = 1000
       daily_tokens_demo: int = 5
       rate_limit_per_minute: int = 10
       rate_limit_burst: int = 15
       
       class Config:
           env_file = ".env"
   
   settings = Settings()
   ```

2. `render.yaml`
   ```yaml
   services:
     - type: web
       name: trickster-oracle-api
       env: python
       buildCommand: "cd backend && pip install -e ."
       startCommand: "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
       envVars:
         - key: ENV
           value: production
         - key: BUILD_COMMIT
           sync: false  # Set manually or via CI
         - key: CORS_ORIGINS
           value: "https://tricksteranalytics.gahenaxaisolutions.com"
   ```

3. `docs/DEPLOY_RENDER.md`
   - Step-by-step Render.com deployment guide
   - Environment variable configuration
   - CORS setup for production
   - Health check endpoints configuration

**Files to modify**:
4. `app/main.py`
   - Import `settings` from `app.config`
   - Replace hardcoded values with `settings.cors_origins.split(",")`
   - Pass `settings` to middlewares as needed

5. `.env.example`
   - Add all new environment variables with sane defaults

**Evidence required**:
- ✅ App boots with `ENV=production` and CORS configured from env
- ✅ `docs/DEPLOY_RENDER.md` includes copy/paste steps
- ✅ No wildcard `*` CORS in production config

---

## Definition of Done

- [ ] All files created as specified
- [ ] All tests pass: `pytest -v`
- [ ] Smoke test endpoints work:
  - `curl -i http://127.0.0.1:8000/health` → 200 + `X-Request-ID`
  - `curl -i http://127.0.0.1:8000/ready` → 200
  - `curl -i http://127.0.0.1:8000/version` → includes `build_commit`
- [ ] Simulate request demonstrates:
  - Cache hit on second identical request
  - Idempotency replay on duplicate `X-Idempotency-Key`
  - Token consumption (balance decreases)
  - 402 error when balance insufficient
  - 429 error when rate limit exceeded
- [ ] Code committed with message: `feat: Implement maturation prerequisites (B1-E1) for Phase 5/6`
- [ ] Evidence file created: `docs/MATURATION_EVIDENCE.md` with curl outputs and test results

---

## Verification Commands

```bash
# 1. Run tests
cd backend && pytest -v

# 2. Start server
cd backend && uvicorn app.main:app --reload

# 3. Test health endpoints
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/ready
curl -i http://127.0.0.1:8000/version

# 4. Test simulate with all features
curl -s -X POST http://127.0.0.1:8000/api/simulate \
  -H "Content-Type: application/json" \
  -H "X-Actor-ID: anon_test_1" \
  -H "X-Idempotency-Key: idem-001" \
  -d '{"event_id":"sample_001","iterations":100,"seed":42}' | jq

# Run again (should show cache_hit or idempotency_replay)
curl -s -X POST http://127.0.0.1:8000/api/simulate \
  -H "Content-Type: application/json" \
  -H "X-Actor-ID: anon_test_1" \
  -H "X-Idempotency-Key: idem-001" \
  -d '{"event_id":"sample_001","iterations":100,"seed":42}' | jq

# 5. Test token balance
curl -s http://127.0.0.1:8000/api/balance -H "X-Actor-ID: anon_test_1" | jq

# 6. Test rate limiting (run in loop)
for i in {1..20}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://127.0.0.1:8000/api/simulate \
    -H "Content-Type: application/json" \
    -H "X-Actor-ID: rate_test_user" \
    -d '{"event_id":"sample_001","iterations":100}'
done
# Should see some 429 responses
```

---

## References

- Main work order: `docs/ANTIGRAVITY_MATURATION_PHASE5_PHASE6.md`
- Current progress: `docs/MATURATION_IMPLEMENTATION.md`
- GLOSSARY (compliance): `GLOSSARY.md`
- API docs: `API_DOCUMENTATION.md`

---

## Notes for Jules

- Use existing code style (see `app/core/engine.py` for reference)
- Follow GLOSSARY.md terminology (no gambling language)
- All errors must be structured JSON (no stacktrace leakage in prod)
- Add docstrings to all public functions
- Include type hints (Python 3.11+)
- Keep implementations simple and well-documented
- Test coverage should be >80% for new modules

Good luck! Report back once complete with evidence file.
