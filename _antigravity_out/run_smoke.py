import os
import sys
import subprocess

def run(cmd: str) -> int:
    print(f"> {cmd}")
    return subprocess.call(cmd, shell=True)

def main() -> int:
    # Minimal automated gate: tests only.
    # Full smoke involves starting the server and curl calls, which is environment-specific.
    code = 0
    # Add project root to PYTHONPATH so viewer can find app.py if needed, 
    # but here viewer/ is a package usually or just a flat dir.
    os.environ["PYTHONPATH"] = os.environ.get("PYTHONPATH", "") + os.pathsep + os.getcwd() + "/viewer"
    code |= run("pytest -q viewer/tests")
    if code != 0:
        print("SMOKE FAILED: unit tests")
        return 1
    print("SMOKE OK: unit tests passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
