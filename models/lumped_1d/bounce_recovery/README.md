# Bounce + recovery model

**Idea.** After release the ball's *height* hardly oscillates; the visible "ringing" is the whole ball hopping off the table. So: a rigid ballistic hop with restitution, plus an exponential recovery of the height.

## Formulas
State at the first hop apex (velocity zero), measured from the clip: lift `A` of the ball above the table and height dip `δ_a` (fraction of rest height `h_rest`). With `g_px = 9.81 · (h_rest / 0.067 m)`:

- Observed top edge above rest: `y(t) = L(t; A, e, t_c) + h_rest · δ(t)`
- Height recovery: `δ(t) = δ_a · exp(−t / τ)`
- Lift `L`: first fall `L = A − ½ g_px t²` until `t_f = √(2A / g_px)`; then arcs `n = 1, 2, …` with launch speed `v_n = eⁿ · g_px · t_f`, duration `T_n = 2 eⁿ t_f`, `L = v_n τ − ½ g_px τ²`, separated by a table-contact dwell `t_c` where `L = 0`. Apex heights shrink as `e^{2n} A`.
- `A = y(0) − h_rest · δ_a`.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| g | gravity | fixed | 9.81 m/s² |
| 6.7 cm | ball diameter → pixels per metre | fixed (rough estimate) | about 58 px/cm |
| h_rest, A, δ_a, apex time | rest height, starting lift, height dip, first-apex time | measured per clip | — |
| e | restitution | fitted | 0.66–0.71 (per clip 0.63–0.80) |
| τ | height-recovery time constant | fitted | 44–59 ms (per clip 30–72) |
| t_c | table contact dwell | fitted | 8–14 ms (per clip 7–16) |
| time shift | ±2 ms apex-time nuisance per clip | fitted (training only) | — |

## Assumptions
Rigid-body hop; instantaneous bounce apart from `t_c`; exponential height recovery that is independent of the hop; start exactly at the first apex; bottom edge ignored (it is clamped at the table line).

## Limitations
- Only models the motion *after* the first apex; the squeeze and release are inputs.
- Height dip is 2–3 % of height, comparable to tracking noise, so `τ` is weakly determined.
- Fails on IMG_0538: tin glare corrupts the apex, and the starting lift is overestimated.
- The hop may include friction/suction from the tin, which this model attributes entirely to the ball.

## Results (RMSE of top edge, % of ball height; model vs single exponential vs stay-at-rest)
| Held-out clip | Model | Exponential | Rest |
| --- | --- | --- | --- |
| 0538 (train 536+537) | 0.99 | **0.52** | 1.14 |
| 0539 (train 536+537) | **0.63** | 1.18 | 1.77 |
| 0536 (leave-one-out) | **1.11** | 1.69 | 4.42 |
| 0537 (leave-one-out) | **0.97** | 1.19 | 3.13 |
| 0538 (leave-one-out) | 1.18 | **0.55** | 1.14 |
| 0539 (leave-one-out) | **0.63** | 1.19 | 1.77 |

## Run
`./run.sh` (about 2 min). Code: `src/fit.py` (model + fit + evaluation), `src/demo.py` (real clip next to the ellipsoid proxy). Outputs: `outputs/results.txt`, `loo_predictions.png`, `demo_IMG_0538.mp4`, `demo_IMG_0539.mp4`.
