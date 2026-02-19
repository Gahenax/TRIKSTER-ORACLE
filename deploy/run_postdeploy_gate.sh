#!/usr/bin/env bash
set -euo pipefail

# Post-deploy gate runner
# Usage:
#   export VIEWER_BASE_URL=https://viewer.example.com
#   export VIEWER_API_KEY=...
#   python _antigravity_out/go_live_gate.py

if [[ -z "${VIEWER_BASE_URL:-}" ]]; then
  echo "Missing VIEWER_BASE_URL (e.g. https://viewer.example.com)"
  exit 1
fi

echo "Running post-deploy gate against: $VIEWER_BASE_URL"
python _antigravity_out/go_live_gate.py
