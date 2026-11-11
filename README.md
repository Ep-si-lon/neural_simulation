# neural_simulation: learning a soft ball's deformation from video

One foam ball, one steel tin that presses it and is pulled away, filmed at 1080p / 240 fps. From that video I fit physics models of how the ball squashes and recovers, and test them on clips held out of the fit (no refitting). Thirteen models in three families are compared on the same footing.
**The models are physics, not learned**: spring and continuum solvers (hand-written, or NVIDIA Warp) with a handful of physical constants fitted by least squares or Adam (system identification). The only neural network is the **pretrained SAM 2** segmentation model used for tracking (together with a colour-threshold tracker).

```bash
# needs python3, ffmpeg and the four originals in videos/IMG_053{6,7,8,9}.MOV (not in git, ~157 MB)
./run_all.sh              # ~30 min: tracking, the 1D models, 3D mesh and continuum videos, the comparison (saved parameters)
./run_all.sh --fit-3d     # refit the 3D mesh models and the FEM too (each ~10-20 min)
# the continuum models and SAM 2 run in a separate environment (.venv-sim: Warp, PyTorch, SAM 2; created on first use by env_sim.sh; GPU recommended)
```
Every folder under `tracking/`, `models/` and `evaluation/` has its own `README.md` (formulas, parameters, assumptions, limitations, results), `src/`, `outputs/` and `run.sh`. Clips: 0536 and 0537 are training (deep squeezes, 36-41 % of height); 0538 and 0539 are test (shallow squeezes, 62-63 %). Plain-words explanations of the terms: [docs/glossary.md](docs/glossary.md).

## An important correction (read this first)
An earlier version of this repo had a bug in the release instant: it took the **mid-rise frame** (ball already at about 72 % of its height) as the moment the tin lets go. The tin in fact **retreats gradually** (46-121 ms) with the ball riding on it until the ball separates; only the free recovery after separation (about 25-40 ms to 95 % of rest height) belongs to the ball. Every model was therefore started from the wrong state and fitted to look "fast". Consequences: the claim that the real ball snaps back in 1-2 frames was false, the fast-snap experiment chased an artefact, and the early recovery-time study is invalid. Fix: the measured tin trajectory drives a plate in every simulator, time zero is the separation frame, and **all models were refitted on the SAM 2 measurements**. Details and what stays valid: [docs/correction_release_definition.md](docs/correction_release_definition.md). Old outputs are kept in `outputs/archive_v1_instant_release/`.

## What the video taught me
- **Time base:** file timestamps are uneven (2/3 of gaps 1/240 s, 1/3 1/120 s); fitting free-flight arcs gives gravity of about 8.7 m/s² with them against 9.4-25 with a uniform 1/240 s, so the file timestamps are used.
- **The ball hops** (3-8 mm) after separating; part of it may come from friction or suction with the tin, which this video cannot separate from the ball's own elasticity.
- **Shape:** while pressed the outline is a flat-sided cylinder (squareness n about 4); the width grows only 4-8 % while the height drops 37-66 %, so volume is not conserved (foam, not a sealed gas).
- **Tracking:** the colour tracker reads the pressed top edge 4-5 % too high (a reflection on the tin); SAM 2 does not. After release they agree.

## Repository map: one problem, several ways to solve it
```
tracking/        video -> measurements: colour tracker and SAM 2 (ball edges, outline, shape)
models/
  lumped_1d/     Family 1: the ball as one or two vertical bodies
    bounce_recovery/       rigid hop (restitution) + exponential recovery (after the first apex)
    two_mass_spring/       bottom + top mass, nonlinear spring-damper
    fast_snap/             + stiff deep-compression regime
  mesh_3d/       Family 2: 3D mass-spring surface mesh with a pressing tool
    gas_shell/             sealed gas inside a stretchy skin
    foam_core_height_fit/  foam core (radial springs), fit to height / lift / width
    foam_core_shape_fit/   + outline squareness and width over time
    foam_core_no_lift/     hop ignored in the fit
    foam_core_with_lift/   hop included (weight 4)
  continuum/     Family 3: the ball as an elastic solid (E, nu), Warp + PyTorch, SAM 2 data
    fem_axisymmetric_warp/ finite elements on the 2D slice, revolved into a smooth ball
    mpm_3d_warp/           3D material point method, FEM material, point and side loads
evaluation/      model_comparison (all models, every aspect); recovery_time (superseded)
shared/          code several models import (3D engine, scenario runner, renderers, clip preparation)
docs/            assignment PDF, initial plan, the correction, write-up of the first experiments, glossary
```
Family overviews: [lumped_1d](models/lumped_1d/README.md), [mesh_3d](models/mesh_3d/README.md), [continuum](models/continuum/README.md). Every model folder has real-versus-model videos in `outputs/` (time zero = separation, slowed 8x; training clip 0536 and held-out 0538, 0539).

## Results: all models on the same footing ([full comparison](evaluation/model_comparison/README.md))
Height error after separation (RMSE, % of ball height) on the **held-out clips**; skill = 1 − RMSE / RMSE of the plain exponential (3.3 % on the held-out clips), averaged over all four clips:

| Model | Held-out height error | Skill (4 clips) | 95 % recovery (real 27 / 24 ms) | Notes |
| --- | --- | --- | --- | --- |
| fast-snap two-mass | 1.1 % | +0.67 | 24 / 24 | best 1D model |
| foam core, no-lift (mesh) | 1.1 % | +0.71 | 31 / 30 | no hop |
| two-mass spring | 1.6 % | +0.56 | 35 / 34 | |
| **axisymmetric FEM (Warp)** | **1.7 %** | +0.46 | 24 / 24 | E = 38 kPa, ν = 0.10; smooth round ball; reproduces the outline |
| foam core, shape fit (mesh) | 1.9 % | +0.42 | 16 / 16 | recovers too fast |
| foam core, with-lift (mesh) | 2.0 % | +0.40 | 16 / 15 | hop on deep presses |
| **axisymmetric FEM, damping relative to centre of mass ×16** | **1.4 %** | +0.62 | 20 / 20 | lowest height error; keeps a hop (4-8 mm vs real 3-7); 95 % recovery slightly fast on test clips; α chosen on training clips only (hop_scan) |
| **3D MPM (Warp), FEM material** | 2.1 % | +0.38 | 27 / 27 | point and side loads (unvalidated) |
| foam core, height fit (mesh) | 3.2 % | +0.20 | 11 / 10 | closest hop of the meshes |
| 3D gas shell | 3.9 % | 0.00 | 22 / 9 | fit stalled; rings |
| bounce + recovery | not comparable | | | covers only the time after the first hop apex; reproduces the hop |
| axisymmetric FEM, instant release (old protocol) | 3.1 % | +0.05 | 30 / 30 | ablation: the tin retreat is worth 1.4 points |

**Reading it honestly.** After the correction most physics models beat the plain exponential, and the spread among the good ones (1.1-2.1 %) is about the tracker's noise, so they cannot be ranked on height alone. The protocol (driving the measured tin retreat) mattered more than the model choice. The continuum models are not more accurate on height than the 1D models; what they add is physical constants that do not depend on the discretisation, a smooth ball that reproduces the outline, and a route to other loads. Only the spring models and the relative-damping FEM variant produce a hop; the spring models get it right on training clips only.

## Limitations (read before relying on any number)
- **The tin's motion is an input.** The compressed height and the measured tin trajectory come from the video; the models predict the ball's response after separation (and the outline).
- **Only flat top presses were fitted and tested.** The point-probe and side-plate loads (spring engine, MPM) are predictions with no video to test against.
- **No ball mass was measured accurately:** stiffness and damping of the spring models are per unit mass; the continuum models assume 55 kg/m³ (E scales linearly with it). The diameter (6.7 cm) is a rough estimate that sets the pixel scale and the gravity term.
- **Mass-spring parameters depend on the mesh**; the continuum constants should not.
- **No hop in the default continuum models** (mass-proportional damping); the FEM variant with damping relative to the centre of mass (×16) hops 4-8 mm, but E, ν and friction were fitted with absolute damping and only α was rescaled, and its hop starts ~5 ms after separation versus ~20 ms in the video. MPM has no such option yet. Tin friction or suction may add to the real hop and is not modelled.
- **Fit status:** two training clips and two test clips give a rough spread, not a confidence interval; the gas-shell fit never left its starting values; the no-lift fit ended with one stiffness on its bound; mesh fits use two or three starting points and 20-30 optimizer steps.
- **Tracking:** fixed table line (pixel row 740, one camera pose); the cause of the irregular frame gaps is not verified; SAM 2 and the colour tracker agree after release but differ while pressed (the continuum models and the refitted older models use SAM 2).

## Credits
Python, NumPy, SciPy, OpenCV, Matplotlib, FFmpeg; NVIDIA Warp (simulation), PyTorch (fitting), Meta's SAM 2 (`facebook/sam2.1-hiera-tiny`, via Hugging Face) for segmentation. Code and analysis were written with Claude Code (Anthropic's AI assistant); results were checked by running the pipelines.
