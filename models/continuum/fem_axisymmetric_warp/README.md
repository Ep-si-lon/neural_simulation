# Axisymmetric FEM ball (NVIDIA Warp + PyTorch)

**Idea.** A flat plate pressing a round ball is symmetric around the vertical axis, so one 2D slice (a half disc in the (r, z) plane) revolved around the axis is the whole ball. The slice is meshed with 938 nodes and 1,778 triangles (about 1.5 mm), and the side-view silhouette of the ball *is* the radial profile of the slice. The model is a hyperelastic solid with physical constants, fitted to the tracked outlines with gradients through the whole simulation.

## Formulas
Reference position `X = (R, Z)`, current position `x = (r, z)`; the hoop direction is analytic.
- Deformation: in-plane `F2 = Ds · Dm⁻¹`, hoop stretch `λθ = r / R`, volume ratio `J = det(F2) · λθ`.
- Compressible neo-Hookean Cauchy stress: `σ = (μ/J)(B − I) + (λ ln J / J) I`, `B = F Fᵀ`; `μ = E / (2(1+ν))`, `λ = E ν / ((1+ν)(1−2ν))`.
- Nodal forces `f_a = −∫ (σ · ∇N_a + σθθ N_a / r e_r) dV`, `dV = 2π r A`; lumped mass `m_a = ρ ∫ 2π r dA / 3`.
- Dynamics (explicit): `M ẍ = f − α M ẋ − M g e_z`, symplectic Euler, step 0.18 × (1.5 mm / wave speed), at most 1.5×10⁻⁵ s.
- Plate and table: exact kinematic constraints, Coulomb friction limited to `μ · a_n · Δt`.
- **Protocol:** plate ramps down over 0.12 s with extra numerical drag (quasi-static), holds 0.04 s, then **retreats along the measured tin trajectory** (46-121 ms) until the separation frame; then it is removed and the free recovery is simulated for 0.25 s.
- Loss (per clip): Huber distance between simulated and tracked outline widths (42 levels) and height, at 3 points along the squeeze, the hold and every 3rd frame after separation.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| R | ball radius | fixed (6.7 cm diameter, rough) | 33.5 mm |
| ρ | density | fixed (**estimate**) | 55 kg/m³ |
| g, γ, T_sq, T_hold | gravity, squeeze drag, durations | fixed | 9.81, 600 s⁻¹, 0.12 s, 0.04 s |
| h_c, tin trajectory, separation frame, outlines | per clip | measured (SAM 2) | — |
| E | Young's modulus | fitted | **38.4 kPa** (E/ρ = 697 m²/s²) |
| ν | Poisson ratio | fitted | **0.10** (foam: little sideways bulge) |
| α | mass-proportional damping rate | fitted | 2,806 s⁻¹ |
| μ_plate, μ_table | Coulomb friction | fitted | 1.78, 1.75 |

E scales linearly with the assumed density. Fitted with Adam in PyTorch on 0536+0537 (45 steps, sigmoid bounds); Warp's tape gradients agree with finite differences to 3-4 digits.

## Assumptions and limitations
- **No hop.** Mass-proportional damping on the absolute velocity suppresses it. Damping only the motion relative to the centre of mass keeps the hop but gives 126-356 mm at the fitted strength and still 25-43 mm at 8x the strength, with recovery twice as fast as the real ball (`src/hop_experiment.py`, `outputs/hop_experiment.txt`): the compressed foam stores far more energy than the real ball releases as a hop, so a single damping number cannot match both. The proper remedy is internal viscoelastic (Kelvin-Voigt) damping, which needs implicit time stepping or time steps near 10⁻⁷ s on this mesh. Friction 1.8 is large and may stand in for tin suction.
- Axisymmetric: flat top press only (point and side loads need `../mpm_3d_warp`).
- **Pressed width too wide on the deep presses** (1.13 / 1.16× against 1.077×); close on the shallow ones (1.053 / 1.055× against 1.043×).
- Tin trajectory (measured) is an input; E depends on the density estimate; ν and friction are weakly separated from a single side view.

## Results (SAM 2 truth; common footing; train 0536+0537, test 0538+0539)
| Clip | Height RMSE (% of ball height) | Plain exponential | Same FEM, instant release (old protocol) | Outline RMSE (% of ball width) | 95 % recovery: model / real |
| --- | --- | --- | --- | --- | --- |
| 0536 (train) | 3.2 | 5.4 | 5.2 | 7.0 | 30 / 34 ms |
| 0537 (train) | 3.2 | 6.1 | 5.7 | 6.5 | 31 / 39 ms |
| 0538 (**test**) | 1.9 | 3.1 | 3.1 | 4.8 | 24 / 27 ms |
| 0539 (**test**) | 1.4 | 3.4 | 3.1 | 5.4 | 24 / 24 ms |

It beats the plain exponential on all four clips (skill +0.39 to +0.58), reproduces the outline, and matches the test recovery times. **Ablation:** with the same model but the tin removed instantly at the separation frame (the earlier protocol, fitted separately: `outputs/params_fem_instant_release.json`) the height error is the exponential's (3.1 %); the measured tin retreat is worth about 1.4 points, more than the difference between most models.

## Run
`./run.sh` (fit about 10 min on a laptop GPU, then videos). Code: `src/mesh.py`, `src/fem_axi.py` (Warp kernels), `src/fit_fem.py` (PyTorch fit, evaluation; `FEM_PROTOCOL=instant` for the old protocol), `src/render_fem.py` (revolved smooth surface). Needs `.venv-sim` and `tracking/run_sam2.sh`. `./render.sh` re-renders the videos.
**Videos** (`outputs/real_vs_fem_IMG_0536|0538|0539.mp4`): real clip, FEM side view, FEM oblique view on one clock (time zero = separation, slowed 8x). 0536 is a training clip. Other outputs: `results.txt`, `params_fem.json`; `results_instant_release.txt`, `results_colour_tracker.txt` are earlier runs.
