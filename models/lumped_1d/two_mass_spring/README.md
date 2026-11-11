# Two-mass spring simulation (squeeze, tin retreat, release)

**Idea.** Simulate the deformation itself: a bottom mass resting on the table and a top mass, joined by a nonlinear spring-damper. The tin presses the top mass, retreats along the measured trajectory, and the ball is then free.

## Formulas
Heights in px, masses normalised so `m_b + m_t = 1` (`m_b = m_t = 0.5`). `h = y_t − y_b`, compression `x = h_rest − h`.
- Internal force: `F_int = k x + k₃ x³ − c ḣ`, `k₃ = k z₃ / h_rest²`.
- `m_t ÿ_t = F_int − m_t g_px + a_plate`, `m_b ÿ_b = F_table − F_int − m_b g_px`.
- Table (if `y_b < 0`): `F_table = −K_T y_b − 2 ζ_T √K_T ẏ_b`. Plate (while the tin retreats, `t < T_ret`): `a_plate = −K_T (y_t − z_p(t)) − 2 ζ_T √K_T max(ẏ_t − ż_p, 0)` if `y_t > z_p`, with `z_p(t)` the measured tin trajectory.
- Start: plateau (`y_b = 0`, `y_t = h_c`, rest); time zero is the separation instant, `T_ret` = 46-121 ms later than the plateau end.
- Linear case: relative-mode `ω = 2√k`, damping ratio `ζ = c / √k`.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| g, m split, K_T, ζ_T | gravity, 0.5/0.5, contact stiffness, contact damping | fixed | 9.81, 0.5, 4×10⁶ s⁻², 0.3 |
| h_rest, h_c, z_p(t), separation | rest and pressed height, tin trajectory, separation frame | measured per clip (SAM 2) | h_c = 40, 34, 63, 62 % of rest |
| k | spring constant per unit mass | fitted | 8,970 s⁻² |
| c | damping per unit mass | fitted | 260 s⁻¹ |
| z₃ | cubic stiffening | fitted | 12.6 (used now) |

Derived (linear part): `ω = 2√k` = 189 rad/s (30 Hz), `ζ = c/√k` = 2.75, strongly overdamped.

## Assumptions and limitations
One vertical degree of freedom pair; homogeneous spring; table and plate are stiff penalty contacts; the ball's width is an empirical law in the demo, not physics. Per-unit-mass parameters (no mass measured). Recovery time is a little slow on the shallow test clips (35 / 34 ms against 27 / 24). The hop is captured for the deep presses (6.0 / 7.7 mm against 7.1 / 7.5) but not the shallow ones (0.1 mm against 3.3 / 5.4).

## Results (SAM 2 truth; common footing, see `evaluation/model_comparison`)
| Clip | Height RMSE (% of ball height) | Plain exponential | 95 % recovery: model / real |
| --- | --- | --- | --- |
| 0536 (train) | 2.4 | 5.4 | 39 / 34 ms |
| 0537 (train) | 1.7 | 6.1 | 39 / 39 ms |
| 0538 (**test**) | 1.7 | 3.1 | 35 / 27 ms |
| 0539 (**test**) | 1.6 | 3.4 | 34 / 24 ms |

It beats the plain exponential on every clip (skill +0.47 to +0.72). With the earlier, wrong protocol (instant removal at the mid-rise frame) the same model reported 6-8 %; that was an artefact (see `docs/correction_release_definition.md`).

## Run
`./run.sh` (about 6 min). Code: `src/sim.py` (model, fit, leave-one-out), `src/demo_sim.py` (real clip next to the ellipsoid). Outputs: `outputs/sim_results.txt`, `sim_params.json`, `demo_squeeze_IMG_0538.mp4`, `demo_squeeze_IMG_0539.mp4`; [archive/v1_instant_release](../../../archive/v1_instant_release/) holds the earlier run.
