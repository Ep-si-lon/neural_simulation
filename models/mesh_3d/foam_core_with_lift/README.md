# 3D foam core refitted with the hop term

**Idea.** As `foam_core_no_lift`, but the residual also contains the hop: `LIFT_W · (ℓ − ℓ_meas)` with `LIFT_W = 4`, so the model is asked to hop about as high as the real ball.

## Formulas and parameters
Same physics as `../foam_core_height_fit`. Fitted (per unit mass): `k_s = 110`, `k_b = 3,062`, `k_r = 3,161`, `c_d = 44.0`. Trained on 0536+0537 with the plate following the measured tin trajectory.

## Results (SAM 2 truth; common footing; peak lift in mm, ball height 67 mm)
| Clip | Height RMSE (%) | 95 % recovery: model / real | Hop: with-lift / no-lift fit / real |
| --- | --- | --- | --- |
| 0536 (train) | 3.0 | 19 / 34 ms | 6.4 / 0.2 / 7.1 |
| 0537 (train) | 3.8 | 19 / 39 ms | 7.8 / 0.6 / 7.5 |
| 0538 (**test**) | 2.1 | 16 / 27 ms | 0.9 / 0.0 / 3.3 |
| 0539 (**test**) | 1.9 | 15 / 24 ms | 0.7 / 0.0 / 5.4 |

Matching the hop costs height accuracy (2.0 % against 1.1 % for the no-lift fit) and speed (it recovers in 15-19 ms against 24-39 real). It reproduces the hops of the deep presses and almost none of the shallow ones. Hop table and curves against the no-lift fit and the real clips: `outputs/hop_check.md`, `outputs/hops.png` (from `src/hop_check.py`).

## Assumptions and limitations
As `foam_core_height_fit`. Tin friction or suction may account for part of the real hop and is not modelled. Two starting points, 20 optimizer steps.

**Videos** (`outputs/real_vs_3d_IMG_0536|0538|0539.mp4`): real clip, the model's side view and its oblique view on one clock (time zero = the tin separates; the window starts just before the tin begins to retreat; slowed 8x). 0536 is a training clip; 0538 and 0539 are held out. `./render.sh` re-renders them from the saved parameters in about a minute.

## Run
`./run.sh` (fit about 20 min, then videos and the hop check; `TRACKER=sam2`). Code `src/fit3d_lift.py`, `src/hop_check.py`. Outputs `outputs/params_3d_lift.json`, `fit3d_lift_log.txt`, `hop_check.md`, `hops.png`, `outputs/archive_v1_instant_release/`.
