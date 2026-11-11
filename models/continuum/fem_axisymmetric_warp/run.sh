#!/usr/bin/env bash
# Fit the axisymmetric FEM (Warp + PyTorch) on 0536+0537, evaluate on all clips, then render the videos. Needs .venv-sim (see ../../../env_sim.sh) and tracking/run.sh.
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env_sim.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/continuum/fem_axisymmetric_warp/src"
D=models/continuum/fem_axisymmetric_warp
$PY -u $D/src/fit_fem.py 45
"$(dirname "${BASH_SOURCE[0]}")/render.sh"
