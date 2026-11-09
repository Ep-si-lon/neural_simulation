# 3D foam core fitted to the ball's shape over time

**Idea.** Use more of the video: not only height but the outline. In every frame the silhouette is fitted by the width profile `w(s) = W (1 − |2s−1|ⁿ)^(1/n)` (`s` = 0 top … 1 bottom). `W` is the max width and `n` the squareness (2 = ellipse, 5–6 = flat-sided cylinder). The simulated mesh is analysed with the same curve, so measured and simulated shape are like for like.

## Formulas
Same physics as `../foam_core_height_fit`. Fit residuals: `h − h_meas`, `ℓ − ℓ_meas` (lift), `3 (W/W_rest − meas)`, `0.05 (n − n_meas)`, all per unit rest height; soft-L1 loss.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| k_s, k_b, k_r, c_d | stretch, bending, radial foam, damping (per unit mass) | fitted | 126.6, 276.4, 1000.5, 23.0 |
| mesh, table, g | see `../README.md` | fixed | — |
| W(t), n(t), h(t), lift(t), compressed height, release | per clip | measured | — |

## Results (train 0536+0537, test 0538+0539)
| Clip | Height | Lift | Width (% of rest width) | Squareness n RMSE |
| --- | --- | --- | --- | --- |
| 0536 (train) | 7.6 % | 3.7 % | 1.6 | 0.92 |
| 0537 (train) | 7.7 % | 4.7 % | 0.5 | 0.98 |
| 0538 (test) | 6.1 % | 2.4 % | 1.4 | 0.15 |
| 0539 (test) | 6.0 % | 3.2 % | 0.7 | 0.21 |

Finding: the shape snaps back as fast as the height (n falls from 5 to about 2.4 within 2 frames), so the fast first frames are the ball's own, not only a measurement artifact.

## Assumptions and limitations
As `foam_core_height_fit`. The simulated ball does not hop (lift RMSE equals the size of the real hops). The deep-squeeze training clips are not flat-sided enough (n error about 0.9). Fit used 2 starts and 20 steps; it may not be a true optimum.

## Run
`./run.sh` (about 20 min; needs `tracking/run.sh` first). Code `src/fit_shape.py`. Outputs `outputs/results_shape.txt`, `params_shape.json`.

**Videos** (`outputs/real_vs_3d_IMG_0536|0538|0539.mp4`): real clip, the model's side view and its oblique view on one clock (t = 0 at release, slowed 8x). 0536 is a training clip; 0538 and 0539 are held out. `./render.sh` re-renders them from the saved parameters in about a minute.
