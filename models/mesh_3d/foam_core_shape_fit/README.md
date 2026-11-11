# 3D foam core fitted to the ball's shape over time

**Idea.** Use more of the video: the outline, not only the height. In every frame the silhouette is fitted by the width profile `w(s) = W (1 − |2s−1|ⁿ)^(1/n)` (`s` = 0 top … 1 bottom): `W` is the maximum width and `n` the squareness (2 = ellipse, 5-6 = flat-sided cylinder). The simulated mesh is analysed with the same curve, so measured and simulated shape are like for like.

## Formulas
Same physics as `../foam_core_height_fit`. Fit residuals: `h − h_meas`, `ℓ − ℓ_meas` (lift), `3 (W/W_rest − meas)`, `0.05 (n − n_meas)`, per unit rest height; soft-L1 loss.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| k_s, k_b, k_r, c_d | stretch, bending, radial foam, damping (per unit mass) | fitted | 119 / 1,628 / 2,574 / 35.9 |
| mesh, table, g | see `../README.md` | fixed | — |
| W(t), n(t), h(t), lift(t), compressed height, tin trajectory | per clip | measured (SAM 2) | — |

## Results (SAM 2 truth; common footing)
| Clip | Height RMSE (%) | Plain exponential | 95 % recovery: model / real | Pressed width (curve) model / real | Hop (mm) model / real |
| --- | --- | --- | --- | --- | --- |
| 0536 (train) | 3.0 | 5.4 | 19 / 34 ms | 1.010 / 1.069 | 5.6 / 7.1 |
| 0537 (train) | 3.8 | 6.1 | 20 / 39 ms | 1.014 / 1.069 | 6.9 / 7.5 |
| 0538 (**test**) | 2.0 | 3.1 | 16 / 27 ms | 0.991 / 1.030 | 0.4 / 3.3 |
| 0539 (**test**) | 1.7 | 3.4 | 16 / 24 ms | 0.992 / 1.029 | 0.3 / 5.4 |

Beats the plain exponential (skill +0.37 to +0.49 on the test clips) and reproduces the pressed shape's squareness only partly (n at hold 3.2 against 4.1 real). It **under-bulges** (width ratio 0.99-1.01 against 1.03-1.07) and **recovers too fast** (16 ms against 24-27).

## Assumptions and limitations
As `foam_core_height_fit`. The deep-press training clips are not flat-sided enough. No hop after the shallow presses. Two starting points, 20 optimizer steps; the optimum may not have been reached.

**Videos** (`outputs/real_vs_3d_IMG_0536|0538|0539.mp4`): real clip, the model's side view and its oblique view on one clock (time zero = the tin separates; the window starts just before the tin begins to retreat; slowed 8x). 0536 is a training clip; 0538 and 0539 are held out. `./render.sh` re-renders them from the saved parameters in about a minute.

## Run
`./run.sh` (fit about 20 min, then videos; `TRACKER=sam2`). Code `src/fit_shape.py`. Outputs `outputs/results_shape.txt`, `params_shape.json`, [archive/v1_instant_release](../../../archive/v1_instant_release/).
