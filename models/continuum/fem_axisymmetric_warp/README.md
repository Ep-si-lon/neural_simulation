# Axisymmetric FEM ball (NVIDIA Warp + PyTorch)

**Idea.** A flat plate pressing a round ball is symmetric around the vertical axis, so one 2D slice (a half disc in the (r, z) plane) revolved around the axis is the whole ball. The slice is meshed with 938 nodes and 1,778 triangles (about 1.5 mm), and the side-view silhouette of the ball *is* the radial profile of the slice. The model is a hyperelastic solid with physical constants, fitted to the tracked outlines with gradients through the whole simulation.

## Formulas
Reference position `X = (R, Z)`, current position `x = (r, z)`; the hoop direction is analytic.
- Deformation: in-plane `F2 = Ds · Dm⁻¹` (current over reference triangle edges), hoop stretch `λθ = r / R`, volume ratio `J = det(F2) · λθ`.
- Compressible neo-Hookean Cauchy stress: `σ = (μ/J)(B − I) + (λ ln J / J) I`, `B = F Fᵀ` (with `Bθθ = λθ²`).
- Lamé constants: `μ = E / (2(1+ν))`, `λ = E ν / ((1+ν)(1−2ν))`.
- Nodal forces: `f_a = −∫ (σ · ∇N_a + σθθ N_a / r e_r) dV`, element volume `dV = 2π r A`; lumped mass `m_a = ρ ∫ 2π r dA / 3`.
- Dynamics (explicit): `M ẍ = f − α M ẋ − M g e_z`, symplectic Euler, time step 0.18 × (1.5 mm / wave speed) and at most 1.5×10⁻⁵ s.
- Plate and table: exact kinematic constraints (nodes projected onto the plate or table), Coulomb friction limited to `μ · a_n · Δt` with `a_n` the estimated normal reaction.
- Squeeze: plate ramps linearly over 0.12 s with extra numerical drag `γ = 600 s⁻¹` (quasi-static), holds 0.04 s, then is removed; release is simulated for 0.25 s with the fitted damping `α`.
- Loss (per clip): Huber distance between simulated and tracked **outline widths** (42 levels from top to bottom) and height, at 3 points along the squeeze, the hold, and every 3rd frame after release.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| R | ball radius | fixed (6.7 cm diameter, rough) | 33.5 mm |
| ρ | density | fixed (**estimate**, not weighed accurately) | 55 kg/m³ |
| g, γ, T_sq, T_hold | gravity, squeeze drag, durations | fixed | 9.81, 600 s⁻¹, 0.12 s, 0.04 s |
| h_c, release time, outlines | pressed height, release frame, widths at 48 levels | measured per clip (SAM 2) | — |
| E | Young's modulus | fitted | **36.7 kPa** (E/ρ = 668 m²/s²) |
| ν | Poisson ratio | fitted | **0.068** (foam: little sideways bulge) |
| α | Rayleigh mass-proportional damping rate | fitted | 2450 s⁻¹ |
| μ_plate, μ_table | Coulomb friction | fitted | 1.03, 1.73 |

E scales linearly with the assumed density (only E/ρ is identified from the video). Fitted with Adam in PyTorch on 0536+0537 (45 steps, sigmoid bounds); gradients from Warp's tape were checked against finite differences (agreement to 3-4 digits).

## Assumptions
Axisymmetric press; homogeneous isotropic compressible neo-Hookean foam; plate removed instantly at the measured release; tin and table rigid; the squeeze is quasi-static.

## Limitations
- **No hop.** Mass-proportional damping gives the overdamped recovery of the real ball but suppresses the hop (lift 0 mm; real 3-8 mm). Physical Kelvin-Voigt viscosity would need time steps around 10⁻⁷ s on this mesh. Friction 1.0-1.7 is large, which may stand in for the tin's suction or sticking.
- Axisymmetric only: flat top press. Point and side loads need the 3D model (`../mpm_3d_warp`).
- Pressed width is too wide on the deep training clips (model 1.12-1.14×, tracked 1.07×); on the test clips it is close (1.05×, tracked 1.04×).
- E depends on the density estimate; ν and friction are weakly separated from a single side view.
- Element inversion is guarded only by a clamp on J; the 75 % compression range was not tested.
- Mass-proportional damping also damps rigid-body motion, which is why it is not a physical viscosity.

## Results (train 0536+0537, test 0538+0539; SAM 2 measurements)
| Clip | Height RMSE (% of ball height) | Plain exponential | Outline RMSE (% of ball width) | 95 % recovery: model / real |
| --- | --- | --- | --- | --- |
| 0536 (train) | 5.4 | 5.6 | 7.0 | 37 / 37 ms |
| 0537 (train) | 5.9 | 5.8 | 6.5 | 42 / 42 ms |
| 0538 (**test**) | 3.2 | 3.3 | 4.9 | 33 / 29 ms |
| 0539 (**test**) | 3.3 | 3.7 | 5.5 | 38 / 25 ms |

This is the first physics model in this repo that reaches the plain-exponential baseline on held-out height (the spring-mesh models were at 6-8 %). It does so while also reproducing the outline, which the baseline cannot.
The same fit on the colour-tracker data (pressed height biased high, see `../../../tracking/README.md`) gave E = 35.4 kPa, ν = 0.078, α = 2200 and test height errors 4.2 / 3.1 % (`outputs/results_colour_tracker.txt`).

## Run
`./run.sh` (fit about 8 min on a laptop GPU, then videos). Code: `src/mesh.py` (half-disc mesh), `src/fem_axi.py` (Warp kernels), `src/fit_fem.py` (PyTorch fit, evaluation), `src/render_fem.py` (revolved smooth surface). Needs `.venv-sim` and `tracking/run_sam2.sh`. `./render.sh` re-renders the videos.
**Videos** (`outputs/real_vs_fem_IMG_0536|0538|0539.mp4`): real clip, FEM side view, FEM oblique view on one clock (t = 0 at release, slowed 8×). 0536 is a training clip, 0538 and 0539 are held out. Other outputs: `results.txt`, `params_fem.json`.
