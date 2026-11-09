#!/usr/bin/env bash
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/mesh_3d/foam_core_height_fit/src"
$PY -u models/mesh_3d/foam_core_height_fit/src/fit3d.py | tee models/mesh_3d/foam_core_height_fit/outputs/results.txt     # ~15 min; needs tracking/run.sh first
