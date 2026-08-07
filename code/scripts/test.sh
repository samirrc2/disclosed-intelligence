#!/usr/bin/env bash
# Unit tests for the statistics helpers (no API, no data files needed).
set -euo pipefail
CODE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$CODE_ROOT"
export PYTHONPATH="$CODE_ROOT/src:${PYTHONPATH:-}"
if ! command -v pytest >/dev/null 2>&1; then
  echo "ERROR: pytest not found. Install: pip install -r code/requirements.txt" >&2
  exit 1
fi
exec pytest -q
