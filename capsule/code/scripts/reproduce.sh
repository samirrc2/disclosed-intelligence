#!/usr/bin/env bash
# Reproduce every numerical result, table, and figure from the FROZEN dataset.
# No network, no API keys, no cost. Deterministic.
#
#   bash reproduce.sh                 # analyze + determinism (replication) check  [default]
#   bash reproduce.sh --analyze-only  # analyze once, skip the replication check
#   bash reproduce.sh --test          # run unit tests only
#   bash reproduce.sh --help
set -euo pipefail

usage() {
  cat <<'EOF'
Usage (from repository root or via /code/run on Code Ocean):

  bash reproduce.sh                 # analyze the frozen data + byte-identical replication check
  bash reproduce.sh --analyze-only  # analyze once
  bash reproduce.sh --test          # unit tests only (no data needed)
  bash reproduce.sh --help

Outputs: results/latest/{metrics_summary.md, tables/*.csv, figures/*.{png,svg}}
On Code Ocean these are written to /results.
EOF
}

MODE="full"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --analyze-only|--analyze) MODE="analyze"; shift ;;
    --replication|--full) MODE="full"; shift ;;
    --test) MODE="test"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

# Resolve roots for Code Ocean (/code,/data,/results) or a local checkout.
if [[ -d /code/src && -d /data ]]; then
  CODE_ROOT="/code"; export P10_DATA="/data"; export P10_RESULTS="/results"
  OUT="/results"
else
  CODE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  REPO_ROOT="$(cd "$CODE_ROOT/.." && pwd)"
  export P10_DATA="$REPO_ROOT/data"; export P10_RESULTS="$REPO_ROOT/results"
  OUT="$REPO_ROOT/results/latest"
fi
export PYTHONPATH="$CODE_ROOT/src:${PYTHONPATH:-}"

pybin="$(command -v python3 || command -v python)"
if [[ -z "$pybin" ]]; then echo "ERROR: python not found on PATH." >&2; exit 1; fi
echo "Python: $($pybin --version 2>&1)"

if [[ "$MODE" == "test" ]]; then
  exec bash "$CODE_ROOT/scripts/test.sh"
fi

mkdir -p "$OUT/tables" "$OUT/figures"
export P10_OUT_DIR="$OUT"

echo "== analyze =="
( cd "$CODE_ROOT/src" && "$pybin" analyze.py )

if [[ "$MODE" == "full" ]]; then
  echo "== replication (determinism) check =="
  ( cd "$CODE_ROOT/src" && "$pybin" replication_check.py )
fi

echo "Done. Open $OUT/metrics_summary.md (verdict first), tables/, figures/."
