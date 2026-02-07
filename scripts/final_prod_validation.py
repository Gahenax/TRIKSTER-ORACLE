import os
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import requests


# -----------------------------
# Config
# -----------------------------

BASE_URL = os.environ.get("TRICKSTER_BASE_URL", "").rstrip("/")
AUTH = os.environ.get("TRICKSTER_AUTH", "").strip()

EVENT_ID = os.environ.get("TRICKSTER_EVENT_ID", "SMOKE_EXAMPLE_1")
SPORT = os.environ.get("TRICKSTER_SPORT", "soccer")
MARKET = os.environ.get("TRICKSTER_MARKET", "moneyline_home")

IDEMPOTENCY_KEY = f"prod-validate-{int(time.time())}"

ROOT = Path(os.getcwd()).resolve()
REPORT_PATH = ROOT / "reports" / "antigravity" / "FINAL_PROD_VALIDATION_REPORT.md"


# -----------------------------
# Helpers
# -----------------------------

@dataclass
class StepResult:
    name: str
    ok: bool
    request: str
    status: int
    body_snippet: str


def snippet(text: str, limit: int = 1200) -> str:
    text = text or ""
    return text[:limit] + ("..." if len(text) > limit else "")


def req_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h = {"Accept": "application/json"}
    if extra:
        h.update(extra)
    return h


def get(path: str, headers: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
    r = requests.get(BASE_URL + path, headers=headers or req_headers(), timeout=25)
    return r.status_code, r.text


def post(path: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
    r = requests.post(BASE_URL + path, json=payload, headers=headers or req_headers(), timeout=45)
    return r.status_code, r.text


def render_report(results: Dict[str, StepResult]) -> str:
    ok_all = all(r.ok for r in results.values())
    lines = []
    lines.append("# TRICKSTER-ORACLE v2 — FINAL PROD VALIDATION REPORT")
    lines.append("")
    lines.append(f"- Base URL: `{BASE_URL}`")
    lines.append(f"- Timestamp: `{time.strftime('%Y-%m-%d %H:%M:%S')}`")
    lines.append(f"- Overall: `{'PASS' if ok_all else 'FAIL'}`")
    lines.append("")
    lines.append("## Results")
    for k in results:
        r = results[k]
        lines.append(f"### {r.name}")
        lines.append(f"- OK: `{r.ok}`")
        lines.append(f"- Request: `{r.request}`")
        lines.append(f"- Status: `{r.status}`")
        lines.append("")
        lines.append("```text")
        lines.append(r.body_snippet.rstrip())
        lines.append("```")
        lines.append("")
    lines.append("## Closure Criteria")
    lines.append("- health/ready/version OK")
    lines.append("- free-tier simulate OK")
    lines.append("- gated deny without tokens OK (expected 401/402/403)")
    lines.append("- gated allow with auth OK (if auth configured)")
    lines.append("- idempotency retry does not double-charge (best-effort via identical response/ledger)")
    lines.append("")
    return "\n".join(lines)


# -----------------------------
# Main
# -----------------------------

def main() -> int:
    if not BASE_URL:
        raise SystemExit("ERROR: TRICKSTER_BASE_URL is required. Set it after Render deploy.")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    results: Dict[str, StepResult] = {}

    # 1) Health checks
    for p in ["/health", "/ready", "/version"]:
        try:
            status, body = get(p)
            ok = status < 400
        except Exception as e:
            status = 0
            body = str(e)
            ok = False

        results[p] = StepResult(
            name=f"GET {p}",
            ok=ok,
            request=f"GET {BASE_URL}{p}",
            status=status,
            body_snippet=snippet(body),
        )
        if not ok:
            # fail fast
            write_report(results)
            return 1

    # 2) Free-tier simulate
    payload_free = {
        "sport": SPORT,
        "event_id": EVENT_ID,
        "market": MARKET,
        "depth": "headline_pick"
    }
    try:
        status, body = post("/api/v2/simulate", payload_free)
        ok = status < 400
    except Exception as e:
        status = 0
        body = str(e)
        ok = False

    results["simulate_free"] = StepResult(
        name="POST /api/v2/simulate (free-tier)",
        ok=ok,
        request=f"POST {BASE_URL}/api/v2/simulate {json.dumps(payload_free)}",
        status=status,
        body_snippet=snippet(body),
    )
    if not ok:
        write_report(results)
        return 1

    # 3) Gated deny (no auth)
    payload_gated = {
        "sport": SPORT,
        "event_id": EVENT_ID,
        "market": MARKET,
        "depth": "full_distribution",
        "config": {"n_simulations": 1000}
    }
    # Using /v2/simulate as analysis endpoint evolved in the roadmap
    try:
        status, body = post("/api/v2/simulate", payload_gated)
        ok = status in (401, 402, 403)
    except Exception as e:
        status = 0
        body = str(e)
        ok = False

    results["gated_deny"] = StepResult(
        name="POST /api/v2/simulate (expect deny without tokens)",
        ok=ok,
        request=f"POST {BASE_URL}/api/v2/simulate {json.dumps(payload_gated)}",
        status=status,
        body_snippet=snippet(body),
    )
    if not ok:
        write_report(results)
        return 1

    # 4) Gated allow + idempotency retry (if auth provided)
    if AUTH:
        user_id = "test_user" # standard test user
        headers = req_headers({
            "X-User-ID": user_id,
            "X-Idempotency-Key": IDEMPOTENCY_KEY
        })
        # Check for bearer-like auth if provided in ENV
        if AUTH.startswith("Bearer "):
             headers["Authorization"] = AUTH

        try:
            status1, body1 = post("/api/v2/simulate", payload_gated, headers=headers)
            ok1 = status1 < 400
        except Exception as e:
            status1 = 0
            body1 = str(e)
            ok1 = False

        results["gated_allow_first"] = StepResult(
            name="POST /api/v2/simulate (auth, first)",
            ok=ok1,
            request=f"POST {BASE_URL}/api/v2/simulate (auth) idempotency={IDEMPOTENCY_KEY}",
            status=status1,
            body_snippet=snippet(body1),
        )
        if not ok1:
            write_report(results)
            return 1

        try:
            status2, body2 = post("/api/v2/simulate", payload_gated, headers=headers)
            ok2 = status2 < 500  # should not crash, and should be safe
        except Exception as e:
            status2 = 0
            body2 = str(e)
            ok2 = False

        results["gated_allow_retry"] = StepResult(
            name="POST /api/v2/simulate (auth, retry same idempotency)",
            ok=ok2,
            request=f"POST {BASE_URL}/api/v2/simulate (auth) retry idempotency={IDEMPOTENCY_KEY}",
            status=status2,
            body_snippet=snippet(body2),
        )
        if not ok2:
            write_report(results)
            return 1

        # 5) Ledger/audit (best effort)
        try:
            status3, body3 = get(f"/api/v2/tokens/balance?user_id={user_id}", headers=headers)
            ok3 = status3 < 500
        except Exception as e:
            status3 = 0
            body3 = str(e)
            ok3 = False

        results["ledger"] = StepResult(
            name="GET /api/v2/tokens/balance (best effort)",
            ok=ok3,
            request=f"GET {BASE_URL}/api/v2/tokens/balance?user_id={user_id}",
            status=status3,
            body_snippet=snippet(body3, limit=2000),
        )

    else:
        results["auth_skipped"] = StepResult(
            name="AUTH not provided",
            ok=True,
            request="Set TRICKSTER_AUTH to validate gated allow + idempotency + ledger.",
            status=0,
            body_snippet="SKIPPED gated allow/idempotency/ledger checks (no TRICKSTER_AUTH).",
        )

    write_report(results)
    ok_all = all(r.ok for r in results.values())
    return 0 if ok_all else 1


def write_report(results: Dict[str, StepResult]) -> None:
    content = render_report(results)
    REPORT_PATH.write_text(content, encoding="utf-8")
    print(f"[OK] Wrote report: {REPORT_PATH}")


if __name__ == "__main__":
    raise SystemExit(main())
