#!/usr/bin/env python3
"""
ANTIGRAVITY — TRICKSTER-ORACLE
REDIS ACCESS CONTROL CORRECTION (Minimal + Evidence)

GOAL
Ensure Redis is secured correctly:
- Prefer internal Redis URL for Render-to-Render traffic.
- Avoid unnecessary external allowlists (Hostinger ranges) unless explicitly required.
- Write an audit report and apply minimal patch to render.yaml if needed.

NON-NEGOTIABLE
- Minimal changes only.
- No refactors.
- Produce evidence.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
RENDER_YAML = ROOT / "render.yaml"
REPORT_DIR = ROOT / "reports" / "antigravity"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT = REPORT_DIR / "REDIS_ACCESS_CONTROL_AUDIT.md"

HOSTINGER_RANGES = {"74.220.48.0/24", "74.220.56.0/24"}

def sh(cmd: list[str], check=True) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    if check and p.returncode != 0:
        raise RuntimeError(out)
    return out

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def write_text(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8")

def find_internal_redis_indicators(text: str) -> bool:
    # Heuristic: internal Render KV/Redis host often looks like red-xxxxx:6379 (no scheme) or contains "red-"
    # External often looks like redis:// or rediss:// with user/pass and a public host
    return bool(re.search(r"\bred-\w{6,}\b.*:6379", text)) or ("INTERNAL" in text.upper())

def find_external_redis_indicators(text: str) -> bool:
    return ("redis://" in text) or ("rediss://" in text)

def remove_hostinger_allowlist(yaml_text: str) -> tuple[str, bool]:
    # Remove ipAllowList entries that match the Hostinger ranges.
    changed = False
    lines = yaml_text.splitlines()
    out = []
    skip_block = False
    for i, line in enumerate(lines):
        # naive but safe: if a line contains the CIDR, skip that line and the next description line if indented similarly
        if any(rng in line for rng in HOSTINGER_RANGES):
            changed = True
            continue
        # remove accompanying description lines right after the source line if they contain "Hostinger"
        if "description:" in line and "Hostinger" in line:
            changed = True
            continue
        out.append(line)
    return "\n".join(out) + ("\n" if yaml_text.endswith("\n") else ""), changed

def audit():
    if not RENDER_YAML.exists():
        raise SystemExit("render.yaml not found at repo root.")

    y = read_text(RENDER_YAML)

    has_allowlist = "ipAllowList" in y
    has_hostinger = any(rng in y for rng in HOSTINGER_RANGES)

    internal_hint = find_internal_redis_indicators(y)
    external_hint = find_external_redis_indicators(y)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_lines = []
    report_lines.append("# Redis Access Control Audit\n")
    report_lines.append(f"- Timestamp: {ts}\n")
    report_lines.append(f"- render.yaml present: true\n")
    report_lines.append(f"- ipAllowList present: {has_allowlist}\n")
    report_lines.append(f"- Hostinger ranges present: {has_hostinger}\n")
    report_lines.append(f"- Internal Redis indicator found (heuristic): {internal_hint}\n")
    report_lines.append(f"- External Redis indicator found (heuristic): {external_hint}\n\n")

    decision = "KEEP"  # default
    rationale = []

    # Policy:
    # If no explicit need for external redis and we're likely using internal, remove hostinger allowlist.
    if has_hostinger and internal_hint and not external_hint:
        decision = "REMOVE_HOSTINGER_ALLOWLIST"
        rationale.append("Render-to-Render traffic should use internal Redis URL; external allowlist not needed.")
        rationale.append("Hostinger IP ranges are irrelevant unless Redis is accessed externally from Hostinger.")
    elif has_hostinger and not external_hint:
        decision = "REMOVE_HOSTINGER_ALLOWLIST"
        rationale.append("No evidence of external Redis URL usage; keep Redis closed to external access.")
    else:
        rationale.append("Insufficient signal to auto-remove allowlist (possible external usage). Manual review advised.")

    report_lines.append("## Decision\n")
    report_lines.append(f"- Decision: **{decision}**\n")
    report_lines.append("## Rationale\n")
    for r in rationale:
        report_lines.append(f"- {r}\n")

    changed = False
    if decision == "REMOVE_HOSTINGER_ALLOWLIST":
        new_y, changed = remove_hostinger_allowlist(y)
        if changed:
            write_text(RENDER_YAML, new_y)
            report_lines.append("\n## Patch\n- Removed Hostinger CIDR entries from ipAllowList in render.yaml.\n")
        else:
            report_lines.append("\n## Patch\n- No patch applied (ranges not found).\n")
    else:
        report_lines.append("\n## Patch\n- No automatic patch applied.\n")

    write_text(REPORT, "".join(report_lines))

    if changed:
        sh(["git", "add", "render.yaml", str(REPORT)])
        sh(["git", "commit", "-m", "chore(security): remove unnecessary Redis external allowlist"])
        sh(["git", "push", "origin", "master"])

    print(f"[OK] Wrote report: {REPORT}")
    if changed:
        print("[OK] Patch committed and pushed.")
    else:
        print("[OK] No repo changes were required.")

if __name__ == "__main__":
    audit()
