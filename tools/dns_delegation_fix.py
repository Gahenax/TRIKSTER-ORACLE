#!/usr/bin/env python3
"""
ANTIGRAVITY — DNS Delegation Fix Roadmap Executor (Evidence + Instructions)

Project: TRICKSTER-ORACLE
Goal:
- Diagnose authoritative DNS delegation for gahenaxaisolutions.com
- Confirm why trickster-api.gahenaxaisolutions.com returns NXDOMAIN
- Generate exact step-by-step fix instructions (Cloudflare/Hostinger/dns-parking paths)
- Produce deterministic evidence and retest commands
- Optional: update project docs and frontend config guidance (NO DNS changes performed automatically)

NON-NEGOTIABLE RULES
1) Do NOT attempt to log into panels or change DNS automatically.
2) Use only deterministic CLI DNS queries (dig/nslookup) and record evidence.
3) Output a single actionable plan with the minimal changes required.
4) If required tools are missing (dig/nslookup), stop and report what to install.
5) Never modify unrelated modules. Only create docs under docs/dns/ and optional helper scripts under backend/tools/.

OUTPUTS
- docs/dns/DNS_ROOTCAUSE_REPORT.md
- docs/dns/DNS_FIX_ROADMAP.md
- docs/dns/DNS_RETEST_COMMANDS.md
- Optional helper: backend/tools/dns_verify.py (runs dig/nslookup checks)

CONFIG (edit if needed)
- DOMAIN = "gahenaxaisolutions.com"
- SUBDOMAIN = "trickster-api"
- EXPECTED_CNAME_TARGET = "trickster-oracle-api.onrender.com"

"""

import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

DOMAIN = "gahenaxaisolutions.com"
SUBDOMAIN = "trickster-api"
FQDN = f"{SUBDOMAIN}.{DOMAIN}"
EXPECTED_CNAME_TARGET = "trickster-oracle-api.onrender.com"

OUT_DIR = Path("docs/dns")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def now():
    return {
        "utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z"),
        "local": datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    }

def run(cmd: str) -> str:
    p = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.strip()

def have(bin_name: str) -> bool:
    return shutil.which(bin_name) is not None

def codeblock(s: str) -> str:
    return f"```text\n{s}\n```\n"

def extract_ns(text: str):
    ns = set()
    for line in text.splitlines():
        line = line.strip()
        m = re.search(r"\sNS\s+([a-zA-Z0-9._-]+)\.?", line)
        if m:
            ns.add(m.group(1).rstrip("."))
        m2 = re.search(r"nameserver\s*=\s*([a-zA-Z0-9._-]+)\.?", line, re.I)
        if m2:
            ns.add(m2.group(1).rstrip("."))
    return sorted(ns)

def write(path: Path, content: str):
    path.write_text(content, encoding="utf-8")

def main():
    if not have("dig") and not have("nslookup"):
        msg = (
            "# DNS Tooling Missing\n\n"
            "Neither 'dig' nor 'nslookup' is available on this machine.\n\n"
            "Install one of:\n"
            "- Windows: install BIND tools or use WSL\n"
            "- macOS: dig is usually present\n"
            "- Linux: sudo apt-get install dnsutils\n"
        )
        write(OUT_DIR / "DNS_ROOTCAUSE_REPORT.md", msg)
        print("ERROR: missing dig/nslookup. Wrote docs/dns/DNS_ROOTCAUSE_REPORT.md")
        return

    stamp = now()
    checks = []
    checks.append(f"Time (UTC): {stamp['utc']}")
    checks.append(f"Time (Local): {stamp['local']}")
    checks.append(f"Domain: {DOMAIN}")
    checks.append(f"FQDN: {FQDN}")
    checks.append(f"Expected CNAME target: {EXPECTED_CNAME_TARGET}")

    # Delegated NS (recursive)
    ns_8888 = run(f"nslookup -type=NS {DOMAIN} 8.8.8.8") if have("nslookup") else ""
    dig_ns_8888 = run(f"dig NS {DOMAIN} @8.8.8.8 +noall +answer +authority +additional") if have("dig") else ""
    delegated = extract_ns(ns_8888 + "\n" + dig_ns_8888)

    # Recursive checks for FQDN
    rec_8888 = run(f"nslookup -type=CNAME {FQDN} 8.8.8.8") if have("nslookup") else ""
    rec_1111 = run(f"nslookup -type=CNAME {FQDN} 1.1.1.1") if have("nslookup") else ""
    dig_rec_8888 = run(f"dig {FQDN} CNAME @8.8.8.8 +noall +answer +comments") if have("dig") else ""
    dig_rec_1111 = run(f"dig {FQDN} CNAME @1.1.1.1 +noall +answer +comments") if have("dig") else ""

    # Trace to authoritative
    trace = run(f"dig {FQDN} CNAME +trace") if have("dig") else ""

    # Direct authoritative queries (use first delegated NS if present)
    auth_section = ""
    auth_ns = delegated[0] if delegated else ""
    auth_cname = auth_a = auth_aaaa = auth_status = ""
    if auth_ns and have("dig"):
        auth_cname = run(f"dig @{auth_ns} {FQDN} CNAME +noall +answer +comments")
        auth_a = run(f"dig @{auth_ns} {FQDN} A +noall +answer +comments")
        auth_aaaa = run(f"dig @{auth_ns} {FQDN} AAAA +noall +answer +comments")
        auth_status = run(f"dig @{auth_ns} {FQDN} CNAME +noall +comments")
        auth_section = (
            f"Authoritative NS (first from delegation): {auth_ns}\n\n"
            "## @authoritative CNAME\n" + codeblock(auth_cname) +
            "## @authoritative A\n" + codeblock(auth_a) +
            "## @authoritative AAAA\n" + codeblock(auth_aaaa) +
            "## @authoritative status/comments\n" + codeblock(auth_status)
        )

    # Classify root cause
    blob = "\n".join([rec_8888, rec_1111, dig_rec_8888, dig_rec_1111, trace, auth_cname, auth_a, auth_aaaa, auth_status]).lower()
    nxdomain = "nxdomain" in blob
    cname_present = (" cname " in (auth_cname.lower() if auth_cname else "")) or (" in cname " in (auth_cname.lower() if auth_cname else ""))
    a_present = (" in a " in (auth_a.lower() if auth_a else "")) or ("\ta\t" in (auth_a.lower() if auth_a else ""))
    aaaa_present = (" in aaaa " in (auth_aaaa.lower() if auth_aaaa else "")) or ("\taaaa\t" in (auth_aaaa.lower() if auth_aaaa else ""))

    if delegated and any("dns-parking" in ns.lower() for ns in delegated) and nxdomain:
        classification = "Nameservers delegated to dns-parking.com and subdomain record not present there (NXDOMAIN)."
        likely_fix = "Create the CNAME in the actual authoritative DNS panel (dns-parking), or change delegation to Cloudflare/Hostinger and create it there."
    elif nxdomain and not cname_present and not a_present and not aaaa_present:
        classification = "FQDN NXDOMAIN at authoritative level: record missing or not published in authoritative zone."
        likely_fix = "Create CNAME trickster-api -> trickster-oracle-api.onrender.com in the authoritative DNS provider."
    elif (a_present or aaaa_present) and not cname_present:
        classification = "Record conflict: A/AAAA exists where CNAME is expected."
        likely_fix = "Remove A/AAAA for trickster-api and keep only CNAME."
    elif cname_present and EXPECTED_CNAME_TARGET.lower() not in (auth_cname.lower() if auth_cname else ""):
        classification = "CNAME exists but points to an unexpected target (typo/malformed)."
        likely_fix = f"Fix CNAME target to: {EXPECTED_CNAME_TARGET} (no https://)."
    else:
        classification = "Inconclusive from current outputs. Need full authoritative trace or additional NS checks."
        likely_fix = "Re-run trace and direct authoritative queries for each delegated NS."

    # Reports
    rootcause = (
        "# DNS Root Cause Report\n\n"
        + "\n".join(f"- {x}" for x in checks) + "\n\n"
        "## Delegated Nameservers (via 8.8.8.8)\n"
        + codeblock(ns_8888 or "(nslookup not available)") +
        codeblock(dig_ns_8888 or "(dig not available)") +
        f"Extracted NS: {', '.join(delegated) if delegated else '(none parsed)'}\n\n"
        "## Recursive checks\n"
        "### nslookup CNAME (8.8.8.8)\n" + codeblock(rec_8888 or "(nslookup not available)") +
        "### nslookup CNAME (1.1.1.1)\n" + codeblock(rec_1111 or "(nslookup not available)") +
        "### dig CNAME (8.8.8.8)\n" + codeblock(dig_rec_8888 or "(dig not available)") +
        "### dig CNAME (1.1.1.1)\n" + codeblock(dig_rec_1111 or "(dig not available)") +
        "## Trace (+trace)\n" + codeblock(trace or "(dig not available)") +
        (("\n" + auth_section) if auth_section else "\n(No direct authoritative query executed)\n") +
        "\n## Classification\n"
        f"- Root cause: {classification}\n"
        f"- Minimal fix: {likely_fix}\n"
    )
    write(OUT_DIR / "DNS_ROOTCAUSE_REPORT.md", rootcause)

    # Roadmap (actionable)
    roadmap = (
        "# DNS Fix Roadmap (Minimal)\n\n"
        "## Plan A (Immediate): Keep using Render URL\n"
        f"- API base: https://{EXPECTED_CNAME_TARGET}\n"
        "- No DNS changes required.\n\n"
        "## Plan B (Correct fix): Make the subdomain exist in authoritative DNS\n"
        "### Step 1: Identify authoritative DNS provider\n"
        f"- Run: nslookup -type=NS {DOMAIN} 8.8.8.8\n"
        "- The NS returned are the authoritative delegation.\n\n"
        "### Step 2: Apply one of the following\n"
        "#### Option B1: If authoritative is dns-parking\n"
        "- Log into the dns-parking panel (where DNS is actually served)\n"
        f"- Create: {SUBDOMAIN}  CNAME  {EXPECTED_CNAME_TARGET}\n"
        "- Ensure there is no A/AAAA for the same host.\n\n"
        "#### Option B2: Move DNS to Cloudflare (recommended) or Hostinger\n"
        "- In your registrar: change nameservers to Cloudflare/Hostinger\n"
        "- After delegation updates, create the same CNAME in that DNS provider.\n\n"
        "### Step 3: Verify\n"
        f"- dig {FQDN} CNAME +trace\n"
        f"- dig {FQDN} CNAME @8.8.8.8 +noall +answer +comments\n\n"
        "### Step 4: Render TLS\n"
        "- Once CNAME resolves, Render will issue TLS for the custom domain.\n"
        f"- Verify: curl -I https://{FQDN}/health\n"
    )
    write(OUT_DIR / "DNS_FIX_ROADMAP.md", roadmap)

    # Retest commands
    retest = (
        "# DNS Retest Commands\n\n"
        "Run these after making DNS changes:\n\n"
        + codeblock(
            "\n".join([
                f"nslookup -type=NS {DOMAIN} 8.8.8.8",
                f"nslookup -type=CNAME {FQDN} 8.8.8.8",
                f"nslookup -type=CNAME {FQDN} 1.1.1.1",
                f"dig {FQDN} CNAME +trace",
                f"dig {FQDN} CNAME @8.8.8.8 +noall +answer +comments",
                f"dig {FQDN} CNAME @1.1.1.1 +noall +answer +comments",
            ])
        )
    )
    write(OUT_DIR / "DNS_RETEST_COMMANDS.md", retest)

    # Optional helper script
    helper = f'''#!/usr/bin/env python3
import shutil, subprocess, sys

DOMAIN="{DOMAIN}"
FQDN="{FQDN}"

def have(x): return shutil.which(x) is not None
def run(cmd):
    p = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print("\\n$ " + cmd)
    print(p.stdout.strip())

if not have("dig") and not have("nslookup"):
    print("Missing dig/nslookup. Install dnsutils (Linux) or use WSL (Windows).")
    sys.exit(1)

if have("nslookup"):
    run(f"nslookup -type=NS {{DOMAIN}} 8.8.8.8")
    run(f"nslookup -type=CNAME {{FQDN}} 8.8.8.8")
    run(f"nslookup -type=CNAME {{FQDN}} 1.1.1.1")

if have("dig"):
    run(f"dig NS {{DOMAIN}} @8.8.8.8 +noall +answer +authority +additional")
    run(f"dig {{FQDN}} CNAME @8.8.8.8 +noall +answer +comments")
    run(f"dig {{FQDN}} CNAME @1.1.1.1 +noall +answer +comments")
    run(f"dig {{FQDN}} CNAME +trace")
'''
    tools_dir = Path("backend/tools")
    tools_dir.mkdir(parents=True, exist_ok=True)
    write(tools_dir / "dns_verify.py", helper)

    print("OK: generated docs/dns/* and backend/tools/dns_verify.py")
    print("See docs/dns/DNS_ROOTCAUSE_REPORT.md for classification and evidence.")

if __name__ == "__main__":
    main()
