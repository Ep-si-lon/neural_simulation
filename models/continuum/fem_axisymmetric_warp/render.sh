#!/usr/bin/env bash
# Re-renders the real-vs-FEM videos from outputs/params_fem.json (about 2 min): training clip 0536 and held-out 0538, 0539.
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env_sim.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/continuum/fem_axisymmetric_warp/src"
for n in IMG_0536 IMG_0538 IMG_0539; do $PY models/continuum/fem_axisymmetric_warp/src/render_fem.py $n; done
