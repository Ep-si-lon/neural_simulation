# Bounce + recovery model

**Idea.** After the ball separates from the tin its *height* recovers smoothly, and the visible bouncing is the whole ball hopping off the table. So: a rigid ballistic hop with restitution, plus an exponential recovery of the height. This model starts at the first apex of the hop, so it does not depend on the release instant; it was refitted on the SAM 2 measurements for consistency.

## Formulas
State at the first hop apex (velocity zero), measured from the clip: lift `A` of the ball above the table and height dip `δ_a` (fraction of rest height `h_rest`). With `g_px = 9.81 · (h_rest / 0.067 m)`:
- Observed top edge above rest: `y(t) = L(t; A, e, t_c) + h_rest · δ(t)`; height recovery `δ(t) = δ_a · exp(−t / τ)`.
- Lift `L`: first fall `L = A − ½ g_px t²` until `t_f = √(2A / g_px)`; then arcs `n = 1, 2, …` with launch speed `v_n = eⁿ g_px t_f`, duration `T_n = 2 eⁿ t_f`, separated by a table dwell `t_c` where `L = 0`. Apex heights shrink as `e^{2n} A`. `A = y(0) − h_rest δ_a`.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| g, diameter | gravity, 6.7 cm (pixels per metre) | fixed | 9.81 m/s², about 58 px/cm |
| h_rest, A, δ_a, apex time | per clip | measured | — |
| e | restitution | fitted | 0.69 (leave-one-out 0.62-0.70; per clip 0.59-0.86) |
| τ | height-recovery time constant | fitted | 36 ms (24-33 ms leave-one-out) |
| t_c | table contact dwell | fitted | 9 ms (9-14 ms) |

## Assumptions
Rigid-body hop; instantaneous bounce apart from `t_c`; exponential height recovery independent of the hop; start exactly at the first apex; bottom edge ignored.

## Limitations
- Covers only the time after the first apex (the height is already about 99 % there), so its height error is **not comparable** with the other models; it appears in the comparison for the hop only.
- The hop may include friction or suction with the tin, which the model attributes entirely to the ball.
- Height dip is 2-3 %, comparable to tracking noise, so `τ` is weakly determined.

## Results (top-edge RMSE after the apex, % of ball height; leave-one-clip-out)
| Held-out clip | Model | Single exponential | Stay at rest |
| --- | --- | --- | --- |
| 0536 | **1.38** | 1.74 | 4.71 |
| 0537 | **0.81** | 1.13 | 3.07 |
| 0538 | 1.19 | **0.92** | 1.39 |
| 0539 | **0.81** | 1.21 | 1.79 |

It beats both baselines on 3 of 4 clips. **Hop** (peak lift of the bottom edge, mm), model against real: 7.1 / 6.5 / 2.5 / 4.7 against 7.1 / 7.5 / 3.3 / 5.4, the closest of any model.

## Run
`./run.sh` (about 2 min; `TRACKER=sam2`). Code: `src/fit.py` (model, fit, evaluation), `src/demo.py` (real clip next to the ellipsoid proxy). Outputs: `outputs/results.txt`, `loo_predictions.png`, `demo_IMG_0538.mp4`, `demo_IMG_0539.mp4`; [archive/v1_instant_release](../../../archive/v1_instant_release/) holds the earlier colour-tracker run.
