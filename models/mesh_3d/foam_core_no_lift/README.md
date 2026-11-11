# 3D foam core refitted with the hop ignored ("no lift")

**Idea.** The hop is treated as a tin/table interaction rather than a material property, so the fit residual contains only height, width and squareness: `h − h_meas`, `3 (W/W_rest − meas)`, `0.05 (n − n_meas)`.

## Formulas and parameters
Same physics as `../foam_core_height_fit`. Fitted (per unit mass): `k_s = 100` (**on its lower bound**), `k_b = 1,795`, `k_r = 1,808`, `c_d = 48.2`. Trained on 0536+0537; the plate follows the measured tin trajectory before the ball is free.

## Results (SAM 2 truth; common footing)
| Clip | Height RMSE (%) | Plain exponential | 95 % recovery: model / real | Pressed width (curve) model / real | Hop (mm) model / real |
| --- | --- | --- | --- | --- | --- |
| 0536 (train) | 1.7 | 5.4 | 34 / 34 ms | 1.028 / 1.069 | 0.2 / 7.1 |
| 0537 (train) | 1.0 | 6.1 | 35 / 39 ms | 1.039 / 1.069 | 0.6 / 7.5 |
| 0538 (**test**) | 1.1 | 3.1 | 31 / 27 ms | 0.994 / 1.030 | 0.0 / 3.3 |
| 0539 (**test**) | 1.2 | 3.4 | 30 / 24 ms | 0.997 / 1.029 | 0.0 / 5.4 |

The largest skill against the plain exponential of any model (+0.65 to +0.83) and recovery times within 5 ms on average, at the price of **no hop** (the heavy damping 48 s⁻¹ absorbs the release energy; under the earlier, wrong protocol this model hopped 50-90 mm, which was an artefact).

## Assumptions and limitations
As `foam_core_height_fit`. The edge stiffness sits on its bound, so the parameters are not fully determined. It under-bulges (0.99-1.04 against 1.03-1.07).

**Videos** (`outputs/real_vs_3d_IMG_0536|0538|0539.mp4`): real clip, the model's side view and its oblique view on one clock (time zero = the tin separates; the window starts just before the tin begins to retreat; slowed 8x). 0536 is a training clip; 0538 and 0539 are held out. `./render.sh` re-renders them from the saved parameters in about a minute.

## Run
`./run.sh` (fit about 20 min, then videos; `TRACKER=sam2`). Code `src/fit3d_recovery.py`. Outputs `outputs/params_3d.json`, `fit3d_log.txt`, [archive/v1_instant_release](../../../archive/v1_instant_release/).
