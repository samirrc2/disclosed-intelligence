#!/usr/bin/env bash
# ============================================================================
# Disclosed Intelligence — REPRODUCE (offline, $0, no network, no API keys)
# ============================================================================
# Regenerates every reported number, table, and figure from the FROZEN,
# pseudonymized dataset, then runs the manuscript-wide numerical audit and a
# byte-identical determinism check. Delegates to the audited Code Ocean capsule
# (already submitted and approved) under capsule/.
#
#   bash reproduce.sh
#
# The original data-gathering path (network + API keys, time-sensitive) is the
# live pipeline in build/, analysis/, marketing/ and is NOT part of this
# reproduction; see run_all.sh.
# ============================================================================
set -euo pipefail
cd "$(dirname "$0")"
exec bash capsule/reproduce.sh "$@"
