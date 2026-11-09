#!/usr/bin/env bash
# Re-renders this model's videos from its saved parameters (about 1 min): real clip vs the 3D model on one clock, t = 0 at release.
# One training clip (0536) and the two held-out clips (0538, 0539).
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env.sh"
for n in IMG_0536 IMG_0538 IMG_0539; do $PY shared/real_vs_3d.py $n models/mesh_3d/gas_shell/outputs/params_gas.json models/mesh_3d/gas_shell/outputs/real_vs_3d_$n.mp4 "gas shell (sealed gas)"; done