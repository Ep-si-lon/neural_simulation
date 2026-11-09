# Fast-snap variant (negative result)

Hypothesis: the squeeze/release simulation (`src/sim.py`) recovers too slowly because one spring cannot give both a fast snap-back and a slow tail.
Variant: add a much stiffer spring regime in deep compression, `F = k·x + k_hi·max(x − x0, 0) − c·ḣ`, so the ball snaps back quickly, then hands over to the soft spring.

Run from the repo root: `PYTHONPATH=src:fast_snap python -u fast_snap/snap_sim.py` (about 5 min). Output: `results.txt`, `params.json`.

Result: **no improvement.** Height RMSE is the same as `src/sim.py` to within 0.2 points on every held-out clip (6.2–8.3 % vs the exponential baseline's 3.8–5.8 %).
The fit pushed the extra stiffness `k_hi` small (280–10 000, against `k` of 13 000–19 000) and put the threshold `x0` at 31–60 % of rest height, so the extra regime is barely used.
The data do not support a stiffer deep-compression regime as the explanation for the fast first frames.

Remaining candidates (untested): the first 1–2 frames after the tin leaves are hand-driven (the tin still carries the ball's top edge up), or are corrupted by tin glare on the top edge, so they are not ball dynamics.
A cleaner test needs the tin's own position tracked, or a clip with the tin withdrawn more slowly.
