# 3D material point method (MPM) ball, NVIDIA Warp

**Idea.** A second, independent solver for the same material. The ball is a cloud of 79,711 particles (2×2×2 per 2.5 mm grid cell, small fixed jitter) carrying mass, velocity and deformation; each step the particles pass momentum to a fixed background grid, the physics runs on the grid, and the result is passed back (MLS-MPM with APIC transfers). There is no mesh to fold, so large squeezes and contacts are easier, and the same code handles any load in 3D.
**Nothing is refitted here**: the material (E, ν, damping, friction) comes from the axisymmetric FEM fit (`../fem_axisymmetric_warp/outputs/params_fem.json`). So the MPM is a test of whether that material, in a different solver, still reproduces the real clips, and a way to predict loads the axisymmetric model cannot represent.

## Formulas
- Kirchhoff stress (compressible neo-Hookean): `τ = μ (F Fᵀ − I) + λ ln(J) I`, `μ = E/(2(1+ν))`, `λ = Eν/((1+ν)(1−2ν))`, `J = det F`.
- Particle-to-grid with quadratic B-splines: `m v_i = Σ_p w_ip [ m_p v_p + (−Δt V_p (4/Δx²) τ_p + m_p C_p)(x_i − x_p) ]`; grid update `v_i ← v_i + Δt g`, then `v_i ← v_i (1 − α Δt)` (Rayleigh damping); grid-to-particle: `v_p = Σ w v_i`, `C_p = (4/Δx²) Σ w v_i (x_i − x_p)ᵀ`, `x_p += Δt v_p`, `F_p ← (I + Δt C_p) F_p`.
- Contact on grid nodes (table, flat plate, two side plates, spherical probe): remove the velocity component into the tool, with Coulomb friction limited by that component.
- Same schedule as the FEM: 0.12 s squeeze ramp (drag 600 s⁻¹), 0.04 s hold, tool removed at release, 0.25 s release simulated. Time step 0.25 Δx / wave speed (about 2×10⁻⁵ s).

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| Δx, particles | grid spacing, particle count | fixed | 2.5 mm, 79,711 |
| R, ρ | radius, density | fixed (ρ is an **estimate**) | 33.5 mm, 55 kg/m³ |
| E, ν, α | Young's modulus, Poisson ratio, damping rate | **taken from the FEM fit** | 36.7 kPa, 0.068, 2450 s⁻¹ |
| μ_plate, μ_table | friction | taken from the FEM fit | 1.02, 1.73 |
| pressed height, release time | per clip | measured (SAM 2) | — |
| probe radius | point load | fixed | 6 mm |

## Results (flat press, material from the FEM fit, no refit; SAM 2 measurements)
| Clip | Height RMSE | Plain exponential | 95 % recovery MPM / real | Pressed width MPM / real |
| --- | --- | --- | --- | --- |
| 0536 (FEM train) | 3.4 % | 5.6 % | 29 / 37 ms | 1.103× / 1.077× |
| 0537 (FEM train) | 3.4 % | 5.8 % | 29 / 42 ms | 1.127× / 1.072× |
| 0538 (test) | **1.8 %** | 3.3 % | 25 / 29 ms | 1.039× / 1.043× |
| 0539 (test) | **1.8 %** | 3.7 % | 29 / 25 ms | 1.041× / 1.038× |

**Read this carefully.** The MPM's height error is *lower* than the FEM's own (1.8 % against 3.2-3.3 % on the test clips) with identical constants. That is a difference between solvers and discretisations (grid dissipation, height measured from particle extents plus half a spacing, the way the plate meets particles versus nodes), not evidence that MPM is the better physics. The solver-to-solver spread of about 1.5 points is the same size as the model error, so differences of that size should not be over-interpreted. What the table does show: the material identified from two clips predicts the other two within about 2 % of the ball height in two different solvers, and the pressed width matches on the test clips.

## Other loads (`outputs/mpm_load_{flat,point,side}.mp4`; **predictions, not validated**)
No video of these loads exists to test against.
- **Point probe** (6 mm, pressed 45 % of the height): local dimple at the tip that spreads over the top; the shoulders stay round; the overall height drops by 12 mm.
- **Two side plates** (width squeezed 40 %): the ball becomes a rounded cylinder; its height stays at 99 % of rest (ν = 0.07: the foam hardly bulges, volume is not conserved).
- **Flat plate to 60 % compression**: pancake with a small bulge, smooth recovery.

## Assumptions
Same as the FEM (homogeneous isotropic neo-Hookean foam; ρ = 55 kg/m³ estimate; rigid tools; plate removed instantly at the measured release) plus: Rayleigh damping applied on the grid velocity; friction coefficients carried over unchanged although the FEM and MPM contact treatments differ.

## Limitations
- **No hop** (mass-proportional damping, as in the FEM).
- The 2.5 mm grid is coarse for a 6 mm probe: the dimple spans only a couple of cells.
- MPM adds numerical dissipation and particle noise; the rendered surface shows particle-scale texture.
- Parameters (E, ν) were fitted in another solver, so they absorb that solver's discretisation error; refitting inside MPM would need a differentiable MPM run (about 80,000 particles per step).
- Load videos other than the flat press are unvalidated extrapolations. E depends on the density estimate.

## Run
`./run.sh` (about 8 min on a laptop GPU; needs the FEM fit and `.venv-sim`). Code: `src/mpm3d.py` (solver), `src/run_mpm.py` (evaluation, renderer with a depth buffer). Outputs: `results.txt`, `results_mpm.json`, `real_vs_mpm_IMG_0536|0538|0539.mp4` (real clip, MPM side view, MPM oblique view on one clock, t = 0 at release, slowed 8×) and the three `mpm_load_*.mp4`. `results_colour_tracker.txt` is the same run with the earlier colour-tracker material.
