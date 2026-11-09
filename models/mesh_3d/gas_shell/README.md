# 3D gas-filled shell (abandoned)

**Idea.** The ball is a sealed, air-filled skin: surface springs plus an internal gas whose pressure rises as the volume shrinks.

## Formulas (per node `i`, per unit mass; `m = 1/162`)
- Stretch spring on every mesh edge: `f = −k_s (l − l₀) û − c_d (v_rel · û) û`
- Bending spring between the two far corners of each pair of neighbouring triangles: `f = −k_b (l_b − l_b0) û_b`
- Gas pressure: `p = p₀ V₀ / V`, with `V = Σ a·(b×c) / 6` over triangles; force `p · A · n̂` split over each triangle's 3 nodes (outward normal)
- Gravity `−g`, table penalty (`K_T = 10⁷`) and friction, contact penalty from the pressing tool.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| k_s, k_b | stretch / bending spring | fitted | 6853, 827 |
| p₀ | initial gas pressure (per unit mass) | fitted | 25 |
| c_d | damping | fitted | 0.7 |
| mesh, table, g | see `../README.md` | fixed | — |
| compressed height, release time | per clip | measured | — |

## Assumptions
Gas amount constant and isothermal; skin stretchable; uniform pressure; foam walls ignored.

## Limitations (why abandoned)
- Sealed gas under a stretchy skin conserves volume: the pressed ball bulged to 1.23–1.26× its width (measured 1.10×), like a water balloon.
- The fit chose almost no damping (damping ratio ≈ 0.04), so after release it rang and bulged on each bounce; height RMSE 10–13 %.
- A real foam ball is porous and does not conserve volume; replaced by `foam_core_height_fit`.

## Run
`./run.sh` (about 10 min; needs `tracking/run.sh` first). Code `src/fit_gas.py` (restored from the commit where the gas model was first fitted). Outputs `outputs/results_gas.txt`, `params_gas.json`, and the two earlier demo videos `demo_flat_gas.mp4`, `demo_point_gas.mp4` (an earlier renderer; superseded by the `real_vs_3d_*` videos).

**Videos** (`outputs/real_vs_3d_IMG_0536|0538|0539.mp4`): real clip, the model's side view and its oblique view on one clock (t = 0 at release, slowed 8x). 0536 is a training clip; 0538 and 0539 are held out. `./render.sh` re-renders them from the saved parameters in about a minute.
