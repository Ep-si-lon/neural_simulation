# 3D gas-filled shell

**Idea.** The ball is a sealed, air-filled skin: surface springs plus an internal gas whose pressure rises as the volume shrinks.

## Formulas (per node, per unit mass; `m = 1/162`)
- Stretch spring on every mesh edge: `f = −k_s (l − l₀) û − c_d (v_rel · û) û`; bending spring between the far corners of neighbouring triangles: `f = −k_b (l_b − l_b0) û_b`.
- Gas pressure: `p = p₀ V₀ / V` (`V = Σ a·(b×c) / 6` over triangles), force `p · A · n̂` split over each triangle's 3 nodes. Gravity, table penalty and friction, contact penalty from the plate.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| k_s, k_b | stretch / bending spring | fitted | 30,000 / 3,000 |
| p₀ | initial gas pressure | fitted | 3,000 |
| c_d | damping | fitted | 5.0 |
| mesh, table, g, compressed height, tin trajectory | see `../README.md` | fixed / measured | — |

**These are the optimizer's starting values**: the fit made no progress from its first starting point (cost 0.199), so this model is effectively an unfitted baseline.

## Assumptions and limitations
Gas amount constant and isothermal; skin stretchable; uniform pressure. A sealed gas under a stretchy skin conserves volume, so the pressed ball bulges (1.165-1.169× width on the deep presses against 1.077× measured) and rings after release: the height overshoots by 5-10 % and oscillates for about 100 ms (see `evaluation/model_comparison/outputs/fig1_height_curves_all.png`). A real foam ball is porous; replaced by the foam-core models.

## Results (SAM 2 truth; common footing)
| Clip | Height RMSE (%) | Plain exponential | Pressed width model / real | Hop (mm) model / real |
| --- | --- | --- | --- | --- |
| 0536 (train) | 4.6 | 5.4 | 1.165 / 1.077 | 12.9 / 7.1 |
| 0537 (train) | 4.4 | 6.1 | 1.169 / 1.077 | 14.4 / 7.5 |
| 0538 (**test**) | 3.7 | 3.1 | 1.040 / 1.043 | 5.4 / 3.3 |
| 0539 (**test**) | 4.1 | 3.4 | 1.044 / 1.043 | 4.9 / 5.4 |

Worse than the plain exponential on the test clips.

**Videos** (`outputs/real_vs_3d_IMG_0536|0538|0539.mp4`): real clip, the model's side view and its oblique view on one clock (time zero = the tin separates; the window starts just before the tin begins to retreat; slowed 8x). 0536 is a training clip; 0538 and 0539 are held out. `./render.sh` re-renders them from the saved parameters in about a minute.

## Run
`./run.sh` (fit about 10 min, then videos; `TRACKER=sam2`). Code `src/fit_gas.py`. Outputs `outputs/results_gas.txt`, `params_gas.json`, the earlier `demo_*_gas.mp4` (old renderer) and [archive/v1_instant_release](../../../archive/v1_instant_release/).
