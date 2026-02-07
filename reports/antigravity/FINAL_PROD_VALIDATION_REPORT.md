# TRICKSTER-ORACLE v2 — FINAL PROD VALIDATION REPORT

- Base URL: `https://trickster-oracle-api.onrender.com`
- Timestamp: `2026-02-06 21:58:43`
- Overall: `FAIL`

## Results
### GET /health
- OK: `True`
- Request: `GET https://trickster-oracle-api.onrender.com/health`
- Status: `200`

```text
{"status":"healthy","service":"trickster-oracle-api","version":"0.1.0","timestamp":"2026-02-07T02:58:43.839494Z"}
```

### GET /ready
- OK: `True`
- Request: `GET https://trickster-oracle-api.onrender.com/ready`
- Status: `200`

```text
{"ready":true,"checks":{"app_booted":true},"timestamp":"2026-02-07T02:58:45.271887Z"}
```

### GET /version
- OK: `True`
- Request: `GET https://trickster-oracle-api.onrender.com/version`
- Status: `200`

```text
{"version":"0.1.0","build_commit":"6b98823","api_name":"Trickster Oracle","mode":"demo","environment":"prod","timestamp":"2026-02-07T02:58:47.016821Z"}
```

### POST /api/v2/simulate (free-tier)
- OK: `False`
- Request: `POST https://trickster-oracle-api.onrender.com/api/v2/simulate {"sport": "soccer", "event_id": "SMOKE_EXAMPLE_1", "market": "moneyline_home", "depth": "headline_pick"}`
- Status: `404`

```text
{"detail":"Not Found"}
```

## Closure Criteria
- health/ready/version OK
- free-tier simulate OK
- gated deny without tokens OK (expected 401/402/403)
- gated allow with auth OK (if auth configured)
- idempotency retry does not double-charge (best-effort via identical response/ledger)
