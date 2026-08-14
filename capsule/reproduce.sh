#!/usr/bin/env bash
# Top-level entry point for Code Ocean / local reproduction.
# Delegates to code/scripts/reproduce.sh.
#
#   bash reproduce.sh                 # analyze frozen data + determinism check
#   bash reproduce.sh --analyze-only
#   bash reproduce.sh --test
#   bash reproduce.sh --help
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
if [[ -f "$ROOT/code/scripts/reproduce.sh" ]]; then
  exec bash "$ROOT/code/scripts/reproduce.sh" "$@"
else
  echo "ERROR: cannot find code/scripts/reproduce.sh" >&2
  exit 1
fi
