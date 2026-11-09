#!/usr/bin/env bash
# One command: track -> fit/evaluate -> demo videos. Needs ffmpeg + the four originals in videos/IMG_053{6,7,8,9}.MOV
set -euo pipefail
cd "$(dirname "$0")"
[ -d .venv ] || { python3 -m venv .venv; .venv/bin/pip install -q -r requirements.txt; }
mkdir -p data out
export PYTHONPATH=src
for n in IMG_0536 IMG_0537 IMG_0538 IMG_0539; do .venv/bin/python src/track.py $n & done; wait
.venv/bin/python src/fit.py | tee out/results.txt
for n in IMG_0538 IMG_0539; do .venv/bin/python src/demo.py $n; done
