#!/usr/bin/env bash
set -euo pipefail

BASE="https://trickster-api.gahenaxaisolutions.com"

echo "[*] Checking health..."
curl -i "$BASE/health" | sed -n '1,20p'

echo
echo "[*] Checking ready..."
curl -i "$BASE/ready" | sed -n '1,20p'

echo
echo "[*] Checking version..."
curl -i "$BASE/version" | sed -n '1,50p'

echo
echo "[*] Checking Request-ID preservation..."
curl -i "$BASE/health" -H "X-Request-ID: audit-fixed-001" | sed -n '1,25p'

echo
echo "[OK] If all returned 200 and X-Request-ID is present/preserved, deploy surface is healthy."
