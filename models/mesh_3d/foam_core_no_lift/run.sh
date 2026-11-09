#!/usr/bin/env bash
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/mesh_3d/foam_core_no_lift/src"
$PY -u models/mesh_3d/foam_core_no_lift/src/fit3d_recovery.py | tee models/mesh_3d/foam_core_no_lift/outputs/fit3d_log.txt     # ~20 min
