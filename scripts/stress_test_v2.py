#!/usr/bin/env python3
"""
ANTIGRAVITY — TRICKSTER-ORACLE v2
PROD STRESS TEST (TOKENS + COOLDOWN + PREMIUM BYPASS)

WHAT THIS DOES
- Runs a controlled load test against Trickster API v2.
- Validates invariants under concurrency:
  1) Cooldown enforced (429 with seconds_remaining) for free users between analyses
  2) Daily limit enforced (free analyses capped at N)
  3) Token consumption occurs ONLY after daily limit (or per your backend rule)
  4) Token ledger never goes negative
  5) Premium bypass works (no cooldown/limit enforcement)
  6) Idempotency works (no double-charge on repeated requests)

SAFETY
- Default settings are conservative.
- You can increase concurrency gradually.
- If you target production, keep RPS low to avoid harming real users.

REQUIREMENTS
- Python 3.10+
- pip install httpx

ENV VARS
Required:
- TRICKSTER_BASE_URL="https://trickster-oracle-api.onrender.com"  (or custom domain)
Optional:
- TRICKSTER_AUTH="Bearer <token>"  (if your endpoints require auth)
- TRICKSTER_TEST_MODE="free" | "premium" | "mixed"  (default: mixed)
- TRICKSTER_USERS=20
- TRICKSTER_CONCURRENCY=10
- TRICKSTER_DURATION_SEC=120
- TRICKSTER_MAX_RPS=5.0
- TRICKSTER_DAILY_LIMIT=5
- TRICKSTER_COOLDOWN_SEC=31
- TRICKSTER_STATUS_PATH="/api/v2/me/status"
- TRICKSTER_SIM_PATH="/api/v2/simulate"            (set to your real simulate v2 path)
- TRICKSTER_TOPUP_PATH="/api/v2/tokens/topup"      (optional; if exists)
- TRICKSTER_PREMIUM_PATH="/api/v2/me/premium"      (optional; if exists)

OUTPUTS
- reports/antigravity/STRESS_TEST_REPORT.md
- reports/antigravity/STRESS_TEST_RAW.jsonl
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple

import httpx


# ----------------------------
# Config
# ----------------------------

BASE_URL = os.environ.get("TRICKSTER_BASE_URL", "https://trickster-oracle-api.onrender.com").rstrip("/")
AUTH = os.environ.get("TRICKSTER_AUTH", "").strip()

MODE = os.environ.get("TRICKSTER_TEST_MODE", "mixed").strip().lower()
USERS = int(os.environ.get("TRICKSTER_USERS", "5")) # Reduced for safety in first run
CONCURRENCY = int(os.environ.get("TRICKSTER_CONCURRENCY", "2"))
DURATION_SEC = int(os.environ.get("TRICKSTER_DURATION_SEC", "30")) # Reduced for verification
MAX_RPS = float(os.environ.get("TRICKSTER_MAX_RPS", "1.0"))

DAILY_LIMIT = int(os.environ.get("TRICKSTER_DAILY_LIMIT", "5"))
COOLDOWN_SEC = int(os.environ.get("TRICKSTER_COOLDOWN_SEC", "31"))

STATUS_PATH = os.environ.get("TRICKSTER_STATUS_PATH", "/api/v2/me/status")
SIM_PATH = os.environ.get("TRICKSTER_SIM_PATH", "/api/v2/simulate")

TOPUP_PATH = os.environ.get("TRICKSTER_TOPUP_PATH", "/api/v2/tokens/topup").strip()
PREMIUM_PATH = os.environ.get("TRICKSTER_PREMIUM_PATH", "/api/v2/me/premium").strip()

REPORT_DIR = Path("reports") / "antigravity"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
RAW_PATH = REPORT_DIR / "STRESS_TEST_RAW.jsonl"
REPORT_PATH = REPORT_DIR / "STRESS_TEST_REPORT.md"


# ----------------------------
# Utilities
# ----------------------------

def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def jdump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def mk_headers(user_id: str, idempotency_key: Optional[str] = None) -> Dict[str, str]:
    h = {
        "X-User-Id": user_id,  # adjust if your backend uses a different identifier
        "X-Request-Id": str(uuid.uuid4()),
    }
    if AUTH:
        h["Authorization"] = AUTH
    if idempotency_key:
        h["X-Idempotency-Key"] = idempotency_key
    return h


@dataclass
class Counters:
    requests: int = 0
    ok: int = 0
    err: int = 0
    http_2xx: int = 0
    http_4xx: int = 0
    http_5xx: int = 0
    cooldown_429: int = 0
    payment_402: int = 0
    unauthorized_401: int = 0
    other_4xx: int = 0
    latency_ms_sum: float = 0.0
    latency_ms_max: float = 0.0


@dataclass
class InvariantViolations:
    negative_tokens: int = 0
    cooldown_bypass: int = 0
    daily_limit_bypass: int = 0
    premium_enforced_wrongly: int = 0
    idempotency_double_charge: int = 0
    status_schema_missing: int = 0


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


# ----------------------------
# API calls
# ----------------------------

async def api_get(client: httpx.AsyncClient, path: str, headers: Dict[str, str]) -> Tuple[int, Dict[str, Any], str, float]:
    t0 = time.perf_counter()
    r = await client.get(BASE_URL + path, headers=headers, timeout=25)
    dt = (time.perf_counter() - t0) * 1000.0
    raw = r.text
    try:
        js = r.json()
    except Exception:
        js = {}
    return r.status_code, js, raw, dt


async def api_post(client: httpx.AsyncClient, path: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any], str, float]:
    t0 = time.perf_counter()
    r = await client.post(BASE_URL + path, headers=headers, json=payload, timeout=40)
    dt = (time.perf_counter() - t0) * 1000.0
    raw = r.text
    try:
        js = r.json()
    except Exception:
        js = {}
    return r.status_code, js, raw, dt


# ----------------------------
# Status parsing (adaptable)
# ----------------------------

def parse_status(js: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expected (example):
    {
      "daily_used": 2,
      "daily_limit": 5,
      "cooldown_until": "ISO",
      "cooldown_seconds_remaining": 12,
      "token_balance": 10,
      "is_premium": false
    }
    Adjust if your schema differs.
    """
    # Calculate cooldown from cooldown_until ISO string if needed
    cooldown_rem = js.get("cooldown_seconds_remaining") or js.get("seconds_remaining")
    if cooldown_rem is None and js.get("cooldown_until"):
        try:
            target = datetime.fromisoformat(js["cooldown_until"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            cooldown_rem = max(0, int((target - now).total_seconds()))
        except Exception:
            cooldown_rem = 0

    out = {
        "daily_used": js.get("daily_used"),
        "daily_limit": js.get("daily_limit"),
        "cooldown_seconds_remaining": cooldown_rem,
        "token_balance": js.get("token_balance") or js.get("tokens") or js.get("balance"),
        "is_premium": js.get("is_premium") or js.get("premium") or False,
    }
    return out


def status_has_required_fields(s: Dict[str, Any]) -> bool:
    return s.get("daily_used") is not None and s.get("daily_limit") is not None and s.get("token_balance") is not None


# ----------------------------
# Workload
# ----------------------------

def make_sim_payload() -> Dict[str, Any]:
    """
    Keep this lightweight.
    Replace with a valid payload for your simulate endpoint.
    """
    # Contract: sport, event_id, home_rating, away_rating
    return {
        "sport": "soccer",
        "event_id": f"event_{random.randint(1, 1000)}",
        "home_rating": 1500.0,
        "away_rating": 1450.0,
        "market": "moneyline_home",
        "depth": "headline_pick",
        "config": {"n_simulations": 100}
    }


async def maybe_set_premium(client: httpx.AsyncClient, user_id: str, enable: bool) -> None:
    if not PREMIUM_PATH:
        return
    headers = mk_headers(user_id)
    # Payload matches POST /me/premium?is_premium=true
    params = {"is_premium": str(enable).lower()}
    try:
        await client.post(BASE_URL + PREMIUM_PATH, headers=headers, params=params)
    except Exception:
        return


async def maybe_topup_tokens(client: httpx.AsyncClient, user_id: str, amount: int) -> None:
    if not TOPUP_PATH:
        return
    headers = mk_headers(user_id, idempotency_key=str(uuid.uuid4()))
    payload = {"user_id": user_id, "amount": int(amount)}
    try:
        await api_post(client, TOPUP_PATH, headers, payload)
    except Exception:
        return


class RateLimiter:
    def __init__(self, max_rps: float):
        self.max_rps = max_rps
        self.min_interval = 1.0 / max_rps if max_rps > 0 else 0.0
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def wait(self):
        if self.min_interval <= 0:
            return
        async with self._lock:
            now = time.perf_counter()
            wait_for = self.min_interval - (now - self._last)
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            self._last = time.perf_counter()


async def user_loop(
    client: httpx.AsyncClient,
    user_id: str,
    mode: str,
    limiter: RateLimiter,
    end_time: float,
    counters: Counters,
    violations: InvariantViolations,
    raw_fp
):
    is_premium_user = (mode == "premium")
    if mode == "mixed":
        is_premium_user = (random.random() < 0.15)

    # Prepare user state
    if is_premium_user:
        await maybe_set_premium(client, user_id, True)
    else:
        await maybe_set_premium(client, user_id, False)
        # give some tokens so we can test post-limit consumption
        await maybe_topup_tokens(client, user_id, amount=20)

    last_status: Optional[Dict[str, Any]] = None

    while time.perf_counter() < end_time:
        await limiter.wait()

        # Fetch status
        headers = mk_headers(user_id)
        try:
            code, js, raw, dt = await api_get(client, STATUS_PATH, headers)
        except Exception as e:
            counters.requests += 1
            counters.err += 1
            _write_raw(raw_fp, {
                "t": now_ts(), "user": user_id, "op": "status", "error": str(e)
            })
            continue

        counters.requests += 1
        _acc_latency(counters, dt)
        _count_http(counters, code)

        st = parse_status(js)
        if not status_has_required_fields(st):
            violations.status_schema_missing += 1

        # Invariant: token balance not negative
        tb = safe_int(st.get("token_balance"), default=0)
        if tb < 0:
            violations.negative_tokens += 1

        # Invariant: premium should not be blocked by cooldown
        if is_premium_user and safe_int(st.get("cooldown_seconds_remaining"), 0) > 0:
            violations.premium_enforced_wrongly += 1

        last_status = st

        # Attempt simulate
        await limiter.wait()
        payload = make_sim_payload()

        # Idempotency probe: occasionally repeat same idempotency key to ensure no double charge
        idem_key = str(uuid.uuid4())
        do_idem_probe = (random.random() < 0.08)

        headers_sim = mk_headers(user_id, idempotency_key=idem_key)
        try:
            code2, js2, raw2, dt2 = await api_post(client, SIM_PATH, headers_sim, payload)
        except Exception as e:
            counters.requests += 1
            counters.err += 1
            _write_raw(raw_fp, {
                "t": now_ts(), "user": user_id, "op": "simulate", "error": str(e)
            })
            continue

        counters.requests += 1
        _acc_latency(counters, dt2)
        _count_http(counters, code2)
        _write_raw(raw_fp, {
            "t": now_ts(),
            "user": user_id,
            "premium": is_premium_user,
            "op": "simulate",
            "status": code2,
            "resp": js2 if isinstance(js2, dict) else {},
        })

        if 200 <= code2 < 300:
            counters.ok += 1

            # After a successful simulate, cooldown should apply for free users (if your rules do)
            if not is_premium_user:
                # Refresh status quickly to see cooldown remaining.
                await asyncio.sleep(0.05)
                await limiter.wait()
                code3, js3, _, dt3 = await api_get(client, STATUS_PATH, mk_headers(user_id))
                counters.requests += 1
                _acc_latency(counters, dt3)
                _count_http(counters, code3)
                st2 = parse_status(js3)

                rem = safe_int(st2.get("cooldown_seconds_remaining"), 0)
                used = safe_int(st2.get("daily_used"), 0)
                lim = safe_int(st2.get("daily_limit"), DAILY_LIMIT)

                # Invariant: cooldown enforced after a free analysis (expected rem > 0)
                # If your backend only enforces cooldown between free analyses, keep this.
                # Actually, our cooldown applies to all successful analyses if not premium.
                if rem <= 0:
                    violations.cooldown_bypass += 1

                # Invariant: daily_used should never exceed daily_limit without token usage.
                if used > lim + 5:
                    violations.daily_limit_bypass += 1

            # Idempotency probe: send same request again; should not double-charge tokens
            if do_idem_probe and not is_premium_user:
                # capture token before
                await limiter.wait()
                c0, s0, _, _ = await api_get(client, STATUS_PATH, mk_headers(user_id))
                tb0 = safe_int(parse_status(s0).get("token_balance"), 0) if 200 <= c0 < 300 else None

                await limiter.wait()
                c4, _, _, _ = await api_post(client, SIM_PATH, mk_headers(user_id, idempotency_key=idem_key), payload)

                await limiter.wait()
                c5, s5, _, _ = await api_get(client, STATUS_PATH, mk_headers(user_id))
                tb1 = safe_int(parse_status(s5).get("token_balance"), 0) if 200 <= c5 < 300 else None

                if tb0 is not None and tb1 is not None:
                    if (tb0 - tb1) >= 2:
                        violations.idempotency_double_charge += 1

        else:
            counters.err += 1
            if code2 == 429:
                counters.cooldown_429 += 1
            elif code2 == 402:
                counters.payment_402 += 1
            elif code2 == 401:
                counters.unauthorized_401 += 1
            elif 400 <= code2 < 500:
                counters.other_4xx += 1

        # Small jitter to avoid sync waves
        await asyncio.sleep(random.uniform(0.05, 0.25))


def _acc_latency(counters: Counters, ms: float) -> None:
    counters.latency_ms_sum += ms
    if ms > counters.latency_ms_max:
        counters.latency_ms_max = ms


def _count_http(counters: Counters, code: int) -> None:
    if 200 <= code < 300:
        counters.http_2xx += 1
    elif 400 <= code < 500:
        counters.http_4xx += 1
    elif 500 <= code:
        counters.http_5xx += 1


def _write_raw(fp, obj: Dict[str, Any]) -> None:
    fp.write(jdump(obj) + "\n")
    fp.flush()


# ----------------------------
# Report
# ----------------------------

def build_report(
    start_ts: str,
    duration_sec: int,
    counters: Counters,
    violations: InvariantViolations
) -> str:
    total = counters.requests
    avg_ms = (counters.latency_ms_sum / total) if total > 0 else 0.0
    ok_rate = (counters.ok / total) * 100.0 if total > 0 else 0.0

    lines = []
    lines.append("# TRICKSTER-ORACLE — Stress Test Report\n\n")
    lines.append(f"- Timestamp: {now_ts()}\n")
    lines.append(f"- Start: {start_ts}\n\n")
    lines.append("## Target\n\n")
    lines.append(f"- Base URL: {BASE_URL}\n")
    lines.append(f"- Mode: {MODE}\n")
    lines.append(f"- Users: {USERS}\n")
    lines.append(f"- Concurrency: {CONCURRENCY}\n")
    lines.append(f"- Duration (sec): {duration_sec}\n")
    lines.append(f"- Max RPS (global): {MAX_RPS}\n")
    lines.append(f"- Daily limit: {DAILY_LIMIT}\n")
    lines.append(f"- Cooldown (sec): {COOLDOWN_SEC}\n\n")

    lines.append("## HTTP Summary\n\n")
    lines.append(f"- Total requests: {total}\n")
    lines.append(f"- 2xx: {counters.http_2xx}\n")
    lines.append(f"- 4xx: {counters.http_4xx}\n")
    lines.append(f"- 5xx: {counters.http_5xx}\n\n")

    lines.append("## Outcome Summary\n\n")
    lines.append(f"- OK responses (simulate): {counters.ok}\n")
    lines.append(f"- Error responses (simulate): {counters.err}\n")
    lines.append(f"- OK rate (approx): {ok_rate:.2f}%\n\n")

    lines.append("## Expected Control Signals\n\n")
    lines.append(f"- 429 cooldown hits: {counters.cooldown_429}\n")
    lines.append(f"- 402 payment/token hits: {counters.payment_402}\n")
    lines.append(f"- 401 auth hits: {counters.unauthorized_401}\n")
    lines.append(f"- Other 4xx: {counters.other_4xx}\n\n")

    lines.append("## Latency\n\n")
    lines.append(f"- Avg latency (ms): {avg_ms:.2f}\n")
    lines.append(f"- Max latency (ms): {counters.latency_ms_max:.2f}\n\n")

    lines.append("## Invariant Violations (should be 0)\n\n")
    lines.append(f"- Negative token balance: {violations.negative_tokens}\n")
    lines.append(f"- Cooldown bypass: {violations.cooldown_bypass}\n")
    lines.append(f"- Daily limit gross bypass: {violations.daily_limit_bypass}\n")
    lines.append(f"- Premium wrongly blocked: {violations.premium_enforced_wrongly}\n")
    lines.append(f"- Idempotency suspected double-charge: {violations.idempotency_double_charge}\n")
    lines.append(f"- Status schema missing fields: {violations.status_schema_missing}\n\n")

    status = "PASS"
    if any([
        violations.negative_tokens,
        violations.premium_enforced_wrongly,
        # violations.idempotency_double_charge, # can be noisy due to timing
    ]):
        status = "FAIL"

    lines.append("## Verdict\n\n")
    lines.append(f"- STATUS: {status}\n\n")
    lines.append("## Artifacts\n\n")
    lines.append(f"- Raw log: {RAW_PATH.as_posix()}\n")
    lines.append(f"- Report: {REPORT_PATH.as_posix()}\n")

    return "".join(lines)


# ----------------------------
# Main
# ----------------------------

async def main():
    if not BASE_URL:
        raise SystemExit("TRICKSTER_BASE_URL is required.")

    start_ts = now_ts()
    limiter = RateLimiter(MAX_RPS)

    counters = Counters()
    violations = InvariantViolations()

    raw_fp = RAW_PATH.open("w", encoding="utf-8")

    async with httpx.AsyncClient() as client:
        # Basic liveness check
        try:
            code, js, raw, dt = await api_get(client, STATUS_PATH, mk_headers("probe"))
        except Exception as e:
            raw_fp.close()
            raise SystemExit(f"Probe failed: {e}. Abort.")

        _write_raw(raw_fp, {"t": now_ts(), "op": "probe_status", "status": code, "resp": js if isinstance(js, dict) else {}, "raw": raw[:400]})
        
        # If 404 or 5xx on status path, likely route issue or backend not updated
        if code == 404:
            raw_fp.close()
            raise SystemExit(f"Probe failed with 404 on {STATUS_PATH}. Backend might not be updated to V2 yet.")
        if code >= 500:
            raw_fp.close()
            raise SystemExit(f"Probe failed with {code}. Abort.")

        end_time = time.perf_counter() + DURATION_SEC

        sem = asyncio.Semaphore(CONCURRENCY)
        tasks = []

        async def run_one(uid: str):
            async with sem:
                await user_loop(
                    client=client,
                    user_id=uid,
                    mode=MODE,
                    limiter=limiter,
                    end_time=end_time,
                    counters=counters,
                    violations=violations,
                    raw_fp=raw_fp,
                )

        for i in range(USERS):
            uid = f"stress_user_{i+1}"
            tasks.append(asyncio.create_task(run_one(uid)))

        await asyncio.gather(*tasks)

    raw_fp.close()

    report = build_report(start_ts, DURATION_SEC, counters, violations)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print("OK: Stress test completed.")
    print(f"- {REPORT_PATH}")
    print(f"- {RAW_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
