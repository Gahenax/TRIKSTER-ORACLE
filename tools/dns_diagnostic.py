#!/usr/bin/env python3
"""
ANTIGRAVITY PROMPT (Python) — DNS/TLS Diagnosis for trickster-api.gahenaxaisolutions.com

Goal
- Determine why Google DNS (8.8.8.8) returns NXDOMAIN for:
  trickster-api.gahenaxaisolutions.com
- Produce a deterministic diagnosis and a concrete fix plan.
"""

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

DOMAIN = "gahenaxaisolutions.com"
SUB = "trickster-api"
FQDN = f"{SUB}.{DOMAIN}"
EXPECTED_CNAME_TARGET = "trickster-oracle-api.onrender.com"

REPORT_PATH = Path("DNS_DIAG_REPORT.md")

def run(cmd: str) -> str:
    p = subprocess.run(
        cmd,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return p.stdout.strip()

def header(title: str) -> str:
    return f"\n## {title}\n"

def codeblock(text: str) -> str:
    return f"\n```text\n{text}\n```\n"

def now_stamp() -> str:
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    local = datetime.now().strftime("%Y-%m-%d %H:%M:%S (local)")
    return f"UTC: {utc}\nLocal: {local}"

def extract_ns(ns_output: str):
    hosts = set()
    for line in ns_output.splitlines():
        line = line.strip()
        m = re.search(r"\sNS\s+([a-zA-Z0-9._-]+)\.?", line)
        if m:
            hosts.add(m.group(1).rstrip("."))
        m2 = re.search(r"nameserver\s*=\s*([a-zA-Z0-9._-]+)\.?", line, re.I)
        if m2:
            hosts.add(m2.group(1).rstrip("."))
    return sorted(hosts)

def classify(delegated_ns, auth_cname, auth_a, auth_aaaa, auth_status_lines, trace_out):
    auth_txt = "\n".join([auth_cname, auth_a, auth_aaaa, auth_status_lines]).lower()

    a_present = ("\tA\t" in auth_a) or re.search(r"\sIN\s+A\s", auth_a) is not None
    aaaa_present = ("\tAAAA\t" in auth_aaaa) or re.search(r"\sIN\s+AAAA\s", auth_aaaa) is not None
    cname_present = ("\tCNAME\t" in auth_cname) or re.search(r"\sIN\s+CNAME\s", auth_cname) is not None

    nxdomain = "nxdomain" in auth_txt or "status: nxdomain" in auth_txt or "non-existent domain" in auth_txt
    noerror = "status: noerror" in auth_txt

    hostinger_hint = any(("hostinger" in ns.lower()) for ns in delegated_ns)
    mismatch_suspected = not hostinger_hint and len(delegated_ns) > 0

    if mismatch_suspected and nxdomain:
        return "A) Nameserver delegation mismatch (zone not on Hostinger or editing wrong DNS zone)"
    if nxdomain and not cname_present and not a_present and not aaaa_present:
        return "B) Record not published in authoritative zone (missing CNAME or saved in draft / wrong host field)"
    if (a_present or aaaa_present) and not cname_present:
        return "C) Record conflict (A/AAAA present at host; cannot also use CNAME)"
    if cname_present and EXPECTED_CNAME_TARGET.lower() not in auth_cname.lower():
        return "E) Typo/malformed record (CNAME exists but target is not expected; check host/target formatting)"
    if cname_present and EXPECTED_CNAME_TARGET.lower() in auth_cname.lower():
        return "D) Record exists in authoritative; remaining issue likely negative caching/propagation in recursive resolvers"
    return "Unclear: needs deeper inspection (but outputs should contain enough to decide)."

def main():
    lines = []
    lines.append(f"# DNS Diagnosis Report\n")
    lines.append(f"FQDN: {FQDN}\nExpected CNAME: {EXPECTED_CNAME_TARGET}\n")
    lines.append(codeblock(now_stamp()))

    # Check tool availability
    lines.append(header("Tool Availability"))
    which_nslookup = run("where nslookup")
    lines.append(codeblock(f"nslookup: {which_nslookup}"))

    # 1) Delegated NS via public recursive (8.8.8.8)
    lines.append(header("1) Delegated Nameservers (Public)"))
    ns_nslookup = run(f"nslookup -type=NS {DOMAIN} 8.8.8.8")
    lines.append("### nslookup (8.8.8.8)\n" + codeblock(ns_nslookup or "nslookup not available"))

    delegated_ns = extract_ns(ns_nslookup)
    lines.append(f"\nExtracted delegated NS: {', '.join(delegated_ns) if delegated_ns else '(none parsed)'}\n")

    # 2) Check FQDN against 8.8.8.8 and 1.1.1.1
    lines.append(header("2) Recursive Resolver Checks"))
    q1 = run(f"nslookup -type=CNAME {FQDN} 8.8.8.8")
    q2 = run(f"nslookup -type=CNAME {FQDN} 1.1.1.1")
    lines.append("### nslookup CNAME (8.8.8.8)\n" + codeblock(q1))
    lines.append("### nslookup CNAME (1.1.1.1)\n" + codeblock(q2))

    # 3) Direct authoritative queries
    lines.append(header("3) Direct Authoritative Queries"))
    auth_ns = delegated_ns[:1]
    if not auth_ns:
        lines.append("No authoritative NS parsed from delegation. Cannot do direct @ns queries.\n")
        auth_cname = auth_a = auth_aaaa = auth_status = ""
    else:
        auth = auth_ns[0]
        auth_cname = run(f"nslookup -type=CNAME {FQDN} {auth}")
        auth_a = run(f"nslookup -type=A {FQDN} {auth}")
        auth_aaaa = run(f"nslookup -type=AAAA {FQDN} {auth}")
        auth_status = ""  # Windows nslookup doesn't show status like dig
        lines.append(f"Authoritative NS used (first from delegation): {auth}\n")
        lines.append("### @auth CNAME\n" + codeblock(auth_cname))
        lines.append("### @auth A\n" + codeblock(auth_a))
        lines.append("### @auth AAAA\n" + codeblock(auth_aaaa))

    # 4) Classify root cause
    lines.append(header("4) Root Cause Classification"))
    classification = classify(delegated_ns, auth_cname, auth_a, auth_aaaa, auth_status, "")
    lines.append(f"{classification}\n")

    lines.append(header("5) Fix Steps (Exact, Minimal)"))

    fix_steps = []

    if classification.startswith("A)"):
        fix_steps += [
            "1) Confirm which nameservers are delegated publicly:",
            f"   - Run: nslookup -type=NS {DOMAIN} 8.8.8.8",
            "2) If the NS are NOT Hostinger NS, you are editing the wrong DNS zone in Hostinger.",
            "3) Fix by updating nameservers at your registrar to Hostinger-provided NS (as shown in Hostinger).",
            "4) Wait for NS propagation (can take hours). After that, re-add/confirm the CNAME in the authoritative zone.",
        ]
    elif classification.startswith("B)"):
        fix_steps += [
            "1) In Hostinger hPanel DNS Zone for gahenaxaisolutions.com, ensure the record exists and is saved (not draft):",
            "   - Type: CNAME",
            "   - Host/Name: trickster-api (NOT the full domain unless the UI explicitly requires it)",
            f"   - Target/Points to: {EXPECTED_CNAME_TARGET} (no https://, no spaces; trailing dot optional)",
            "2) Ensure there is NO A or AAAA record for trickster-api at the same time.",
            "3) If Hostinger UI supports it, set TTL temporarily to 300 for faster subsequent changes.",
            "4) Re-test authoritative directly once saved.",
        ]
    elif classification.startswith("C)"):
        fix_steps += [
            "1) Remove any A and/or AAAA records that exist for host trickster-api.",
            "2) Keep ONLY the CNAME record:",
            f"   - trickster-api CNAME {EXPECTED_CNAME_TARGET}",
            "3) Save/publish changes.",
            "4) Re-test authoritative and then recursive resolvers.",
        ]
    elif classification.startswith("D)"):
        fix_steps += [
            "1) Confirm authoritative has the correct CNAME (already indicated).",
            "2) This is likely negative caching or propagation in recursive resolvers.",
            "3) Wait and re-check using 8.8.8.8 and 1.1.1.1 every 10–15 minutes.",
            "4) Optionally reduce TTL to 300 for future changes (does not retroactively clear negative cache).",
        ]
    elif classification.startswith("E)"):
        fix_steps += [
            "1) Correct the CNAME target value. Common mistakes:",
            "   - Using https:// in the target (must be hostname only)",
            "   - Target misspelling (.onrender.com, service name, extra dots)",
            "2) Correct record to:",
            f"   - trickster-api CNAME {EXPECTED_CNAME_TARGET}",
            "3) Ensure no A/AAAA conflict at the same host.",
            "4) Re-test authoritative and then recursive resolvers.",
        ]
    else:
        fix_steps += [
            "1) Check delegated NS and query each authoritative NS directly.",
            "2) If you provide the outputs, we can pinpoint the issue precisely.",
        ]

    lines.append(codeblock("\n".join(fix_steps)))

    # 5) Deterministic retest commands
    lines.append(header("6) Deterministic Retest Commands"))
    retest_cmds = [
        f"nslookup -type=NS {DOMAIN} 8.8.8.8",
        f"nslookup -type=CNAME {FQDN} 8.8.8.8",
        f"nslookup -type=CNAME {FQDN} 1.1.1.1",
    ]
    if delegated_ns:
        retest_cmds.append(f"nslookup -type=CNAME {FQDN} {delegated_ns[0]}")
    lines.append(codeblock("\n".join(retest_cmds)))

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"OK: wrote report to {REPORT_PATH.resolve()}")
    print(f"Summary classification: {classification}")

if __name__ == "__main__":
    main()
