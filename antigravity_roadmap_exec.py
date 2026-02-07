#!/usr/bin/env python3
"""
ANTIGRAVITY EXEC PROMPT (Python)
Project: Proyecto Trickster
Goal: Execute Roadmap "Next Level" implementation plan with strict causality, evidence, and minimal-risk delivery.

NON-NEGOTIABLES
- Do not do speculative refactors.
- Work in small, verifiable commits.
- After each milestone: run deterministic checks and record evidence.
- Do not introduce gambling-forward copy or UI; keep educational/analytics framing.
- Keep changes modular; no rewriting the whole app.

OUTPUT REQUIRED (at end)
1) Executive summary
2) Changes by milestone (files, diffs overview)
3) Verification evidence (commands + outputs)
4) Risk notes + rollback steps
5) Next actions queue (prioritized)

"""

from __future__ import annotations

import os
import sys
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple


# -----------------------------
# Helpers (Antigravity Runtime)
# -----------------------------

def sh(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> Tuple[int, str]:
    """Run a command and return (code, combined_output). Deterministic output capture."""
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
    files_touched: List[str]
    summary: str
    evidence: List[Evidence]
    risks: List[str]
    rollback: List[str]


# -----------------------------
# Configuration (Adjust if needed)
# -----------------------------

REPO_ROOT = Path(os.getcwd()).resolve()

# If your repo uses a backend folder, adjust here.
# Examples:
# BACKEND_DIR = REPO_ROOT / "backend"
# FRONTEND_DIR = REPO_ROOT / "frontend"
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"

REPORTS_DIR = REPO_ROOT / "reports" / "antigravity"
PLAN_OUTPUT = REPORTS_DIR / "TRICKSTER_v2_ROADMAP_EXEC_REPORT.md"


# -----------------------------
# Milestone Plan
# -----------------------------

MILESTONES = [
    "M0_BASELINE_AUDIT",
    "M1_SIM_ENGINE_V2_DISTRIBUTIONS",
    "M2_UNCERTAINTY_LAYER_METRICS",
    "M3_TOKEN_GATING_ANALYTICS_ACCESS",
    "M4_UI_PICK_V2_SKELETON",
    "M5_TRICKSTER_LAB_MICRO_LEARNING_SCAFFOLD",
    "M6_VERIFICATION_AND_RELEASE_NOTES",
]


# -----------------------------
# Detection / Introspection
# -----------------------------

def detect_stack() -> Dict[str, str]:
    """
    Detect basic project stack without guessing too hard.
    We only record what exists.
    """
    stack = {
        "repo_root": str(REPO_ROOT),
        "has_pyproject": str(file_exists(REPO_ROOT / "backend" / "pyproject.toml")),
        "has_requirements": str(file_exists(REPO_ROOT / "backend" / "requirements.txt")),
        "has_package_json": str(file_exists(REPO_ROOT / "frontend" / "package.json")),
        "has_dockerfile": str(file_exists(REPO_ROOT / "Dockerfile")),
    }
    return stack


def baseline_checks() -> List[Evidence]:
    ev = []
    # Git status (if git repo)
    if dir_exists(REPO_ROOT / ".git"):
        _, out = sh(["git", "status", "--porcelain"], check=False)
        ev.append(Evidence("git_status_porcelain", "git status --porcelain", out))

        _, out2 = sh(["git", "rev-parse", "HEAD"], check=False)
        ev.append(Evidence("git_head", "git rev-parse HEAD", out2))

    # Basic tree snapshot (top-level)
    if sys.platform == "win32":
        _, lsout = sh(["powershell", "-Command", "Get-ChildItem | Format-Table Name, Length"], check=False)
    else:
        _, lsout = sh(["ls", "-la"], check=False)
    ev.append(Evidence("repo_ls", "ls -la", lsout))

    # If python project, run unit smoke checks safely
    if file_exists(REPO_ROOT / "backend" / "pyproject.toml") or file_exists(REPO_ROOT / "backend" / "requirements.txt"):
        _, pyver = sh([sys.executable, "-V"], check=False)
        ev.append(Evidence("python_version", f"{sys.executable} -V", pyver))

    # If node project, run node -v safely
    if file_exists(REPO_ROOT / "frontend" / "package.json"):
        _, nodever = sh(["node", "-v"], check=False)
        ev.append(Evidence("node_version", "node -v", nodever))

    return ev


# -----------------------------
# Core Implementation Guidance
# -----------------------------

SIM_ENGINE_SPEC = {
    "artifact": "distribution_object",
    "fields_required": [
        "sport",
        "event_id",
        "market",
        "model_version",
        "n_sims",
        "ci_level",
        "percentiles",     # dict: {p5,p25,p50,p75,p95}
        "mean",
        "stdev",
        "skew",            # optional if available
        "kurtosis",        # optional if available
        "scenarios",       # list of scenario results
        "notes",           # explain assumptions
    ],
    "scenario_types": ["conservative", "base", "aggressive"],
}

UNCERTAINTY_METRICS_SPEC = {
    "volatility_score": "0..100 (higher = more volatile distribution / higher variance / fat tails)",
    "data_quality_index": "0..100 (higher = better data coverage & recency; penalize missing features)",
    "confidence_decay": "0..1 per day or per time unit (higher = confidence decays faster)",
}

TOKEN_GATING_SPEC = {
    "principle": "tokens buy depth (analysis, scenarios, export), NOT 'winning picks'",
    "tiers": [
        {"feature": "headline_pick", "cost_tokens": 0},
        {"feature": "full_distribution", "cost_tokens": 2},
        {"feature": "scenario_extremes", "cost_tokens": 3},
        {"feature": "comparative_analysis", "cost_tokens": 3},
        {"feature": "deep_dive_educational", "cost_tokens": 5},
    ]
}


# -----------------------------
# Patch Strategy (Antigravity should implement)
# -----------------------------

def milestone_instructions() -> Dict[str, str]:
    """
    Natural language instructions embedded in this Python script
    so Antigravity can follow it deterministically.
    """
    return {
        "M0_BASELINE_AUDIT": """
- Confirm repo opens and runs existing tests/build (no changes).
- Identify where current simulation logic lives (search for keywords: montecarlo, simulate, simulation, odds, probabilities).
- Record baseline commands & outputs as evidence.
- DO NOT modify code in this milestone.
""",
        "M1_SIM_ENGINE_V2_DISTRIBUTIONS": f"""
- Implement Simulation Engine v2 output = distribution object, per SIM_ENGINE_SPEC:
{json.dumps(SIM_ENGINE_SPEC, indent=2)}
- Add scenario execution: conservative/base/aggressive with explicit parameter deltas (documented).
- Ensure outputs include percentiles P5/P25/P50/P75/P95 and CI level.
- Add deterministic seed option for reproducible tests.
- Add unit tests for:
  1) schema presence
  2) deterministic repeatability with seed
  3) percentiles monotonicity (p5<=p25<=p50<=p75<=p95)
- Keep changes minimal: adapt existing functions; do not rewrite architecture.
""",
        "M2_UNCERTAINTY_LAYER_METRICS": f"""
- Add uncertainty metrics:
{json.dumps(UNCERTAINTY_METRICS_SPEC, indent=2)}
- These metrics must be computed from distribution + data availability signals.
- Add tests that:
  - volatility_score increases when variance increases (synthetic distributions)
  - data_quality_index decreases when key features missing
  - confidence_decay increases with older data timestamp
""",
        "M3_TOKEN_GATING_ANALYTICS_ACCESS": f"""
- Implement token gating at API/service layer:
{json.dumps(TOKEN_GATING_SPEC, indent=2)}
- Headline remains free; deeper analysis endpoints require tokens.
- Add clear server-side enforcement (no client-only gating).
- Implement token ledger transactions with audit logs:
  - who, what feature, cost, timestamp, event_id
- Add tests for:
  - deny when insufficient tokens
  - allow and decrement when sufficient
  - idempotency protection (avoid double charge on retries)
""",
        "M4_UI_PICK_V2_SKELETON": """
- Implement UI skeleton for "Pick v2":
  - show distribution chart placeholder + percentiles table
  - show risk zones wording (educational)
  - no gambling-forward copy
- Only wire to existing endpoints; if backend missing fields, render gracefully.
- Add simple Cypress/Playwright smoke (if stack supports) or minimal DOM checks.
""",
        "M5_TRICKSTER_LAB_MICRO_LEARNING_SCAFFOLD": """
- Create "Trickster Lab" scaffolding:
  - modules list (static JSON first)
  - module detail page
  - token-unlock for deep modules (reuse token gating)
- Keep content minimal but non-empty: at least 4 modules with short explanations.
""",
        "M6_VERIFICATION_AND_RELEASE_NOTES": """
- Run full test suite and build.
- Produce release notes: what changed, how to verify, rollback steps.
- Ensure no policy-unsafe language in UI/copy.
""",
    }


# -----------------------------
# Report Builder
# -----------------------------

def render_report(stack: Dict[str, str], patches: List[PatchRecord]) -> str:
    lines = []
    lines.append("# TRICKSTER v2 ROADMAP EXECUTION REPORT")
    lines.append("")
    lines.append("## Stack Detection")
    lines.append("```json")
    lines.append(json.dumps(stack, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## Milestones")
    for p in patches:
        lines.append(f"### {p.milestone}")
        lines.append("")
        lines.append(f"**Summary:** {p.summary}")
        lines.append("")
        lines.append("**Files touched:**")
        for f in p.files_touched:
            lines.append(f"- `{f}`")
        lines.append("")
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
    lines.append("## Next Actions Queue (Prioritized)")
    lines.append("- If any milestone fails verification, rollback to last green commit and re-run.")
    lines.append("- Harden token ledger with rate limiting and replay-protection if not already present.")
    lines.append("- Add analytics instrumentation (privacy-preserving) for retention and token spend.")
    lines.append("")
    return "\n".join(lines)


# -----------------------------
# Main (Antigravity should execute)
# -----------------------------

def main() -> int:
    instr = milestone_instructions()
    stack = detect_stack()

    # Create reports dir early
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Baseline evidence
    baseline_ev = baseline_checks()
    patches: List[PatchRecord] = [
        PatchRecord(
            milestone="M0_BASELINE_AUDIT",
            files_touched=[],
            summary="Baseline repository audit and evidence capture. No code changes.",
            evidence=baseline_ev,
            risks=["None (no changes)."],
            rollback=["N/A"],
        )
    ]

    # Write plan file (instructions) so Antigravity can follow step-by-step.
    plan_path = REPORTS_DIR / "TRICKSTER_v2_PLAN.json"
    write_text(plan_path, json.dumps({
        "milestones": MILESTONES,
        "instructions": instr,
        "specs": {
            "sim_engine": SIM_ENGINE_SPEC,
            "uncertainty_metrics": UNCERTAINTY_METRICS_SPEC,
            "token_gating": TOKEN_GATING_SPEC,
        }
    }, indent=2))

    # NOTE:
    # Antigravity should now:
    # 1) Implement each milestone sequentially in separate commits
    # 2) Append PatchRecord entries after each milestone with evidence
    # 3) Save final report to PLAN_OUTPUT
    #
    # This script provides the deterministic structure and spec.
    # Actual patching is performed by Antigravity agent, not by this script.

    # Pre-fill a "work instructions" markdown for convenience.
    write_text(
        REPORTS_DIR / "WORK_INSTRUCTIONS.md",
        "# Antigravity Work Instructions (Trickster v2)\n\n"
        "Follow the milestone instructions in TRICKSTER_v2_PLAN.json.\n\n"
        "Rules:\n"
        "- PARSE/TEST failures first.\n"
        "- Small commits per milestone.\n"
        "- Record evidence after each step.\n"
        "- No gambling-forward copy.\n"
    )

    # Render initial report (baseline only for now).
    report = render_report(stack, patches)
    write_text(PLAN_OUTPUT, report)

    print(f"[OK] Plan written: {plan_path}")
    print(f"[OK] Work instructions: {REPORTS_DIR / 'WORK_INSTRUCTIONS.md'}")
    print(f"[OK] Baseline report: {PLAN_OUTPUT}")
    print("\nNEXT STEP FOR ANTIGRAVITY:")
    print("- Open TRICKSTER_v2_PLAN.json and execute milestones M1..M6 sequentially with evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
