# Two-mass spring simulation (squeeze and release)

**Idea.** Simulate the deformation itself: a bottom mass resting on the table and a top mass, joined by a nonlinear spring-damper. The tin presses the top; on release the ball is simulated from its squeezed state.

## Formulas
Heights in px, masses normalised so `m_b + m_t = 1` (`m_b = m_t = 0.5`). `h = y_t − y_b`, compression `x = h_rest − h`.

- Internal force: `F_int = k x + k₃ x³ − c ḣ`, with `k₃ = k · z₃ / h_rest²`
- `m_t ÿ_t = F_int − m_t g_px`, `m_b ÿ_b = F_table − F_int − m_b g_px`
- Table (only if `y_b < 0`): `F_table = −K_T y_b − 2 ζ_T √K_T ẏ_b`
- Start (release): `y_b = 0`, `y_t = h_c` (measured compressed height), both velocities zero.
- Linear case (`k₃ = 0`): relative-mode frequency `ω = 2√k`, damping ratio `ζ = c / √k`.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| g_px | gravity in px/s² (9.81 × px per metre) | fixed | — |
| m_b, m_t | mass split | fixed | 0.5, 0.5 |
| K_T, ζ_T | table penalty stiffness / damping ratio | fixed (numerical) | 4×10⁶ s⁻², 0.3 |
| h_rest, h_c, release time | rest height, compressed height, release instant | measured per clip | h_c = 41, 36, 67, 67 % of rest |
| k | spring constant per unit mass | fitted | 14,341 s⁻² (leave-one-out 10,800–15,700) |
| c | damping per unit mass | fitted | 371 s⁻¹ (268–403) |
| z₃ | cubic stiffening | fitted | about 0 in 3 of 4 folds |

Derived: `ω = 2√k` = 33–40 Hz, `ζ = c/√k` = 2.6–3.2 (strongly overdamped).

## Assumptions
One vertical degree of freedom pair; mass lumped in two halves; homogeneous spring; tin removed instantaneously at release; table is a stiff damped penalty contact; width from an empirical law in the demo (not part of the physics).

## Limitations
- Real ball snaps back in 1–2 frames; the model recovers over about 50 ms (a single spring cannot give a fast snap and a slow tail).
- Hop height under-predicted for 0538/0539, over-predicted for 0537.
- Stiffness and damping are per unit mass (no mass measured); the tin's pull and friction are not modelled.

## Results (height RMSE, % of ball height)
| Held-out clip | Simulation | Exponential recovery | Stay compressed |
| --- | --- | --- | --- |
| 0538 | 6.6 | **4.0** | 32.1 |
| 0539 | 6.2 | **3.8** | 31.4 |
| 0536 | 8.3 | **5.8** | 56.3 |
| 0537 | 7.9 | **5.6** | 62.4 |

**It loses to the exponential on all four clips.**

## Run
`./run.sh` (about 6 min). Code: `src/sim.py` (model, fit, leave-one-out), `src/demo_sim.py` (real clip next to the ellipsoid, squeeze + release). Outputs: `outputs/sim_results.txt`, `sim_params.json`, `demo_squeeze_IMG_0538.mp4`, `demo_squeeze_IMG_0539.mp4`.
