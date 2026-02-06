#!/usr/bin/env python3
"""
PROTOCOLO SEMÁFORO — TRICKSTER-ORACLE Production Readiness Audit

Sistema de auditoría con 3 estados:
🟢 VERDE: All OK, ready to proceed
🟡 AMARILLO: Warning, review but not blocking
🔴 ROJO: Critical, must fix before deployment

Usage:
    python tools/protocolo_semaforo.py --repo "c:/Users/USUARIO/.gemini/antigravity/playground/TRIKSTER-ORACLE"

Output:
    docs/SEMAFORO_AUDIT_REPORT_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional


@dataclass
class SemaforoCheck:
    """Represents a single audit check with traffic light status"""
    category: str
    name: str
    status: str  # "🟢", "🟡", "🔴"
    message: str
    evidence: str = ""
    blocking: bool = False


def run_cmd(cmd: List[str], cwd: Path, timeout: int = 30) -> Tuple[int, str, str]:
    """Execute command and return (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, 
            timeout=timeout, shell=False
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", f"Command timeout after {timeout}s"
    except Exception as e:
        return 1, "", str(e)


def check_git_status(repo: Path) -> List[SemaforoCheck]:
    """Audit: Git repository status"""
    checks = []
    
    # Check if it's a git repo
    if not (repo / ".git").exists():
        checks.append(SemaforoCheck(
            category="GIT",
            name="Repository Identity",
            status="🔴",
            message="Not a git repository",
            blocking=True
        ))
        return checks
    
    # Check remote
    rc, out, err = run_cmd(["git", "remote", "-v"], cwd=repo)
    if rc != 0 or "TRIKSTER-ORACLE" not in out:
        checks.append(SemaforoCheck(
            category="GIT",
            name="Remote Verification",
            status="🔴",
            message="Git remote not configured correctly",
            evidence=out or err,
            blocking=True
        ))
    else:
        checks.append(SemaforoCheck(
            category="GIT",
            name="Remote Verification",
            status="🟢",
            message="Remote correctly configured",
            evidence=out.split('\n')[0]
        ))
    
    # Check branch
    rc, branch, _ = run_cmd(["git", "branch", "--show-current"], cwd=repo)
    if branch != "master":
        checks.append(SemaforoCheck(
            category="GIT",
            name="Branch Status",
            status="🟡",
            message=f"On branch '{branch}', expected 'master'",
            evidence=branch
        ))
    else:
        checks.append(SemaforoCheck(
            category="GIT",
            name="Branch Status",
            status="🟢",
            message="On master branch",
            evidence=branch
        ))
    
    # Check uncommitted changes
    rc, status_out, _ = run_cmd(["git", "status", "--porcelain"], cwd=repo)
    if status_out:
        checks.append(SemaforoCheck(
            category="GIT",
            name="Working Directory",
            status="🟡",
            message="Uncommitted changes detected",
            evidence=status_out[:200]
        ))
    else:
        checks.append(SemaforoCheck(
            category="GIT",
            name="Working Directory",
            status="🟢",
            message="Working directory clean"
        ))
    
    # Check last commit
    rc, last_commit, _ = run_cmd(["git", "log", "-1", "--oneline"], cwd=repo)
    if rc == 0:
        checks.append(SemaforoCheck(
            category="GIT",
            name="Last Commit",
            status="🟢",
            message="Recent commit found",
            evidence=last_commit
        ))
    
    return checks


def check_maturation_a1(repo: Path) -> List[SemaforoCheck]:
    """Audit: A1 - Request-ID Middleware + Logging"""
    checks = []
    backend = repo / "backend"
    
    # Check request_id middleware exists
    request_id_file = backend / "app" / "middleware" / "request_id.py"
    if not request_id_file.exists():
        checks.append(SemaforoCheck(
            category="MATURATION_A1",
            name="Request-ID Middleware",
            status="🔴",
            message="request_id.py not found",
            blocking=True
        ))
        return checks
    
    # Verify X-Request-ID implementation
    content = request_id_file.read_text(encoding="utf-8", errors="ignore")
    if "X-Request-ID" in content and "uuid" in content.lower():
        checks.append(SemaforoCheck(
            category="MATURATION_A1",
            name="Request-ID Middleware",
            status="🟢",
            message="Request-ID middleware properly implemented",
            evidence=f"File: {request_id_file.name}"
        ))
    else:
        checks.append(SemaforoCheck(
            category="MATURATION_A1",
            name="Request-ID Middleware",
            status="🟡",
            message="request_id.py exists but implementation unclear"
        ))
    
    # Check logging.py
    logging_file = backend / "app" / "logging.py"
    if not logging_file.exists():
        checks.append(SemaforoCheck(
            category="MATURATION_A1",
            name="Structured Logging",
            status="🔴",
            message="logging.py not found",
            blocking=True
        ))
    else:
        log_content = logging_file.read_text(encoding="utf-8", errors="ignore")
        if "json" in log_content.lower() and "JSONFormatter" in log_content:
            checks.append(SemaforoCheck(
                category="MATURATION_A1",
                name="Structured Logging",
                status="🟢",
                message="JSON logging configured",
                evidence=f"File: {logging_file.name}"
            ))
        else:
            checks.append(SemaforoCheck(
                category="MATURATION_A1",
                name="Structured Logging",
                status="🟡",
                message="logging.py found but JSON formatting unclear"
            ))
    
    return checks


def check_maturation_a2(repo: Path) -> List[SemaforoCheck]:
    """Audit: A2 - System Routes"""
    checks = []
    backend = repo / "backend"
    
    # Check system.py exists
    system_file = backend / "app" / "api" / "system.py"
    if not system_file.exists():
        checks.append(SemaforoCheck(
            category="MATURATION_A2",
            name="System Routes File",
            status="🔴",
            message="system.py not found",
            blocking=True
        ))
        return checks
    
    content = system_file.read_text(encoding="utf-8", errors="ignore")
    
    # Check each route
    routes = {
        "/health": "Health check endpoint",
        "/ready": "Readiness check endpoint",
        "/version": "Version endpoint"
    }
    
    for route, desc in routes.items():
        if route in content:
            checks.append(SemaforoCheck(
                category="MATURATION_A2",
                name=f"Route {route}",
                status="🟢",
                message=f"{desc} implemented"
            ))
        else:
            checks.append(SemaforoCheck(
                category="MATURATION_A2",
                name=f"Route {route}",
                status="🔴",
                message=f"{desc} missing",
                blocking=True
            ))
    
    # Check BUILD_COMMIT reference
    if "BUILD_COMMIT" in content:
        checks.append(SemaforoCheck(
            category="MATURATION_A2",
            name="Build Tracking",
            status="🟢",
            message="BUILD_COMMIT tracking configured"
        ))
    else:
        checks.append(SemaforoCheck(
            category="MATURATION_A2",
            name="Build Tracking",
            status="🟡",
            message="BUILD_COMMIT not referenced in /version"
        ))
    
    return checks


def check_deployment_e1(repo: Path) -> List[SemaforoCheck]:
    """Audit: E1 - Deployment Readiness"""
    checks = []
    
    # Check render.yaml
    if (repo / "render.yaml").exists():
        checks.append(SemaforoCheck(
            category="DEPLOYMENT_E1",
            name="Render Blueprint",
            status="🟢",
            message="render.yaml present"
        ))
    else:
        checks.append(SemaforoCheck(
            category="DEPLOYMENT_E1",
            name="Render Blueprint",
            status="🔴",
            message="render.yaml missing",
            blocking=True
        ))
    
    # Check .env.example
    if (repo / "backend" / ".env.example").exists():
        checks.append(SemaforoCheck(
            category="DEPLOYMENT_E1",
            name="Environment Template",
            status="🟢",
            message=".env.example present"
        ))
    else:
        checks.append(SemaforoCheck(
            category="DEPLOYMENT_E1",
            name="Environment Template",
            status="🟡",
            message=".env.example missing"
        ))
    
    # Check deployment docs
    deploy_docs = [
        "docs/DEPLOY_RENDER_HOSTINGER.md",
        "docs/DEPLOY_CHECKLIST.md"
    ]
    for doc in deploy_docs:
        if (repo / doc).exists():
            checks.append(SemaforoCheck(
                category="DEPLOYMENT_E1",
                name=f"Doc: {Path(doc).name}",
                status="🟢",
                message=f"Deployment doc present"
            ))
        else:
            checks.append(SemaforoCheck(
                category="DEPLOYMENT_E1",
                name=f"Doc: {Path(doc).name}",
                status="🔴",
                message=f"Deployment doc missing",
                blocking=True
            ))
    
    return checks


def check_security(repo: Path) -> List[SemaforoCheck]:
    """Audit: Security - No secrets, CORS config"""
    checks = []
    
    # Check for common secret patterns (basic scan)
    dangerous_patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
        (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
        (r'secret\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded secret"),
    ]
    
    secrets_found = False
    for py_file in (repo / "backend").rglob("*.py"):
        if ".venv" in str(py_file) or "node_modules" in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for pattern, desc in dangerous_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    secrets_found = True
                    checks.append(SemaforoCheck(
                        category="SECURITY",
                        name="Secret Detection",
                        status="🔴",
                        message=f"{desc} detected in {py_file.name}",
                        blocking=True
                    ))
                    break
        except Exception:
            continue
    
    if not secrets_found:
        checks.append(SemaforoCheck(
            category="SECURITY",
            name="Secret Detection",
            status="🟢",
            message="No hardcoded secrets detected"
        ))
    
    # Check CORS configuration
    main_file = repo / "backend" / "app" / "main.py"
    if main_file.exists():
        content = main_file.read_text(encoding="utf-8", errors="ignore")
        if 'allow_origins=["*"]' in content or "allow_origins=[\"*\"]" in content:
            checks.append(SemaforoCheck(
                category="SECURITY",
                name="CORS Configuration",
                status="🟡",
                message="CORS allows all origins (wildcard) - OK for dev, change for prod"
            ))
        else:
            checks.append(SemaforoCheck(
                category="SECURITY",
                name="CORS Configuration",
                status="🟢",
                message="CORS configured (check allowlist in production)"
            ))
    
    return checks


def check_performance(repo: Path) -> List[SemaforoCheck]:
    """Audit: Performance - Lazy loading"""
    checks = []
    
    # Check lazy loading in App.tsx
    app_files = list((repo / "frontend").rglob("App.tsx"))
    if not app_files:
        checks.append(SemaforoCheck(
            category="PERFORMANCE",
            name="Frontend Optimization",
            status="🟡",
            message="App.tsx not found, cannot verify lazy loading"
        ))
        return checks
    
    app_file = app_files[0]
    content = app_file.read_text(encoding="utf-8", errors="ignore")
    
    if "lazy" in content and "Suspense" in content:
        checks.append(SemaforoCheck(
            category="PERFORMANCE",
            name="Lazy Loading",
            status="🟢",
            message="React lazy loading implemented"
        ))
    else:
        checks.append(SemaforoCheck(
            category="PERFORMANCE",
            name="Lazy Loading",
            status="🟡",
            message="Lazy loading not detected - consider implementing"
        ))
    
    return checks


def check_documentation(repo: Path) -> List[SemaforoCheck]:
    """Audit: Documentation completeness"""
    checks = []
    
    required_docs = {
        "README.md": "Project README",
        "docs/ANTIGRAVITY_MATURATION_PHASE5_PHASE6.md": "Maturation work order",
        "DEPLOYMENT_PLAN_SUMMARY.md": "Deployment plan",
    }
    
    for doc_path, desc in required_docs.items():
        if (repo / doc_path).exists():
            checks.append(SemaforoCheck(
                category="DOCUMENTATION",
                name=desc,
                status="🟢",
                message=f"{doc_path} present"
            ))
        else:
            checks.append(SemaforoCheck(
                category="DOCUMENTATION",
                name=desc,
                status="🟡",
                message=f"{doc_path} missing"
            ))
    
    return checks


def generate_report(checks: List[SemaforoCheck], repo: Path) -> str:
    """Generate markdown report from checks"""
    
    # Count by status
    green = sum(1 for c in checks if c.status == "🟢")
    yellow = sum(1 for c in checks if c.status == "🟡")
    red = sum(1 for c in checks if c.status == "🔴")
    total = len(checks)
    
    # Determine overall status
    if red > 0:
        overall = "🔴 STOP - Critical issues must be fixed"
    elif yellow > 3:
        overall = "🟡 CAUTION - Review warnings before proceeding"
    else:
        overall = "🟢 GO - Ready for deployment"
    
    # Group checks by category
    categories = {}
    for check in checks:
        if check.category not in categories:
            categories[check.category] = []
        categories[check.category].append(check)
    
    # Build report
    lines = [
        "# 🚦 PROTOCOLO SEMÁFORO — Production Readiness Audit",
        "",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Repository**: {repo.name}",
        "",
        "## Overall Status",
        "",
        f"### {overall}",
        "",
        f"- 🟢 Green: {green}/{total}",
        f"- 🟡 Yellow: {yellow}/{total}",
        f"- 🔴 Red: {red}/{total}",
        "",
        "---",
        "",
        "## Audit Results by Category",
        ""
    ]
    
    for category, cat_checks in categories.items():
        lines.append(f"### {category}")
        lines.append("")
        
        for check in cat_checks:
            blocking_marker = " **[BLOCKING]**" if check.blocking else ""
            lines.append(f"#### {check.status} {check.name}{blocking_marker}")
            lines.append(f"**Status**: {check.message}")
            if check.evidence:
                lines.append(f"**Evidence**: `{check.evidence[:150]}`")
            lines.append("")
    
    lines.extend([
        "---",
        "",
        "## Legend",
        "",
        "- 🟢 **GREEN**: All OK, ready to proceed",
        "- 🟡 **YELLOW**: Warning, review but not blocking",
        "- 🔴 **RED**: Critical, must fix before deployment",
        "",
        "## Next Steps",
        ""
    ])
    
    if red > 0:
        lines.append("1. **STOP**: Fix all 🔴 red issues")
        lines.append("2. Re-run audit: `python tools/protocolo_semaforo.py`")
        lines.append("3. Only proceed when all critical issues resolved")
    elif yellow > 0:
        lines.append("1. **REVIEW**: Examine all 🟡 yellow warnings")
        lines.append("2. Document any accepted risks")
        lines.append("3. Proceed with deployment if warnings acceptable")
    else:
        lines.append("1. **GO**: All checks passed!")
        lines.append("2. Proceed with deployment")
        lines.append("3. Follow deployment checklist")
    
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="PROTOCOLO SEMÁFORO - Production Readiness Audit")
    ap.add_argument("--repo", required=True, help="Path to repository")
    args = ap.parse_args()
    
    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"[ERROR] Repository not found: {repo}")
        return 2
    
    print("[*] Running PROTOCOLO SEMÁFORO audit...")
    print(f"[*] Repository: {repo}")
    print()
    
    all_checks: List[SemaforoCheck] = []
    
    # Run all audits
    print("[*] Auditing Git status...")
    all_checks.extend(check_git_status(repo))
    
    print("[*] Auditing Maturation A1 (Request-ID + Logging)...")
    all_checks.extend(check_maturation_a1(repo))
    
    print("[*] Auditing Maturation A2 (System Routes)...")
    all_checks.extend(check_maturation_a2(repo))
    
    print("[*] Auditing Deployment E1 (Deploy Readiness)...")
    all_checks.extend(check_deployment_e1(repo))
    
    print("[*] Auditing Security...")
    all_checks.extend(check_security(repo))
    
    print("[*] Auditing Performance...")
    all_checks.extend(check_performance(repo))
    
    print("[*] Auditing Documentation...")
    all_checks.extend(check_documentation(repo))
    
    # Generate report
    report = generate_report(all_checks, repo)
    
    # Write report
    report_path = repo / "docs" / f"SEMAFORO_AUDIT_REPORT_{datetime.now().strftime('%Y-%m-%d')}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    
    # Print summary
    print()
    print("=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)
    
    green = sum(1 for c in all_checks if c.status == "🟢")
    yellow = sum(1 for c in all_checks if c.status == "🟡")
    red = sum(1 for c in all_checks if c.status == "🔴")
    
    print(f"[GREEN] Passed: {green}")
    print(f"[YELLOW] Warnings: {yellow}")
    print(f"[RED] Critical: {red}")
    print()
    
    if red > 0:
        print("[STOP] OVERALL: RED - Fix critical issues")
        print(f"Report: {report_path}")
        return 1
    elif yellow > 3:
        print("[CAUTION] OVERALL: YELLOW - Review warnings")
        print(f"Report: {report_path}")
        return 0
    else:
        print("[GO] OVERALL: GREEN - Ready for deployment")
        print(f"Report: {report_path}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
