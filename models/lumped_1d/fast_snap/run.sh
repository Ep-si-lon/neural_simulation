#!/usr/bin/env bash
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/lumped_1d/fast_snap/src"
$PY -u models/lumped_1d/fast_snap/src/snap_sim.py | tee models/lumped_1d/fast_snap/outputs/results.txt     # ~5 min
