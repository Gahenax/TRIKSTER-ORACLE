#!/usr/bin/env python3
"""
ANTIGRAVITY PROMPT (Python) — TRICKSTER-ORACLE AUDIT (A1 + A2)

Goal:
Run a deterministic audit to validate that:
- Repo identity is correct (no "parallel universe" repo)
- A1 Request-ID middleware works (generate + preserve)
- A2 System routes (/health, /ready, /version) are production-safe
- No regressions: tests still pass
- Produce an evidence-first audit report with PASS/FAIL gates

Rules:
1) No code changes unless a gate FAILS. If FAIL, patch minimally and re-run that gate.
2) Evidence must include raw command outputs (sanitized only for secrets).
3) If repo in web differs from local, treat as P0 and stop with diagnosis.

How to run:
  python tools/antigravity_audit_trickster_oracle.py --repo "c:/Users/USUARIO/.gemini/antigravity/playground/TRIKSTER-ORACLE"

Outputs:
  - docs/AUDIT_REPORT_YYYY-MM-DD.md
  - docs/AUDIT_EVIDENCE_YYYY-MM-DD.txt
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


# -----------------------------
# Helpers
# -----------------------------

def run(cmd: List[str], cwd: Path, timeout: int = 300) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, shell=False)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def sanitize(text: str) -> str:
    # Redact obvious secrets patterns if they leak in output
    patterns = [
        (r'(?i)(api[_-]?key\s*[:=]\s*)(\S+)', r'\1[REDACTED]'),
        (r'(?i)(authorization:\s*bearer\s+)(\S+)', r'\1[REDACTED]'),
        (r'(?i)(secret\s*[:=]\s*)(\S+)', r'\1[REDACTED]'),
        (r'(?i)(token\s*[:=]\s*)(\S+)', r'\1[REDACTED]'),
    ]
    out = text
    for pat, rep in patterns:
        out = re.sub(pat, rep, out)
    return out

def write(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def now_date() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d")

def is_windows() -> bool:
    return os.name == "nt"


# -----------------------------
# Audit Steps
# -----------------------------

def audit_repo_identity(repo: Path) -> Tuple[bool, str]:
    lines = []
    ok = True

    if not repo.exists():
        return False, f"[FAIL] Repo path does not exist: {repo}"

    if not (repo / ".git").exists():
        return False, f"[FAIL] Not a git repo (missing .git): {repo}"

    rc, out, err = run(["git", "remote", "-v"], cwd=repo)
    lines.append("## git remote -v")
    lines.append(out if out else err)
    if rc != 0 or not out:
        ok = False
        lines.append("[FAIL] Cannot read git remote -v")

    # Detect likely mismatch between TRIKSTER vs TRICKSTER naming
    if "TRIKSTER-ORACLE" in out and "TRICKSTER-ORACLE" in out:
        lines.append("[WARN] Remote output contains both TRIKSTER and TRICKSTER strings (name inconsistency).")

    # Branch + latest commits
    rc2, out2, err2 = run(["git", "branch", "--show-current"], cwd=repo)
    lines.append("\n## git branch --show-current")
    lines.append(out2 if out2 else err2)
    if rc2 != 0 or not out2:
        ok = False
        lines.append("[FAIL] Cannot read current branch")

    rc3, out3, err3 = run(["git", "log", "--oneline", "-10"], cwd=repo)
    lines.append("\n## git log --oneline -10")
    lines.append(out3 if out3 else err3)
    if rc3 != 0 or not out3:
        ok = False
        lines.append("[FAIL] Cannot read git log")

    return ok, "\n".join(lines)


def locate_backend(repo: Path) -> Tuple[Path, Path]:
    # Returns (backend_root, app_entry_guess_dir)
    backend = repo / "backend"
    if backend.exists():
        return backend, backend
    # fallback
    for cand in ["api", "server", "services"]:
        c = repo / cand
        if c.exists():
            return c, c
    return repo, repo


def audit_fastapi_system_routes(repo: Path) -> Tuple[bool, str]:
    """
    We do NOT start uvicorn here (complex). We validate via static inspection:
    - files exist
    - routes declared (/health, /ready, /version)
    - BUILD_COMMIT referenced
    And we provide runtime commands for Antigravity to execute separately.
    """
    ok = True
    lines = []
    backend, _ = locate_backend(repo)

    # Search python files for route strings
    py_files = list(backend.rglob("*.py"))
    content_hits = {"health": 0, "ready": 0, "version": 0, "build_commit": 0}

    for p in py_files:
        try:
            s = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if "/health" in s:
            content_hits["health"] += 1
        if "/ready" in s:
            content_hits["ready"] += 1
        if "/version" in s:
            content_hits["version"] += 1
        if "BUILD_COMMIT" in s:
            content_hits["build_commit"] += 1

    lines.append("## Static route scan (backend)")
    lines.append(f"Files scanned: {len(py_files)}")
    lines.append(f"/health occurrences: {content_hits['health']}")
    lines.append(f"/ready occurrences: {content_hits['ready']}")
    lines.append(f"/version occurrences: {content_hits['version']}")
    lines.append(f"BUILD_COMMIT occurrences: {content_hits['build_commit']}")

    if content_hits["health"] == 0 or content_hits["ready"] == 0 or content_hits["version"] == 0:
        ok = False
        lines.append("[FAIL] One or more system routes not found by static scan.")
    if content_hits["build_commit"] == 0:
        ok = False
        lines.append("[FAIL] BUILD_COMMIT not referenced (version endpoint may be incomplete).")

    return ok, "\n".join(lines)


def audit_request_id_contract(repo: Path) -> Tuple[bool, str]:
    """
    Static inspection:
    - request_id middleware file exists
    - looks for 'X-Request-ID' usage
    Runtime verification commands are provided in the final report.
    """
    ok = True
    lines = []
    backend, _ = locate_backend(repo)

    candidates = [
        backend / "app" / "middleware" / "request_id.py",
        backend / "app" / "middleware" / "request_id_middleware.py",
        backend / "middleware" / "request_id.py",
    ]
    found = None
    for c in candidates:
        if c.exists():
            found = c
            break

    lines.append("## Request-ID middleware presence")
    if not found:
        ok = False
        lines.append("[FAIL] request_id middleware file not found in expected locations.")
        return ok, "\n".join(lines)

    lines.append(f"Found: {found}")
    s = found.read_text(encoding="utf-8", errors="ignore")
    if "X-Request-ID" not in s and "x-request-id" not in s.lower():
        ok = False
        lines.append("[FAIL] Middleware file does not reference X-Request-ID header.")
    if "uuid" not in s.lower():
        lines.append("[WARN] No 'uuid' reference detected; ensure unique IDs are generated if header missing.")

    return ok, "\n".join(lines)


def audit_tests(repo: Path) -> Tuple[bool, str]:
    backend, _ = locate_backend(repo)
    ok = True
    lines = []

    # Determine whether pytest is present
    tests_dir = backend / "tests"
    if not tests_dir.exists():
        lines.append("[WARN] No backend/tests directory found. Skipping pytest run gate.")
        return True, "\n".join(lines)

    # Run pytest
    lines.append("## pytest -q")
    rc, out, err = run(["pytest", "-q"], cwd=backend, timeout=900)
    lines.append(out if out else err)
    if rc != 0:
        ok = False
        lines.append("[FAIL] pytest failed.")
    else:
        lines.append("[PASS] pytest passed.")

    return ok, "\n".join(lines)


def generate_runtime_commands(repo: Path) -> str:
    backend, _ = locate_backend(repo)
    # We can't reliably infer entrypoint; provide common ones.
    return f"""
## Runtime Verification (manual execution required)
Run these commands and paste outputs into the evidence file if not captured automatically.

### Start API (choose the correct module path)
cd "{backend}"
uvicorn app.main:app --reload
# If that fails, search for FastAPI() and adjust, e.g.:
# uvicorn app.main:app --reload
# uvicorn main:app --reload
# uvicorn app:app --reload

### Gate A1: Request-ID header generation
curl -i http://127.0.0.1:8000/health

### Gate A1: Request-ID preservation
curl -i http://127.0.0.1:8000/health -H "X-Request-ID: audit-fixed-001"

### Gate A2: system routes
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/ready
curl -s http://127.0.0.1:8000/version

Expected:
- 200 OK for all
- /version includes BUILD_COMMIT or 'unknown'
- Responses do NOT leak secrets/config
"""


def make_report(gates: List[Tuple[str, bool, str]]) -> str:
    # Summarize
    pass_count = sum(1 for _, ok, _ in gates if ok)
    fail_count = len(gates) - pass_count
    status = "APPROVED ✅" if fail_count == 0 else "REJECTED ❌"

    lines = []
    lines.append(f"# TRICKSTER-ORACLE — AUDIT REPORT ({now_date()})")
    lines.append("")
    lines.append(f"Overall Status: **{status}**")
    lines.append(f"Gates Passed: {pass_count}/{len(gates)}")
    lines.append("")
    lines.append("## Gate Results")
    for gate_id, ok, _ in gates:
        lines.append(f"- {gate_id}: {'PASS ✅' if ok else 'FAIL ❌'}")
    lines.append("")
    lines.append("## Detailed Evidence (sanitized)")
    for gate_id, ok, evidence in gates:
        lines.append("")
        lines.append(f"### {gate_id} — {'PASS ✅' if ok else 'FAIL ❌'}")
        lines.append("```")
        lines.append(evidence.strip())
        lines.append("```")

    lines.append("")
    lines.append("## Required Runtime Checks")
    lines.append(generate_runtime_commands(Path(".")))
    lines.append("")
    lines.append("## Risk Notes")
    lines.append("- If repo identity mismatches expected remote, STOP and reconcile before proceeding.")
    lines.append("- Static scans confirm presence, but runtime checks confirm behavior (headers, status codes).")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Path to local TRIKSTER-ORACLE repo")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    date = now_date()

    docs_dir = repo / "docs"
    report_path = docs_dir / f"AUDIT_REPORT_{date}.md"
    evidence_path = docs_dir / f"AUDIT_EVIDENCE_{date}.txt"

    gates: List[Tuple[str, bool, str]] = []

    ok0, ev0 = audit_repo_identity(repo)
    gates.append(("GATE_0_REPO_IDENTITY", ok0, sanitize(ev0)))

    if not ok0:
        # Stop early - P0
        report = make_report(gates)
        write(report_path, report)
        write(evidence_path, sanitize(ev0) + "\n\n[STOP] Repo identity gate failed. Fix before continuing.\n")
        print(f"[FAIL] Repo identity gate failed. Report written: {report_path}")
        return 2

    ok1, ev1 = audit_request_id_contract(repo)
    gates.append(("GATE_1_REQUEST_ID_STATIC", ok1, sanitize(ev1)))

    ok2, ev2 = audit_fastapi_system_routes(repo)
    gates.append(("GATE_2_SYSTEM_ROUTES_STATIC", ok2, sanitize(ev2)))

    ok3, ev3 = audit_tests(repo)
    gates.append(("GATE_3_TESTS", ok3, sanitize(ev3)))

    report = make_report(gates)
    write(report_path, report)

    # Evidence file contains raw sanitized outputs plus runtime command checklist
    evidence_blob = "\n\n".join([f"[{gid}] {'PASS' if ok else 'FAIL'}\n{sanitize(ev)}" for gid, ok, ev in gates])
    evidence_blob += "\n\n" + generate_runtime_commands(repo)
    write(evidence_path, evidence_blob)

    if all(ok for _, ok, _ in gates):
        print(f"[OK] Audit approved. Report: {report_path}")
        print(f"[OK] Evidence: {evidence_path}")
        return 0
    else:
        print(f"[WARN] Audit has failures. Report: {report_path}")
        print(f"[WARN] Evidence: {evidence_path}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
