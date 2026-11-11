# Fast-snap variant (stiffer deep-compression regime)

**Idea.** The two-mass spring gets a second, much stiffer regime in deep compression, so a deeply squeezed ball pushes back hard at first and then hands over to the soft spring.
This variant was first built to explain a "snap back in 1-2 frames" that turned out to be an artefact of a wrong release frame (see `docs/correction_release_definition.md`). **With the corrected protocol the stiffer regime is genuinely used and helps**, so the variant stays, with a different justification.

## Formulas
Same two-mass system as `../two_mass_spring` (including the plate that follows the measured tin trajectory), with the internal force
`F_int = k x + k_hi · max(x − x₀, 0) − c ḣ`, `x = h_rest − h`, `x₀ = x0f · h_rest`.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| g, m split, K_T, ζ_T | as in two_mass_spring | fixed | 9.81, 0.5/0.5, 4×10⁶, 0.3 |
| h_rest, h_c, z_p(t), separation | per clip | measured (SAM 2) | — |
| k, c | base stiffness and damping (per unit mass) | fitted | 28,900 s⁻², 525 s⁻¹ |
| k_hi | extra stiffness beyond the threshold | fitted | 20,100 s⁻² |
| x0f | threshold, fraction of rest height | fitted | 0.22 |

## Assumptions and limitations
As the two-mass model, plus a piecewise-linear stiffening. Per-unit-mass parameters. The hop is captured on the deep presses (6.3 / 7.9 mm against 7.1 / 7.5) but not on the shallow ones (0.5 mm against 3.3 / 5.4). Five fitted numbers on two clips: expect some over-fitting.

## Results (SAM 2 truth; common footing)
| Clip | Height RMSE (% of ball height) | Two-mass spring | Plain exponential | 95 % recovery: model / real |
| --- | --- | --- | --- | --- |
| 0536 (train) | 1.8 | 2.4 | 5.4 | 30 / 34 ms |
| 0537 (train) | 1.9 | 1.7 | 6.1 | 31 / 39 ms |
| 0538 (**test**) | 1.1 | 1.7 | 3.1 | 24 / 27 ms |
| 0539 (**test**) | 1.1 | 1.6 | 3.4 | 24 / 24 ms |

The best of the 1D models on height error and recovery time (mean error 1.5 ms on the test clips).

## Run
`./run.sh` (about 5 min). Code `src/snap_sim.py` (model + fit), `src/demo_snap.py` (real clip next to the fast-snap simulation). Outputs: `outputs/results.txt`, `params.json`, `demo_snap_IMG_0538.mp4`, `demo_snap_IMG_0539.mp4`; `outputs/archive_v1_instant_release/` holds the earlier run.
