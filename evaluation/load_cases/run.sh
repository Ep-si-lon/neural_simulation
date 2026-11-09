#!/usr/bin/env bash
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env.sh"
S=evaluation/load_cases/src/render_loads.py; O=evaluation/load_cases/outputs
NL=models/mesh_3d/foam_core_no_lift/outputs/params_3d.json; WL=models/mesh_3d/foam_core_with_lift/outputs/params_3d_lift.json
for m in flat point side; do $PY $S $m $NL $O/no_lift/latest_$m.mp4; $PY $S $m $WL $O/with_lift/lift_$m.mp4; done
$PY $S deep $NL $O/no_lift/deep_nolift.mp4; $PY $S deep $WL $O/with_lift/deep_withlift.mp4
