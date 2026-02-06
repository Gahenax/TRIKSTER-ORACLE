# 📋 GITHUB ISSUE - READY TO COPY/PASTE

## Instructions
1. Go to: https://github.com/Gahenax/TRIKSTER-ORACLE/issues/new
2. Copy the content below
3. Paste into the issue body
4. Add labels: `enhancement`, `jules` (if available)
5. Submit

---

## TITLE (copy this):
```
[JULES] Implement Maturation Prerequisites (B1-E1)
```

---

## BODY (copy everything below this line):

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
2. `app/api/routes.py` (existing `/simulate` endpoint)
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
   - `grant_daily(actor_id: str, amount: int = 5) -> int`
   - `spend(actor_id: str, amount: int, reason: str, request_id: str) -> int`
   - `refund(actor_id: str, amount: int, reason: str) -> int`
   - `get_balance(actor_id: str) -> int`

4. `app/tokens/store.py`
   - Use **JSON file** persistence: `backend/data/tokens.json`
   - File locking (`fcntl` or `filelock` library)
   - Schema: `{"balances": {"actor_123": 5}, "ledger": [...]}`

5. `app/api/tokens.py`
   - Router: `/api/balance`
   - GET: Read `X-Actor-ID` header, return `BalanceView`

**Files to modify**:
6. `app/api/routes.py` (`/simulate` endpoint)
   - Before processing: check balance via `get_balance(actor_id)`
   - If insufficient: return **402 Payment Required**
   - After processing: call `spend(...)`

7. `app/main.py`
   - Include router: `app.include_router(tokens.router)`

**Evidence required**:
- ✅ `curl /api/balance -H "X-Actor-ID: test_user"` returns balance
- ✅ Simulate request decrements balance
- ✅ Insufficient balance returns 402 with `request_id`
- ✅ pytest passes

---

### [D1] Rate Limiting Middleware

**Goal**: Protect expensive endpoints from abuse.

**Files to create**:
1. `app/ratelimit/__init__.py`
2. `app/ratelimit/policy.py`
   - Token bucket algorithm (simple implementation)
   - Class: `RateLimitPolicy`
     - `check(actor_id: str) -> bool`
     - In-memory buckets: `dict[actor_id, (tokens, last_refill_time)]`

3. `app/ratelimit/middleware.py`
   - Middleware: `RateLimitMiddleware`
   - Apply to paths matching `/api/simulate`, `/api/*`
   - On limit exceeded: return **429 Too Many Requests** with `Retry-After`
   - Actor identity: `X-Actor-ID` header → fallback to `request.client.host`

**Files to modify**:
4. `app/main.py`
   - Add middleware: `app.add_middleware(RateLimitMiddleware, ...)`
   - Config: 10 requests/minute, burst=15

**Evidence required**:
- ✅ Burst requests exceed limit → 429 with `Retry-After`
- ✅ Within limit requests succeed
- ✅ pytest passes

---

### [E1] Deploy Readiness

**Goal**: Environment config and deployment docs.

**Files to create**:
1. `app/config.py`
   ```python
   from pydantic import BaseSettings
   
   class Settings(BaseSettings):
       env: str = "development"
       cors_origins: str = "*"
       build_commit: str = "unknown"
       data_dir: str = "./data"
       max_simulations_demo: int = 1000
       daily_tokens_demo: int = 5
       rate_limit_per_minute: int = 10
       
       class Config:
           env_file = ".env"
   ```

2. `render.yaml` - Render.com deployment configuration

3. `docs/DEPLOY_RENDER.md` - Step-by-step deployment guide

**Files to modify**:
4. `app/main.py` - Import `settings`, replace hardcoded values
5. `.env.example` - Add all new environment variables

**Evidence required**:
- ✅ App boots with `ENV=production` and CORS configured
- ✅ `docs/DEPLOY_RENDER.md` includes copy/paste steps

---

## Definition of Done

- [ ] All files created as specified
- [ ] All tests pass: `pytest -v`
- [ ] Smoke test endpoints work
- [ ] Simulate request demonstrates:
  - Cache hit on second identical request
  - Idempotency replay on duplicate key
  - Token consumption (balance decreases)
  - 402 error when balance insufficient
  - 429 error when rate limit exceeded
- [ ] Code committed: `feat: Implement maturation prerequisites (B1-E1) for Phase 5/6`
- [ ] Evidence file created: `docs/MATURATION_EVIDENCE.md`

---

## Verification Commands

```bash
# 1. Run tests
cd backend && pytest -v

# 2. Start server
cd backend && uvicorn app.main:app --reload

# 3. Test endpoints
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/ready
curl -i http://127.0.0.1:8000/version

# 4. Test simulate with cache/idempotency
curl -s -X POST http://127.0.0.1:8000/api/simulate \
  -H "Content-Type: application/json" \
  -H "X-Actor-ID: anon_test_1" \
  -H "X-Idempotency-Key: idem-001" \
  -d '{"event_id":"sample_001","iterations":100,"seed":42}' | jq

# Run again (should show cache_hit or idempotency_replay)

# 5. Test token balance
curl -s http://127.0.0.1:8000/api/balance -H "X-Actor-ID: anon_test_1" | jq

# 6. Test rate limiting
for i in {1..20}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://127.0.0.1:8000/api/simulate \
    -H "X-Actor-ID: rate_test_user" \
    -d '{"event_id":"sample_001","iterations":100}'
done
```

---

## References

- Main work order: `docs/ANTIGRAVITY_MATURATION_PHASE5_PHASE6.md`
- Full task spec: `JULES_TASK_MATURATION.md`
- GLOSSARY (compliance): `GLOSSARY.md`
- API docs: `API_DOCUMENTATION.md`

---

## Notes

- Use existing code style (see `app/core/engine.py`)
- Follow GLOSSARY.md terminology (no gambling language)
- All errors must be structured JSON (no stacktrace leakage)
- Add docstrings to all public functions
- Include type hints (Python 3.11+)
- Test coverage should be >80% for new modules

Good luck! Report back with evidence file when complete.
