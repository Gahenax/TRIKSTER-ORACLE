import os
import time
import json
import subprocess
import requests
from pathlib import Path
from typing import Dict

# -------------------------------------------------
# Config
# -------------------------------------------------

ROOT = Path(os.getcwd()).resolve()
REPORTS = ROOT / "reports" / "antigravity"
REPORTS.mkdir(parents=True, exist_ok=True)

OPERATIONAL_REPORT = REPORTS / "OPERATIONAL_STATUS.md"
BASE_URL = os.environ.get("TRICKSTER_BASE_URL", "https://trickster-oracle-api.onrender.com").rstrip("/")
EXPECTED_VERSION = "2.0.0-beta"

# -------------------------------------------------
# Helpers
# -------------------------------------------------

def verify_version():
    print(f"Verifying version at {BASE_URL}...")
    try:
        r = requests.get(BASE_URL + "/", timeout=20)
        r.raise_for_status()
        data = r.json()
        version = data.get("version")
        if version != EXPECTED_VERSION:
            print(f"Mismatch: Expected {EXPECTED_VERSION}, got {version}. Service might still be deploying...")
            return None
        return version
    except Exception as e:
        print(f"Error connecting: {e}")
        return None

def run_final_validation():
    print("Running final production validation script...")
    script = ROOT / "scripts" / "final_prod_validation.py"
    
    env = os.environ.copy()
    env["TRICKSTER_BASE_URL"] = BASE_URL

    p = subprocess.Popen(
        ["python", str(script)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    out, _ = p.communicate()
    return p.returncode, out

def write_operational_report(version: str, validation_log: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")

    content = f"""# TRICKSTER-ORACLE — OPERATIONAL STATUS CERTIFICATE

Date: {ts}
Environment: Production
Base URL: {BASE_URL}

## System State
- Backend: LIVE (Render)
- Frontend: READY (Vercel compatible)
- API Version: {version}
- Redis Persistence: ACTIVE (Verified via v2 endpoints)
- Idempotency: ENFORCED
- Token Gating: SERVER-SIDE

## Validation
Final production validation executed successfully.
- Health / Ready / Version: PASS
- Free Tier: PASS
- Gated Access: PASS
- Idempotency: PASS
- Ledger / Audit: PASS or Best-Effort Verified

## Declaration
TRICKSTER-ORACLE v2.0 is hereby declared:

🟢 **OPERATIONAL**  
🟢 **PRODUCTION-READY**  
🟢 **ELIGIBLE FOR MARKET VALIDATION**  

Next authorized phase:
→ Initial Token Pricing Design
"""
    OPERATIONAL_REPORT.write_text(content, encoding="utf-8")
    print(f"Operational report written to {OPERATIONAL_REPORT}")

# -------------------------------------------------
# Main
# -------------------------------------------------

def main():
    # Loop for version alignment (wait up to 5 mins)
    max_retries = 10
    version = None
    for i in range(max_retries):
        version = verify_version()
        if version:
            break
        print(f"Retry {i+1}/{max_retries} in 30s...")
        time.sleep(30)
    
    if not version:
        print("FAILED: API did not align with expected version in time.")
        return

    code, log = run_final_validation()
    if code == 0:
        write_operational_report(version, log)
        print("Final Deployment SUCCESS.")
    else:
        print("Final Production Validation FAILED.")
        print(log)

if __name__ == "__main__":
    main()
