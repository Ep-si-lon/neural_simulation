#!/usr/bin/env bash
# Compares every model on the same footing (about 5 min once all models are fitted): forward-runs the earlier models (.venv, colour-tracker inputs), then the continuum models
# (.venv-sim, SAM 2 inputs) and the SAM 2 ground truth, then scores everything and draws the figures. Run the models' own run.sh first (or use the saved parameters).
set -euo pipefail
cd "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
export PYTHONPATH=shared:tracking/src TRACKER=sam2
.venv/bin/python -u evaluation/model_comparison/src/collect_earlier.py
TRACKER=sam2 .venv-sim/bin/python -u evaluation/model_comparison/src/collect_continuum.py
.venv/bin/python -u evaluation/model_comparison/src/compare_all.py
