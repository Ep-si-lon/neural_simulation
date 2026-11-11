# Sourced by the Warp/PyTorch/SAM 2 run scripts: repo root, the separate .venv-sim, and the shared import path.
ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
cd "$ROOT"
[ -d .venv-sim ] || { python3 -m venv .venv-sim; .venv-sim/bin/pip install -q -r requirements-sim.txt; }
PY="$ROOT/.venv-sim/bin/python"
export PYTHONPATH="$ROOT/shared:$ROOT/tracking/src"
export TRACKER=sam2        # the continuum models are fitted to the SAM 2 outlines (the colour tracker reads the pressed top edge too high, see tracking/README.md)
