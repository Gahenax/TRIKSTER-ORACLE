# TRICKSTER-ORACLE v2 — FINAL PROD VALIDATION REPORT

- Base URL: `http://127.0.0.1:8000`
- Timestamp: `2026-02-07 03:15:48`
- Overall: `PASS`

## Results
### GET /health
- OK: `True`
- Request: `GET http://127.0.0.1:8000/health`
- Status: `200`

```text
{"status":"healthy","service":"trickster-oracle-api","version":"0.1.0","timestamp":"2026-02-07T08:15:48.152971Z"}
```

### GET /ready
- OK: `True`
- Request: `GET http://127.0.0.1:8000/ready`
- Status: `200`

```text
{"ready":true,"checks":{"app_booted":true},"timestamp":"2026-02-07T08:15:48.159838Z"}
```

### GET /version
- OK: `True`
- Request: `GET http://127.0.0.1:8000/version`
- Status: `200`

```text
{"version":"0.1.0","build_commit":"unknown","api_name":"Trickster Oracle","mode":"demo","environment":"development","timestamp":"2026-02-07T08:15:48.167509Z"}
```

### POST /api/v2/simulate (free-tier)
- OK: `True`
- Request: `POST http://127.0.0.1:8000/api/v2/simulate {"sport": "soccer", "event_id": "SMOKE_EXAMPLE_1", "market": "moneyline_home", "home_rating": 2100.0, "away_rating": 2050.0, "depth": "headline_pick"}`
- Status: `200`

```text
{"sport":"soccer","event_id":"SMOKE_EXAMPLE_1","market":"moneyline_home","model_version":"v2.0","pick":{"predicted_outcome":"home","confidence":"low","median_probability":0.559},"cost_tokens":0,"notes":"Headline pick is always free for educational access"}
```

### POST /api/v2/simulate (expect deny without tokens)
- OK: `True`
- Request: `POST http://127.0.0.1:8000/api/v2/simulate {"sport": "soccer", "event_id": "SMOKE_EXAMPLE_1", "market": "moneyline_home", "home_rating": 2100.0, "away_rating": 2050.0, "depth": "full_distribution", "config": {"n_simulations": 1000}}`
- Status: `401`

```text
{"error_code":"http_error","message":"X-User-ID header required for gated endpoints","path":"/api/v2/simulate","request_id":null,"timestamp":"2026-02-07T08:15:48.241618+00:00"}
```

### AUTH not provided
- OK: `True`
- Request: `Set TRICKSTER_AUTH to validate gated allow + idempotency + ledger.`
- Status: `0`

```text
SKIPPED gated allow/idempotency/ledger checks (no TRICKSTER_AUTH).
```

## Closure Criteria
- health/ready/version OK
- free-tier simulate OK
- gated deny without tokens OK (expected 401/402/403)
- gated allow with auth OK (if auth configured)
- idempotency retry does not double-charge (best-effort via identical response/ledger)
