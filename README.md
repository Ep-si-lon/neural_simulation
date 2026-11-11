# neural_simulation: learning a soft ball's deformation from video

One foam ball, one steel tin that presses it and is pulled away, filmed at 1080p / 240 fps. From that video I fit simple physics models of how the ball squashes, recovers and hops, and test them on clips held out of the fit (no refitting).
**The models are physics, not learned**: spring and continuum solvers (hand-written, or NVIDIA Warp) with a handful of physical constants fitted by least squares or Adam (system identification). The only neural network is the **pretrained SAM 2** segmentation model, used for tracking (together with a colour-threshold tracker).

```bash
# needs python3, ffmpeg and the four originals in videos/IMG_053{6,7,8,9}.MOV (not in git, ~157 MB)
./run_all.sh              # ~30 min: tracking, the 1D models, 3D mesh and continuum videos and the evaluation from the saved parameters
./run_all.sh --fit-3d     # refit all five 3D mesh models and the FEM (each ~10-20 min) instead of reusing the saved parameters
# the continuum models and SAM 2 run in a separate environment (.venv-sim: Warp, PyTorch, SAM 2; created on first use by env_sim.sh; needs a GPU or a lot of patience)
```

Every folder under `tracking/`, `models/` and `evaluation/` has its own `README.md` (formulas, parameters, assumptions, limitations, results), `src/`, `outputs/` and `run.sh`.

Clips: 0536 and 0537 are training (deep squeezes, 36-41 % of height); 0538 and 0539 are test (shallow squeezes, 67 %).
Plain-words explanations of the terms used here: [docs/glossary.md](docs/glossary.md).

## What the video taught me

- **Time base:** the files have irregular frame gaps (2/3 are 1/240 s, 1/3 are 1/120 s). Fitting free-flight arcs gives gravity of about 8.7 m/s² with the file timestamps against 9.4-25 with a uniform 1/240 s, so the **file timestamps are used**.
- **The "ring" is a hop, not a vibration:** after release the height barely oscillates (it recovers smoothly). The visible bouncing is the whole ball leaving the table by 3-8 mm. Part of it may come from friction or suction with the tin, which this video cannot separate from the ball's own elasticity.
- **Shape:** the outline is a flat-sided cylinder while pressed (squareness n of 4-6) and an ellipse (n = 2) again within about 10 frames. Width changes only 1-10 % while height drops 33-64 %, so volume is not conserved (foam, not a sealed gas).

## Repository map: one problem, several ways to solve it

```
tracking/        video -> measurements: colour tracker and SAM 2 (ball edges, outline, shape)   shared by every model
models/
  lumped_1d/     Family 1: the ball as one or two vertical bodies
    bounce_recovery/     rigid hop (restitution) + exponential height recovery            works on 3 of 4 clips
    two_mass_spring/     bottom + top mass, nonlinear spring-damper                       loses to a plain exponential
    fast_snap/           + stiff deep-compression regime                                  no improvement
  mesh_3d/       Family 2: 3D mass-spring surface mesh with a pressing tool (no solver library)
    gas_shell/           sealed gas inside a stretchy skin                                bulges, rings: abandoned
    foam_core_height_fit/  foam core (radial springs), fit to height/lift/width           first good 3D fit
    foam_core_shape_fit/   + outline squareness and width over time                       matches shape, no hop
    foam_core_no_lift/     hop ignored in the fit                                         hops far too high
    foam_core_with_lift/   hop included (weight 4)                                        deep-squeeze hops match
  continuum/     Family 3: the ball as an elastic solid (E, nu), Warp + PyTorch, fitted on SAM 2 outlines
    fem_axisymmetric_warp/ finite elements on the 2D slice, revolved into a smooth ball       matches the baseline, reproduces the outline
    mpm_3d_warp/           3D material point method, FEM material unchanged, point and side loads  beats the baseline (solver spread ~1.5 points)
evaluation/      recovery_time (cross-model comparison)
shared/          code several models import (3D engine, scenario runner, renderers, clip preparation)
docs/            assignment PDF, initial plan, write-up of the 1D experiments, glossary
```

Family overviews: [models/lumped_1d](models/lumped_1d/README.md), [models/mesh_3d](models/mesh_3d/README.md), [models/continuum](models/continuum/README.md), [evaluation](evaluation/README.md). Every model folder has real-versus-model videos in its `outputs/` (3D models: training clip 0536 and held-out 0538, 0539 on one clock, t = 0 at release; each also has `render.sh` to re-render them in about a minute).

## Results

**1. [Bounce + recovery model](models/lumped_1d/bounce_recovery/README.md)** (hops with restitution, then exponential height recovery; [models/lumped_1d/bounce_recovery](models/lumped_1d/bounce_recovery/README.md)): restitution e = 0.66-0.71, recovery time constant 44-59 ms, table dwell 8-14 ms. Leave-one-clip-out, it beats both baselines on 3 of 4 clips (fails on 0538).

**2. [Two-mass squeeze + release simulation](models/lumped_1d/two_mass_spring/README.md):** stiffness k = 11-16 x 10^3 s^-2 per unit mass, damping ratio 2.6-3.2 (strongly overdamped). Height error 6-8 % against 4-6 % for a plain exponential, so **it loses to the baseline on all four clips**. The real ball snaps back within 1-2 frames.

**3. [3D foam-core ball](models/mesh_3d/README.md)** (162 nodes: edge springs `ks`, bending springs `kb`, radial foam-core springs `kr`, damping `cd`): the fitted shape matches the measured width within 0.5-1.6 % and squeezes with a slight bulge; held-out height error is 6-8 %, again no better than a plain exponential. Fitted values (per unit mass):

| Fit | ks | kb | kr | cd |
| --- | --- | --- | --- | --- |
| with hop term (`foam_core_with_lift`) | 127 | 276 | 1000 | 23 |
| without hop term (`foam_core_no_lift`) | 111 | 951 | 2577 | 34.5 |

**4. [Time to regain shape](evaluation/recovery_time/README.md) (hops ignored), 95 % of rest height, ms:**

| Test clip | Real | Exponential | 1-DOF spring | Fast+slow exp | 3D foam |
| --- | --- | --- | --- | --- | --- |
| 0538 | 25 | 26 | 26 | 28 | 22 |
| 0539 | 13 | 26 | 26 | 27 | 22 |

Models are within -3 to +14 ms. Two clips pressed equally deep differ by 12 ms in reality, so **this test cannot separate the models**.

**5. [Hop height](models/mesh_3d/foam_core_with_lift/README.md) (mm):** real 7.0, 7.4 (train) and 3.6, 5.2 (test). Without the hop term the model overshoots (50-63 mm after deep squeezes); with it, deep-squeeze hops match (5.9, 8.9 mm) but the shallow-squeeze test clips get no hop (0.0 mm).

**6. [Continuum models](models/continuum/README.md) (Warp + PyTorch, SAM 2 measurements):** an axisymmetric finite-element model fitted on 0536+0537 gives E = 36.7 kPa (for an assumed density of 55 kg/m3), Poisson ratio 0.068 (foam: almost no sideways bulge), damping 2450 s^-1. On the held-out clips its height error is 3.2 % and 3.3 % against 3.3 % and 3.7 % for a plain exponential, and it also reproduces the outline (4.9-5.5 % of the ball width). A 3D material-point model with the **same material, nothing refitted**, gets 1.8 % on both held-out clips and predicts the pressed width within 0.004x; its point-probe and side-plate loads are predictions only. This is the first family here that reaches the baseline, and the first with a smooth round ball ([FEM videos](models/continuum/fem_axisymmetric_warp/outputs/), [MPM videos](models/continuum/mpm_3d_warp/outputs/)).

## Limitations (read these before relying on any number)

- **The press is an input.** The compressed height and release time come from the video; the models predict what happens after release (and the shape under the loads above). The 2D squeeze demos replay the measured tin-driven height before release.
- **Only top-down flat presses were fitted.** The simulator also supports a point probe and side plates, but no video of those loads exists to test against.
- **No ball mass was measured**, so stiffness and damping are per unit mass; diameter (6.7 cm) is a rough estimate that sets the pixel scale and the gravity term.
- **Mass-spring parameters depend on the mesh.** A finer mesh would change `ks`, `kb`, `kr`; a finite-element model with Young's modulus would not.
- **Tin interaction is mixed into the results.** Friction or suction from the tin may add to the hop and speed up the first frames after release; the tin itself is not tracked.
- **Fit quality:** the spring-based models (families 1 and 2) do not beat a plain exponential on held-out height error; the continuum models reach it (FEM) or beat it (MPM, but solver-to-solver differences are about 1.5 points); the 3D mesh optimizer sometimes stalled at its starting point; four clips give a rough spread, not a confidence interval.
- **Hop:** only the spring-mesh experiments model it; the continuum models use mass-proportional damping, which gives the overdamped recovery and suppresses the hop.
- **Density is an estimate** (55 kg/m3 for 10 g and 6.7 cm); Young's modulus scales linearly with it.
- **Tracker bias in the earlier models:** the colour tracker reads the pressed top edge about 16-20 px (4-5 %) too high because of a reflection on the tin's underside; SAM 2 does not (see [tracking](tracking/README.md)). The continuum models use SAM 2; the earlier lumped and mesh models were fitted on the colour data (release-phase targets unaffected, compressed height too high) and were not refitted.
- **Tracking:** fixed colour threshold, table line fixed at pixel row 740 (one camera pose), timestamps are from the file and the cause of the irregular frame gaps is not verified. I spot-checked tracks by plot and frames, not every debug frame.

## Credits

Python, NumPy, SciPy, OpenCV, Matplotlib, FFmpeg; NVIDIA Warp (simulation), PyTorch (fitting), Meta's SAM 2 (`facebook/sam2.1-hiera-tiny`, via Hugging Face) for segmentation. Code and analysis were written with Claude Code (Anthropic's AI assistant); results were checked by running the pipeline.
