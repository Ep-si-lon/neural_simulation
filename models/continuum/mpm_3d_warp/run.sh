#!/usr/bin/env bash
# 3D MPM with the material fitted by the axisymmetric FEM (run ../fem_axisymmetric_warp/run.sh first): evaluation against the real clips and videos (about 5 min).
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env_sim.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/continuum/mpm_3d_warp/src"
$PY -u models/continuum/mpm_3d_warp/src/run_mpm.py all
