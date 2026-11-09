#!/usr/bin/env bash
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/mesh_3d/foam_core_with_lift/src"
$PY -u models/mesh_3d/foam_core_with_lift/src/fit3d_lift.py | tee models/mesh_3d/foam_core_with_lift/outputs/fit3d_lift_log.txt     # ~20 min
