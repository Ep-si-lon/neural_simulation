# 3D foam core refitted with the hop term

**Idea.** Same as `foam_core_no_lift` but the residual also contains the hop: `LIFT_W · (ℓ − ℓ_meas)` with `LIFT_W = 4`, so the model must hop about as high as the real ball.

## Formulas and parameters
Same physics as `../foam_core_height_fit`. Fitted (per unit mass): `k_s = 126.6`, `k_b = 276.4`, `k_r = 1000.5`, `c_d = 23.0`. The optimizer's second start (these values) ended exactly where it began and still had the lower cost (0.43 against 0.70 for the hopping start), so this may not be a true optimum.

## Results (peak lift in mm; ball height 67 mm; real 7.0, 7.4, 3.6, 5.2)
| Clip | Set | Real | No-lift fit | With-lift fit |
| --- | --- | --- | --- | --- |
| 0536 | train | 7.0 | 50.3 | 5.9 |
| 0537 | train | 7.4 | 63.3 | 8.9 |
| 0538 | test | 3.6 | 8.7 | 0.0 |
| 0539 | test | 5.2 | 8.5 | 0.0 |

Matching the hop slows recovery: 95 % height at 40–54 ms against 13–42 ms real. Hop table and curves (against the no-lift fit and the real clips): `outputs/hop_check.md`, `outputs/hops.png`, produced by `src/hop_check.py`.

## Assumptions and limitations
As `foam_core_height_fit`; no hop at all after the shallow (67 %) squeezes; tin friction or suction may account for part of the real hop and is not modelled.

## Run
`./run.sh` (about 20 min; needs `tracking/run.sh` first). Code `src/fit3d_lift.py`. Outputs `outputs/params_3d_lift.json`, `fit3d_lift_log.txt`, `hop_check.md`, `hops.png`.

**Videos** (`outputs/real_vs_3d_IMG_0536|0538|0539.mp4`): real clip, the model's side view and its oblique view on one clock (t = 0 at release, slowed 8x). 0536 is a training clip; 0538 and 0539 are held out. `./render.sh` re-renders them from the saved parameters in about a minute.
