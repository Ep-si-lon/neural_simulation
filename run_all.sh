#!/usr/bin/env bash
# Runs everything that is fast (~15 min): tracking, the three 1D models and the 3D videos / evaluation from the saved 3D parameters.
# The slow 3D fits (each ~10-20 min) run only with ./run_all.sh --fit-3d (each model's run.sh = fit + render.sh).
set -euo pipefail
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
tracking/run.sh
models/lumped_1d/bounce_recovery/run.sh
models/lumped_1d/two_mass_spring/run.sh
models/lumped_1d/fast_snap/run.sh
for m in gas_shell foam_core_height_fit foam_core_shape_fit foam_core_no_lift foam_core_with_lift; do
  if [ "${1:-}" = "--fit-3d" ]; then models/mesh_3d/$m/run.sh; else models/mesh_3d/$m/render.sh; fi
done
evaluation/recovery_time/run.sh
