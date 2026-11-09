#!/usr/bin/env bash
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/mesh_3d/foam_core_shape_fit/src"
$PY -u models/mesh_3d/foam_core_shape_fit/src/fit_shape.py | tee models/mesh_3d/foam_core_shape_fit/outputs/results_shape.txt     # ~20 min
