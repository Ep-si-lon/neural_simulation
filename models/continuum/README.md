# Family 3: continuum models (the ball as a solid), built on NVIDIA Warp and PyTorch

The third way to explain the video, and the one the research literature uses: treat the ball as a **volume of elastic material** with physical constants (Young's modulus E, Poisson ratio ν, density ρ) instead of a spring mesh.
Both models use libraries instead of hand-written solvers: [NVIDIA Warp](https://nvidia.github.io/warp/) for the simulation (differentiable, runs on the GPU) and PyTorch for the fitting loop.

| Model | Method | What it is for | Fitted? |
| --- | --- | --- | --- |
| [fem_axisymmetric_warp](fem_axisymmetric_warp/) | finite elements on the 2D slice of the ball, revolved around the vertical axis | the flat-plate press: smooth round ball, fitted E, ν, damping, friction | yes: PyTorch + Warp tape, on 0536+0537 |
| [mpm_3d_warp](mpm_3d_warp/) | 3D material point method (particles + grid), 80,000 particles | an independent solver for the same material, plus point and side loads | no: uses the FEM-fitted material unchanged |

## How they compare with the earlier models (held-out clips 0538 / 0539, height RMSE as % of ball height after release)
| Model | 0538 | 0539 | Note |
| --- | --- | --- | --- |
| Single exponential (baseline) | 3.3 | 3.7 | no physics |
| Two-mass spring (`models/lumped_1d`) | 6.6 | 6.2 | colour tracker data |
| 3D spring mesh, shape fit (`models/mesh_3d`) | 6.1 | 6.0 | colour tracker data |
| **Axisymmetric FEM (fitted)** | **3.2** | **3.3** | SAM 2 data; also reproduces the outline |
| **3D MPM (FEM material, no refit)** | **1.8** | **1.8** | SAM 2 data; solver-to-solver spread is about 1.5 points |

Post-release heights agree between the two trackers to about 2 px, so the comparison is not affected by the tracker change. The continuum models have the physical constants E, ν (stiffness 37 kPa, almost no sideways bulge) that the spring models could not give.

## Why this family
- E, ν and ρ do not depend on the mesh or particle spacing, unlike the spring constants in `models/mesh_3d`.
- The axisymmetric slice makes the side-view silhouette the radial profile of the ball, so the model is fitted to the full tracked outline, not only to the height.
- Fitting uses the whole video: three points along the squeeze, the pressed (hold) outline, and the 0.25 s after release.

## Shared assumptions
- Homogeneous, isotropic, compressible neo-Hookean solid (foam-like, so ν may be small and volume is not conserved).
- Density **ρ = 55 kg/m³, an estimate** (the ball was not weighed accurately; 10 g and 6.7 cm would give 63 kg/m³). Only E/ρ is identified from the video, so E in pascals scales linearly with the assumed density.
- The plate follows the measured compressed height; the squeeze is simulated in 0.12 s with extra numerical drag so it is quasi-static, then the plate is removed instantly at the measured release.
- Damping is mass-proportional (Rayleigh) on the absolute velocity. It gives the overdamped recovery of the real ball and **suppresses the hop**: the hop is not modelled (see `models/mesh_3d` for hop experiments). Physical Kelvin-Voigt viscosity would need time steps around 10⁻⁷ s with this mesh.
- Tin and table are rigid; friction is Coulomb (fitted).

## Environment
These models run in a separate environment, `.venv-sim` (Python 3.13, `requirements-sim.txt`: warp-lang 1.19, torch 2.15 with CUDA 13, sam2). `env_sim.sh` creates it on first use. Tested on an RTX 5060 laptop GPU (Warp and PyTorch both work on its sm_120 architecture).
