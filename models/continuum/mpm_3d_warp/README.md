# 3D material point method (MPM) ball, NVIDIA Warp

**Idea.** A second, independent solver for the same material. The ball is a cloud of 79,711 particles (2×2×2 per 2.5 mm grid cell, small fixed jitter) carrying mass, velocity and deformation; each step the particles pass momentum to a background grid, the physics runs on the grid, and the result goes back (MLS-MPM with APIC transfers). No mesh to fold, and the same code handles any load in 3D.
**E, ν and friction come from the axisymmetric FEM fit** (`../fem_axisymmetric_warp/outputs/params_fem.json`); only the damping rate was recalibrated, on the two training clips, because the grid dissipates differently from the FEM's nodal damping.

## Formulas
- Kirchhoff stress (compressible neo-Hookean): `τ = μ (F Fᵀ − I) + λ ln(J) I`, `J = det F`.
- Particle-to-grid with quadratic B-splines: `m v_i = Σ_p w_ip [ m_p v_p + (−Δt V_p (4/Δx²) τ_p + m_p C_p)(x_i − x_p) ]`; grid update `v_i ← v_i + Δt g`, `v_i ← v_i (1 − α Δt)`; grid-to-particle `v_p = Σ w v_i`, `C_p = (4/Δx²) Σ w v_i (x_i − x_p)ᵀ`, `x_p += Δt v_p`, `F_p ← (I + Δt C_p) F_p`.
- Contact on grid nodes (table, flat plate, two side plates, spherical probe): remove the velocity component into the tool, with Coulomb friction.
- **Protocol** as the FEM: 0.12 s squeeze (drag 600 s⁻¹), 0.04 s hold, the plate retreats along the measured tin trajectory, then 0.25 s of free recovery. Time step 0.25 Δx / wave speed (about 2×10⁻⁵ s).

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| Δx, particles | grid spacing, particle count | fixed | 2.5 mm, 79,711 |
| R, ρ | radius, density | fixed (ρ is an **estimate**) | 33.5 mm, 55 kg/m³ |
| E, ν | Young's modulus, Poisson ratio | taken from the FEM fit | 38.4 kPa, 0.10 |
| μ_plate, μ_table | friction | taken from the FEM fit | 1.78, 1.75 |
| α | damping rate | **calibrated on 0536+0537 only** (scan around the FEM's 2,806 s⁻¹: score = height RMSE + 0.1 × |recovery-time error|) | 3,508 s⁻¹ |
| probe radius | point load | fixed | 6 mm |

## Results (flat press; SAM 2 truth; common footing)
| Clip | Height RMSE (calibrated α) | with the FEM's α | Plain exponential | 95 % recovery: calibrated / real | Pressed width MPM / real |
| --- | --- | --- | --- | --- | --- |
| 0536 (train) | 3.5 | 3.5 | 5.4 | 36 / 34 ms | 1.114 / 1.077 |
| 0537 (train) | 3.3 | 3.6 | 6.1 | 37 / 39 ms | 1.140 / 1.077 |
| 0538 (**test**) | 2.3 | 2.2 | 3.1 | 27 / 27 ms | 1.043 / 1.043 |
| 0539 (**test**) | 1.9 | 1.8 | 3.4 | 27 / 24 ms | 1.045 / 1.043 |

It beats the plain exponential on all four clips (skill +0.25 to +0.46); the pressed width on the test clips is right to within 0.002×; the recovery time is within 3 ms on the test clips. The MPM's height error is not better than the FEM's (1.9 against 2.3 and 1.7 for the test mean): solver-to-solver differences of about 0.5 points are within the scatter. The calibrated damping fixes the earlier impression that the MPM "recovers too quickly" (a symptom of the wrong release frame, now corrected) only partly: the FEM-damping variant is 6-8 ms quicker than the real ball.

## Other loads (`outputs/mpm_load_{flat,point,side}.mp4`; **predictions, not validated**)
No video of these loads exists to test against. Point probe (6 mm, 45 % of the height): a local dimple at the tip, shoulders stay round. Two side plates (width squeezed 40 %): a rounded cylinder whose height stays at 99 % of rest (ν = 0.1: little bulge). Flat plate to 60 % compression: pancake with a small bulge, smooth recovery. (These loads use instant removal; the tin-retreat input exists only for the flat press.)

## Assumptions and limitations
As the FEM, plus: damping applied on the grid; friction carried over although the contact treatments differ. **No hop.** The 2.5 mm grid is coarse for a 6 mm probe (the dimple spans two cells). MPM adds numerical dissipation and particle noise, and the rendered surface shows particle-scale texture. E and ν were fitted in another solver and absorb its discretisation error; refitting inside MPM would need a differentiable MPM run.

## Run
`./run.sh` (calibration about 3 min, evaluation and videos about 8 min; needs the FEM fit and `.venv-sim`). Code: `src/mpm3d.py` (solver), `src/calibrate_mpm.py` (damping scan on the training clips), `src/run_mpm.py` (evaluation, depth-buffer renderer). Outputs: `results.txt`, `results_mpm.json`, `params_mpm.json`, `alpha_scan.json`, `alpha_scan.png`, `real_vs_mpm_IMG_0536|0538|0539.mp4` (time zero = separation, slowed 8x) and the three `mpm_load_*.mp4`; `results_instant_release.*` are the earlier protocol's results.
