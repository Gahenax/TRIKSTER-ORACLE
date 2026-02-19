from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(os.getenv("REPO_ROOT", ".")).resolve()
DEPLOY_DIR = REPO_ROOT / "deploy"
ENV_FILE = DEPLOY_DIR / ".env"
ENV_TEMPLATE = DEPLOY_DIR / "PROD_ENV.template"
COMPOSE_FILE = DEPLOY_DIR / "docker-compose.viewer.yml"
GATE_SCRIPT = REPO_ROOT / "_antigravity_out" / "go_live_gate.py"

BASE_URL = os.getenv("VIEWER_BASE_URL", "")
API_KEY = os.getenv("VIEWER_API_KEY", "")


def must(cond: bool, msg: str) -> None:
    if not cond:
        raise RuntimeError(msg)


def run(cmd: str, check: bool = True) -> None:
    print(f"> {cmd}")
    # Using shell=True and handle potential Windows/Linux differences for 'grep' if needed,
    # but strictly following the prompt's provided code which uses shell patterns.
    p = subprocess.run(cmd, shell=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {cmd}")


def main() -> int:
    print("ANTIGRAVITY | Production Deployment Executor")
    print(f"Repo root: {REPO_ROOT}")

    # 1) Preconditions
    must(COMPOSE_FILE.exists(), f"Missing compose file: {COMPOSE_FILE}")
    must(GATE_SCRIPT.exists(), f"Missing gate script: {GATE_SCRIPT}")
    must(ENV_TEMPLATE.exists(), f"Missing env template: {ENV_TEMPLATE}")

    if not ENV_FILE.exists():
        print("deploy/.env not found. Creating from template...")
        ENV_FILE.write_text(ENV_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
        print("WARNING: Fill deploy/.env before re-running.")
        return 1

    must(BASE_URL != "", "VIEWER_BASE_URL must be set (e.g. https://viewer.example.com)")
    must(API_KEY != "", "VIEWER_API_KEY must be set (production secret required)")

    print(f"Target URL: {BASE_URL}")

    # 2) Build & start container
    run(f"docker compose -f {COMPOSE_FILE} --env-file {ENV_FILE} up -d --build")

    # 3) Wait for container to stabilize
    print("Waiting for container startup...")
    time.sleep(3)

    # For cross-platform support in the script itself, though usually run on Linux prod:
    grep_cmd = "findstr" if os.name == "nt" else "grep"
    run(f"docker ps | {grep_cmd} web-viewer", check=True)

    # 4) Run post-deploy gate
    env = os.environ.copy()
    env["VIEWER_BASE_URL"] = BASE_URL
    env["VIEWER_API_KEY"] = API_KEY

    print("Running post-deploy Go-Live Gate...")
    p = subprocess.run(
        f"python {GATE_SCRIPT}",
        shell=True,
        env=env,
    )

    if p.returncode != 0:
        print("FAIL: Go-Live Gate failed. Rolling back container.")
        run(f"docker compose -f {COMPOSE_FILE} --env-file {ENV_FILE} down", check=False)
        return 1

    print("SUCCESS: Production deployment validated.")
    print("You may now open traffic safely.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"FATAL: {e}")
        sys.exit(1)
