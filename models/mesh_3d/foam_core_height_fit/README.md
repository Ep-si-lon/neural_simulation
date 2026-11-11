# 3D foam-core ball, first fit (height, lift, pressed width)

**Idea.** Replace the sealed gas by a foam core: every surface node is tied to the ball's centre by a spring. Squashing is resisted without pushing the sides out, and volume is not conserved.

## Formulas
Edge stretch, bending, gravity, table and plate contact as in `../gas_shell`, gas pressure removed, plus a radial term (centre `c` = mean of the nodes): `f_i = −[ k_r (|r_i − c| − r₀) + c_d (v_rel · r̂_i) ] r̂_i`, `r_i = x_i − c`, minus its mean so the internal force carries no net momentum.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| k_s | edge stretch spring (skin) | fitted | 15,400 |
| k_b | bending spring | fitted | 17.7 |
| k_r | radial foam-core spring | fitted | 1,078 |
| c_d | damping | fitted | 8.5 |
| mesh, table, g, compressed height, tin trajectory | see `../README.md` | fixed / measured | — |

All per unit mass. The fit chose a very stiff skin and a very soft bending spring, unlike the other foam fits (see `../foam_core_shape_fit`): the parameters are weakly determined by height, lift and width alone.

## Results (SAM 2 truth; common footing)
| Clip | Height RMSE (%) | Plain exponential | 95 % recovery: model / real | Pressed width model / real | Hop (mm) model / real |
| --- | --- | --- | --- | --- | --- |
| 0536 (train) | 3.8 | 5.4 | 21 / 34 ms | 1.033 / 1.077 | 7.4 / 7.1 |
| 0537 (train) | 3.4 | 6.1 | 51 / 39 ms | 1.038 / 1.077 | 8.2 / 7.5 |
| 0538 (**test**) | 3.3 | 3.1 | 11 / 27 ms | 1.051 / 1.043 | 2.8 / 3.3 |
| 0539 (**test**) | 3.0 | 3.4 | 10 / 24 ms | 1.050 / 1.043 | 2.3 / 5.4 |

Height error about the plain exponential's; recovery times scatter (10-51 ms); but it has the **closest hop of the mesh models** and the right width on the shallow presses.

## Assumptions and limitations
Foam is a radial spring field (no shear); skin and core homogeneous; per-unit-mass, mesh-dependent stiffnesses; tin friction or suction not modelled; three starting points, 20-30 optimizer steps.

**Videos** (`outputs/real_vs_3d_IMG_0536|0538|0539.mp4`): real clip, the model's side view and its oblique view on one clock (time zero = the tin separates; the window starts just before the tin begins to retreat; slowed 8x). 0536 is a training clip; 0538 and 0539 are held out. `./render.sh` re-renders them from the saved parameters in about a minute.

## Run
`./run.sh` (fit about 15 min, then videos; `TRACKER=sam2`). Code `src/fit3d.py`. Outputs `outputs/results.txt`, `params.json`, the earlier `demo_flat.mp4`, `demo_point.mp4` (old renderer) and [archive/v1_instant_release](../../../archive/v1_instant_release/).
