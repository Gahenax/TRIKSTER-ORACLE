#!/usr/bin/env python3
"""
ANTIGRAVITY — Trickster v2 Continuation Prompt (Post M1–M3)

MISSION
1) Production Gate: freeze API contract + deploy safely with rollback + evidence.
2) Implement M4 UI_PICK_V2.
3) Implement M5 TRICKSTER_LAB.
4) Implement M6 VERIFICATION_RELEASE.

NON-NEGOTIABLE RULES
- Strict causality: deploy safety & contract before UI/Lab.
- Small, verifiable commits per milestone (M4, M5, M6 and deploy gate steps).
- After each milestone: run deterministic checks and record evidence.
- Server-side token enforcement only (no client-only gating).
- No gambling-forward copy; keep educational/analytics framing.
- No speculative refactors; patch minimally.

OUTPUT REQUIRED (end)
- Executive summary
- Changes per milestone (files, diff overview)
- Verification evidence (commands + outputs)
- Risk notes + rollback steps
- Next actions queue (prioritized)
"""

from __future__ import annotations

import os
import sys
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


# -----------------------------
# Helpers
# -----------------------------

def sh(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> Tuple[int, str]:
    p = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    out, _ = p.communicate()
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{out}")
    return p.returncode, out


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def file_exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def dir_exists(path: Path) -> bool:
    return path.exists() and path.is_dir()


@dataclass
class Evidence:
    name: str
    command: str
    output: str


@dataclass
class PatchRecord:
    milestone: str
    summary: str
    files_touched: List[str]
    evidence: List[Evidence]
    risks: List[str]
    rollback: List[str]


# -----------------------------
# Paths / Repo
# -----------------------------

REPO_ROOT = Path(os.getcwd()).resolve()
REPORTS_DIR = REPO_ROOT / "reports" / "antigravity"
RUNBOOK_PATH = REPORTS_DIR / "TRICKSTER_v2_CONTINUATION_RUNBOOK.json"
FINAL_REPORT = REPORTS_DIR / "TRICKSTER_v2_M4_M6_EXEC_REPORT.md"

# Optional: configure these if your repo has subfolders
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"

# -----------------------------
# Specs (Contract + UI Behavior)
# -----------------------------

CONTRACT_V2_SPEC = {
    "distribution_object": {
        "required_fields": [
            "sport",
            "event_id",
            "market",
            "model_version",
            "n_sims",
            "ci_level",
            "percentiles",
            "mean",
            "stdev",
            "scenarios",
            "uncertainty"
        ],
        "percentiles": ["p5", "p25", "p50", "p75", "p95"],
        "scenarios": ["conservative", "base", "aggressive"],
        "uncertainty": ["volatility_score", "data_quality_index", "confidence_decay"]
    },
    "token_gating": {
        "principle": "tokens buy depth (analysis, scenarios, export), not 'winning picks'",
        "tiers": [
            {"feature": "headline_pick", "cost_tokens": 0},
            {"feature": "full_distribution", "cost_tokens": 2},
            {"feature": "scenario_extremes", "cost_tokens": 3},
            {"feature": "comparative_analysis", "cost_tokens": 3},
            {"feature": "deep_dive_educational", "cost_tokens": 5}
        ],
        "idempotency_required": True,
        "audit_trail_required": True
    }
}

DEPLOY_GATE_SPEC = {
    "preferred_strategy": "versioned_routes",
    "option_versioned_routes": {
        "base": "/api/v2",
        "endpoints_min": ["/simulate", "/analysis", "/tokens/ledger"],
        "compat": "do not break /api/v1"
    },
    "option_feature_flags": {
        "flags": ["SIM_ENGINE_V2", "TOKENS_ENFORCEMENT"],
        "default": "off",
        "rollout": "by env var or config"
    },
    "smoke_tests": [
        "health_ready_version",
        "free_tier_access",
        "token_denial_no_balance",
        "token_charge_once_with_idempotency_retry",
        "audit_trail_written"
    ]
}

UI_M4_SPEC = {
    "pick_v2_view": [
        "percentiles_table",
        "scenarios_summary",
        "uncertainty_badges_or_panel",
        "graceful_degrade_if_missing_fields",
        "no gambling-forward copy"
    ],
    "integration": "use /api/v2 if available; else adapter layer with minimal transformation"
}

LAB_M5_SPEC = {
    "modules_min": 4,
    "format": "static JSON first",
    "unlock": "reuse token gating server-side",
    "progress": "minimal (local ok), but must not break"
}


# -----------------------------
# Runbook Instructions
# -----------------------------

MILESTONES = [
    "B1_CONTRACT_AND_DEPLOY_GATE",
    "M4_UI_PICK_V2",
    "M5_TRICKSTER_LAB",
    "M6_VERIFICATION_RELEASE"
]

INSTRUCTIONS = {
    "B1_CONTRACT_AND_DEPLOY_GATE": """
1) Create/confirm API contract doc:
   - Create docs/API_CONTRACT_v2.md (or similar) describing DistributionObject + uncertainty + token gating.
   - Include sanitized example requests/responses.
2) Implement production-safe exposure:
   Preferred: add /api/v2 routes that call existing v2 engine (M1–M3).
   Alternative: introduce feature flags SIM_ENGINE_V2 and TOKENS_ENFORCEMENT (default off).
3) Deploy readiness:
   - Ensure /health /ready /version endpoints are green.
4) Add a deterministic smoke script (scripts/smoke_v2.py or bash) that can run against a base URL:
   - free-tier call
   - gated endpoint without tokens -> must deny
   - gated endpoint with tokens -> must allow and decrement exactly once
   - retry same request with same idempotency key -> no double-charge
   - verify audit trail log entry exists (or endpoint/DB record)
5) Record evidence and rollback steps.
""",
    "M4_UI_PICK_V2": """
1) Implement Pick v2 UI view:
   - percentiles (p5..p95) visible
   - scenarios summary (conservative/base/aggressive)
   - uncertainty panel (volatility/data quality/confidence decay)
   - graceful degrade if backend returns partial data
2) Use /api/v2 if present; else minimal adapter.
3) No gambling-forward language. Keep educational framing.
4) Add a minimal smoke test for UI load + render.
""",
    "M5_TRICKSTER_LAB": """
1) Implement Trickster Lab scaffold:
   - modules list from static JSON
   - module detail view
2) Token unlock for deep modules using server-side enforcement.
3) Minimal progress tracking (local ok). Must not break.
4) Add basic tests (backend gating + frontend route load).
""",
    "M6_VERIFICATION_RELEASE": """
1) Run full tests suite(s) and build.
2) Run E2E path:
   UI -> /api/v2 -> token gating -> ledger -> audit trail
3) Write release notes + verification checklist + rollback plan.
4) Record evidence.
"""
}


# -----------------------------
# Evidence capture
# -----------------------------

def baseline_evidence() -> List[Evidence]:
    ev: List[Evidence] = []

    if dir_exists(REPO_ROOT / ".git"):
        _, out = sh(["git", "rev-parse", "HEAD"], check=False)
        ev.append(Evidence("git_head", "git rev-parse HEAD", out))
        _, out2 = sh(["git", "status", "--porcelain"], check=False)
        ev.append(Evidence("git_status", "git status --porcelain", out2))

    _, out3 = sh(["ls", "-la"], cwd=REPO_ROOT, check=False)
    ev.append(Evidence("repo_ls", "ls -la", out3))

    if file_exists(BACKEND_DIR / "pyproject.toml") or file_exists(REPO_ROOT / "requirements.txt"):
        _, out4 = sh([sys.executable, "-V"], check=False)
        ev.append(Evidence("python_version", f"{sys.executable} -V", out4))

    if file_exists(FRONTEND_DIR / "package.json"):
        _, out5 = sh(["node", "-v"], check=False)
        ev.append(Evidence("node_version", "node -v", out5))

    return ev


# -----------------------------
# Report rendering
# -----------------------------

def render_report(patches: List[PatchRecord]) -> str:
    lines: List[str] = []
    lines.append("# TRICKSTER v2 — M4–M6 Execution Report")
    lines.append("")
    lines.append("## Runbook")
    lines.append("```json")
    lines.append(json.dumps({
        "milestones": MILESTONES,
        "contract_v2_spec": CONTRACT_V2_SPEC,
        "deploy_gate_spec": DEPLOY_GATE_SPEC,
        "ui_m4_spec": UI_M4_SPEC,
        "lab_m5_spec": LAB_M5_SPEC
    }, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## Milestones & Evidence")
    for p in patches:
        lines.append(f"### {p.milestone}")
        lines.append("")
        lines.append(f"**Summary:** {p.summary}")
        lines.append("")
        if p.files_touched:
            lines.append("**Files touched:**")
            for f in p.files_touched:
                lines.append(f"- `{f}`")
            lines.append("")
        if p.evidence:
            lines.append("**Evidence:**")
            for e in p.evidence:
                lines.append(f"- **{e.name}**")
                lines.append("")
                lines.append("```bash")
                lines.append(e.command)
                lines.append("```")
                lines.append("```")
                lines.append(e.output.rstrip())
                lines.append("```")
            lines.append("")
        if p.risks:
            lines.append("**Risks:**")
            for r in p.risks:
                lines.append(f"- {r}")
            lines.append("")
        if p.rollback:
            lines.append("**Rollback:**")
            for rb in p.rollback:
                lines.append(f"- {rb}")
            lines.append("")
    return "\n".join(lines)


# -----------------------------
# Main
# -----------------------------

def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Write runbook JSON for Antigravity to follow
    write_text(RUNBOOK_PATH, json.dumps({
        "milestones": MILESTONES,
        "instructions": INSTRUCTIONS,
        "specs": {
            "contract_v2": CONTRACT_V2_SPEC,
            "deploy_gate": DEPLOY_GATE_SPEC,
            "ui_m4": UI_M4_SPEC,
            "lab_m5": LAB_M5_SPEC
        }
    }, indent=2))

    # Baseline record
    patches: List[PatchRecord] = [
        PatchRecord(
            milestone="BASELINE",
            summary="Captured repo baseline state before M4–M6 continuation. No changes applied by this script.",
            files_touched=[],
            evidence=baseline_evidence(),
            risks=["None (baseline only)."],
            rollback=["N/A"]
        )
    ]

    # Pre-create an empty report to be appended by Antigravity during execution.
    write_text(FINAL_REPORT, render_report(patches))

    print(f"[OK] Runbook written: {RUNBOOK_PATH}")
    print(f"[OK] Initial report created: {FINAL_REPORT}")
    print("")
    print("NEXT STEP FOR ANTIGRAVITY:")
    print("1) Execute milestones sequentially: B1 -> M4 -> M5 -> M6.")
    print("2) Use small commits; run tests after each milestone.")
    print("3) After each milestone, append PatchRecord entries and overwrite FINAL_REPORT with updated evidence.")
    print("4) Do not deploy UI changes until B1 deploy gate is green in production.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
