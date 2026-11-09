# 3D foam-core ball, first fit (height, lift, pressed width)

**Idea.** Replace the sealed gas by a foam core: every surface node is tied to the ball's centre by a spring. Squashing is resisted without pushing the sides out, and volume is not conserved.

## Formulas
Edge stretch, bending, gravity, table and tool contact as in `../gas_shell`, with the gas pressure removed and a radial term added (centre `c` = mean of the nodes):

- `f_i = −[ k_r (|r_i − c| − r₀) + c_d (v_rel · r̂_i) ] r̂_i`, `r_i = x_i − c`; the mean of all `f_i` is subtracted so the internal force carries no net momentum.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| k_s | edge stretch spring (skin) | fitted | 128 |
| k_b | bending spring | fitted | 321 |
| k_r | radial foam-core spring | fitted | 778 |
| c_d | damping | fitted | 18.7 |
| mesh, table, g | see `../README.md` | fixed | — |
| compressed height, release time, pressed width | per clip | measured | — |

All per unit mass. Bounds on the fit keep the explicit integrator stable (stiffness ≤ 2×10⁶, c_d ≤ 50).

## Fit targets
Residual = height(t)/rest − measured, lift(t)/rest − measured, 3 × (pressed width/rest − measured). Trained on 0536+0537, tested on 0538+0539, no refit.

## Results
| Clip | Height RMSE | Lift RMSE | Pressed width, sim vs measured |
| --- | --- | --- | --- |
| 0536 (train) | 7.7 % | 3.7 % | 1.07 vs 1.10 |
| 0537 (train) | 7.8 % | 4.8 % | 1.08 vs 1.10 |
| 0538 (test) | 6.3 % | 2.4 % | 1.06 vs 1.07 |
| 0539 (test) | 6.2 % | 3.2 % | 1.06 vs 1.06 |

The width bulge now matches. Height error is still not better than a plain exponential, and the ball does not hop (damping ratio about 4 on the radial mode).

## Assumptions and limitations
Foam is a radial spring field (no shear); skin and core are homogeneous; the plate is removed instantly; the squeeze is quasi-static, only the release is timed; stiffnesses are per unit mass and mesh-dependent; the tin's friction/suction is not modelled.

## Run
`./run.sh` (about 15 min; needs `tracking/run.sh` first). Code `src/fit3d.py`. Outputs `outputs/results.txt`, `params.json`, and the earlier demo videos `demo_flat.mp4`, `demo_point.mp4`.
