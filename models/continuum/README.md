# Family 3: continuum models (the ball as a solid), built on NVIDIA Warp and PyTorch

The third way to explain the video, and the one the research literature uses: treat the ball as a **volume of elastic material** with physical constants (Young's modulus E, Poisson ratio ν, density ρ) instead of a spring mesh.
Both models use libraries instead of hand-written solvers: [NVIDIA Warp](https://nvidia.github.io/warp/) for the simulation (differentiable, GPU) and PyTorch for the fitting loop. Fitted on the SAM 2 measurements with the corrected protocol (the tin retreats along its measured trajectory; see [docs/correction_release_definition.md](../../docs/correction_release_definition.md)).

| Model | Method | What it is for | Fitted? | Held-out height error (0538 / 0539) |
| --- | --- | --- | --- | --- |
| [fem_axisymmetric_warp](fem_axisymmetric_warp/) | finite elements on the 2D slice, revolved around the vertical axis | the flat-plate press: smooth round ball; E = 38 kPa, ν = 0.10, damping, friction | yes (PyTorch + Warp tape, on 0536+0537) | 1.9 / 1.4 % |
| [mpm_3d_warp](mpm_3d_warp/) | 3D material point method, 80,000 particles | an independent solver for the same material, plus point and side loads | no: FEM material; damping calibrated on the training clips | 2.3 / 1.9 % |

Plain exponential: 3.1 / 3.4 %. **What this family adds is not a smaller height error** (the 1D and mesh models reach 1.1-2.0 % too); it is physical constants that do not depend on the discretisation, a smooth round ball that reproduces the outline, and a model that extends to loads other than the flat press (unvalidated). See [evaluation/model_comparison](../../evaluation/model_comparison/README.md).

## Shared assumptions
- Homogeneous, isotropic, compressible neo-Hookean solid (foam-like: ν is small and volume is not conserved).
- **Density ρ = 55 kg/m³, an estimate** (10 g and 6.7 cm would give 63). Only E/ρ is identified from the video; E in pascals scales linearly with the assumed density.
- The plate follows the measured compressed height, then the measured tin retreat; the squeeze is simulated in 0.12 s with extra numerical drag so it is quasi-static.
- Damping is mass-proportional (Rayleigh) on the absolute velocity: it gives the overdamped recovery and **suppresses the hop**. Damping relative to the centre of mass was tested and does not fix it (it hops 25-356 mm, and recovers too fast when strong enough to tame the hop; see the FEM README). Physical Kelvin-Voigt viscosity would need implicit stepping or time steps around 10⁻⁷ s with this mesh.
- Tin and table are rigid; friction is Coulomb (fitted).

## Environment
A separate environment, `.venv-sim` (Python 3.13, `requirements-sim.txt`: warp-lang 1.19, torch 2.15 with CUDA 13, sam2); `env_sim.sh` creates it on first use and sets `TRACKER=sam2`. Tested on an RTX 5060 laptop GPU.
