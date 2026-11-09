# 3D predictions for other loads

The 3D foam-core models were fitted only on top-down flat presses. Here they are run, unchanged, with other tools. **These are predictions, not validated against video**; compare with your intuition or a new recording.

| Load | Tool | Press depth |
| --- | --- | --- |
| flat | flat plate on top | to 62 % of height (38 % compression) |
| point | 6 mm probe on top | tip travels 50 % of rest height |
| side | two vertical flat plates at the sides | width squeezed by 40 % |
| deep | flat plate on top | 75 % compression (outside the fitted range) |

`outputs/no_lift/`: fit without the hop term (`latest_*.mp4`, `deep_nolift.mp4`); `outputs/with_lift/`: fit with the hop term (`lift_*.mp4`, `deep_withlift.mp4`). Each video has a side view and an oblique 3D view, slowed 8×.

## What they show
- Flat press: flattens top and bottom, slight bulge, smooth recovery.
- Point force: small local dent, rest of the ball stays round, ball tilts and slides slightly (friction setting was not fitted).
- Two side plates: cylinder-like squeeze; height stays about 101–102 % (volume not conserved, foam-like).
- 75 % press: stable but the coarse mesh folds into a wrinkled pancake (no self-contact); the no-lift model hops 90 mm (unphysical), the with-lift model 16 mm.

Run `./run.sh` (about 5 min); code `src/render_loads.py` (uses `shared/render3d.py`).
