#!/usr/bin/env bash
# Runs everything that is fast (~15 min): tracking, the three lumped models, the evaluations using the saved 3D parameters, and demo videos.
# The slow 3D fits (each ~10-20 min) are listed at the bottom and run only with ./run_all.sh --fit-3d.
set -euo pipefail
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
tracking/run.sh
models/lumped_1d/bounce_recovery/run.sh
models/lumped_1d/two_mass_spring/run.sh
models/lumped_1d/fast_snap/run.sh
if [ "${1:-}" = "--fit-3d" ]; then
  for m in gas_shell foam_core_height_fit foam_core_shape_fit foam_core_no_lift foam_core_with_lift; do models/mesh_3d/$m/run.sh; done
fi
evaluation/recovery_time/run.sh
evaluation/hop_height/run.sh
evaluation/load_cases/run.sh
evaluation/real_vs_model/run.sh
