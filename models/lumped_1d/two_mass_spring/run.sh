#!/usr/bin/env bash
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/lumped_1d/two_mass_spring/src"
O=models/lumped_1d/two_mass_spring/outputs
$PY -u models/lumped_1d/two_mass_spring/src/sim.py | tee $O/sim_results.txt     # ~5 min
for n in IMG_0538 IMG_0539; do $PY models/lumped_1d/two_mass_spring/src/demo_sim.py $n; done
