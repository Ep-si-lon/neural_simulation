# Sourced by every run.sh: go to the repo root, create the virtualenv if needed, set PY and the shared import path.
ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
cd "$ROOT"
[ -d .venv ] || { python3 -m venv .venv; .venv/bin/pip install -q -r requirements.txt; }
PY="$ROOT/.venv/bin/python"
export PYTHONPATH="$ROOT/shared:$ROOT/tracking/src"
export TRACKER=sam2        # every model is fitted on the SAM 2 measurements (the colour tracker reads the pressed top edge too high); tracking/run.sh overrides this
