# 3D foam core refitted with the hop ignored ("no lift")

**Idea.** For the recovery-time question the hop is treated as a tin/table interaction, not a material property, so the fit residual contains only height, width and squareness: `h − h_meas`, `3 (W/W_rest − meas)`, `0.05 (n − n_meas)`.

## Formulas and parameters
Same physics as `../foam_core_height_fit`. Fitted (per unit mass): `k_s = 110.6`, `k_b = 950.7`, `k_r = 2576.9`, `c_d = 34.5`. Everything else fixed or measured as in `../README.md`. Trained on 0536+0537.

## Results
Recovery time is compared with the other models in `../../../evaluation/recovery_time` (95 % height after 22 ms on both test clips; real 25 and 13 ms).

**Side effect:** with nothing constraining the hop, the model launches the ball far too high: 13 mm after a 38 % press, 50–63 mm after the deep training squeezes (real 3–8 mm), and 90 mm at 75 % compression. See `../../../evaluation/hop_height`.

## Assumptions and limitations
As `foam_core_height_fit`. The hop height is unconstrained and unphysical; use this model only for recovery time and shape, not for hop. Fit used 2 starts and 20 steps.

## Run
`./run.sh` (about 20 min; needs `tracking/run.sh` first). Code `src/fit3d_recovery.py`. Outputs `outputs/params_3d.json`, `fit3d_log.txt`.
