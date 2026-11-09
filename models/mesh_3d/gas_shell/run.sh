#!/usr/bin/env bash
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/mesh_3d/gas_shell/src"
$PY -u models/mesh_3d/gas_shell/src/fit_gas.py | tee models/mesh_3d/gas_shell/outputs/results_gas.txt     # ~10 min
