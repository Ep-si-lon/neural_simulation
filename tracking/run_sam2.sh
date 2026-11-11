#!/usr/bin/env bash
# SAM 2 (pretrained, tiny) video tracking of the four clips, compared with the colour tracker. Needs .venv-sim and a network connection the first time (downloads facebook/sam2.1-hiera-tiny from Hugging Face).
set -euo pipefail
source "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/env_sim.sh"
export SAM2_FRAMES="${SAM2_FRAMES:-/tmp/sam2_frames}"
for n in IMG_0536 IMG_0537 IMG_0538 IMG_0539; do $PY -u tracking/src/segment_sam2.py $n 2>&1 | grep -vE "Warning|post-processing|pred_masks_gpu|frame loading|propagate"; done
for n in IMG_0536 IMG_0537 IMG_0538 IMG_0539; do TRACKER=sam2 $PY tracking/src/sam2_tables.py $n; done   # per-frame tables the models read with TRACKER=sam2
