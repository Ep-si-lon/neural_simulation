#!/usr/bin/env bash
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env.sh"
export PYTHONPATH="$PYTHONPATH:$ROOT/models/lumped_1d/bounce_recovery/src"
O=models/lumped_1d/bounce_recovery/outputs
$PY -u models/lumped_1d/bounce_recovery/src/fit.py | tee $O/results.txt
for n in IMG_0538 IMG_0539; do $PY models/lumped_1d/bounce_recovery/src/demo.py $n; done
