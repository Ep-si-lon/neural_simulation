#!/usr/bin/env bash
# Hop model: scan the damping multiplier on the training clips, run the damping comparison, render the videos (about 10 min). Needs .venv-sim, tracking/run_sam2.sh and ../fem_axisymmetric_warp/outputs/params_fem.json.
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env_sim.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/continuum/fem_axisymmetric_warp/src"
D=models/continuum/fem_relative_damping_hop/src
$PY -u $D/hop_experiment.py | tee models/continuum/fem_relative_damping_hop/outputs/hop_experiment.txt
$PY -u $D/hop_scan.py
for n in IMG_0536 IMG_0538; do $PY $D/render_hop_experiment.py $n; done
for n in IMG_0536 IMG_0538 IMG_0539; do $PY $D/render_hop16.py $n; done
