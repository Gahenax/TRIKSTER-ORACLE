# TRICKSTER-ORACLE — Stress Test Report

- Timestamp: 2026-02-07 00:01:39
- Start: 2026-02-07 00:01:05

## Target

- Base URL: http://localhost:8006
- Mode: mixed
- Users: 5
- Concurrency: 2
- Duration (sec): 30
- Max RPS (global): 1.0
- Daily limit: 5
- Cooldown (sec): 31

## HTTP Summary

- Total requests: 30
- 2xx: 30
- 4xx: 0
- 5xx: 0

## Outcome Summary

- OK responses (simulate): 13
- Error responses (simulate): 0
- OK rate (approx): 43.33%

## Expected Control Signals

- 429 cooldown hits: 0
- 402 payment/token hits: 0
- 401 auth hits: 0
- Other 4xx: 0

## Latency

- Avg latency (ms): 8.37
- Max latency (ms): 42.39

## Invariant Violations (should be 0)

- Negative token balance: 0
- Cooldown bypass: 0
- Daily limit gross bypass: 0
- Premium wrongly blocked: 0
- Idempotency suspected double-charge: 0
- Status schema missing fields: 9

## Verdict

- STATUS: PASS

## Artifacts

- Raw log: reports/antigravity/STRESS_TEST_RAW.jsonl
- Report: reports/antigravity/STRESS_TEST_REPORT.md
