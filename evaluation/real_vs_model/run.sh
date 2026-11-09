#!/usr/bin/env bash
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env.sh"
for n in IMG_0536 IMG_0537; do $PY evaluation/real_vs_model/src/side_by_side.py $n; done
