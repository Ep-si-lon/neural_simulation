#!/usr/bin/env bash
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env.sh"
export TRACKER=colour      # this script writes the colour-tracker outputs (tracking/outputs), not the SAM 2 ones
mkdir -p tracking/outputs/debug
for n in IMG_0536 IMG_0537 IMG_0538 IMG_0539; do $PY tracking/src/track.py $n & done; wait
for n in IMG_0536 IMG_0537 IMG_0538 IMG_0539; do ($PY tracking/src/silhouette.py $n && $PY tracking/src/shape.py $n) & done; wait
