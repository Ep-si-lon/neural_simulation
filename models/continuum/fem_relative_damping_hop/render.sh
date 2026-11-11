#!/usr/bin/env bash
# Re-renders the real-vs-FEM x16 videos from ../fem_axisymmetric_warp/outputs/params_fem.json (about 5 min).
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env_sim.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/continuum/fem_axisymmetric_warp/src"
for n in IMG_0536 IMG_0538 IMG_0539; do $PY models/continuum/fem_relative_damping_hop/src/render_hop16.py $n; done
