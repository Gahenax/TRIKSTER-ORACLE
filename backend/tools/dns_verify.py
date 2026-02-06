#!/usr/bin/env python3
import shutil, subprocess, sys

DOMAIN="gahenaxaisolutions.com"
FQDN="trickster-api.gahenaxaisolutions.com"

def have(x): return shutil.which(x) is not None
def run(cmd):
    p = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print("\n$ " + cmd)
    print(p.stdout.strip())

if not have("dig") and not have("nslookup"):
    print("Missing dig/nslookup. Install dnsutils (Linux) or use WSL (Windows).")
    sys.exit(1)

if have("nslookup"):
    run(f"nslookup -type=NS {DOMAIN} 8.8.8.8")
    run(f"nslookup -type=CNAME {FQDN} 8.8.8.8")
    run(f"nslookup -type=CNAME {FQDN} 1.1.1.1")

if have("dig"):
    run(f"dig NS {DOMAIN} @8.8.8.8 +noall +answer +authority +additional")
    run(f"dig {FQDN} CNAME @8.8.8.8 +noall +answer +comments")
    run(f"dig {FQDN} CNAME @1.1.1.1 +noall +answer +comments")
    run(f"dig {FQDN} CNAME +trace")
