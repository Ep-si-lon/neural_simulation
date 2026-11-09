# neural_simulation: learning a soft ball's deformation from video

One foam ball, one steel tin that presses it and is pulled away, filmed at 1080p / 240 fps. From that video I fit simple physics models of how the ball squashes, recovers and hops, and test them on clips held out of the fit (no refitting).
**No neural networks are used**: tracking is colour thresholding plus curve fits, models are hand-written physics, and fitting is nonlinear least squares (system identification).

```bash
# needs python3, ffmpeg and the four originals in videos/IMG_053{6,7,8,9}.MOV (not in git, ~157 MB)
./run_all.sh              # ~20 min: tracking, the three 1D models, evaluations with the saved 3D parameters, demo videos
./run_all.sh --fit-3d     # + refit all five 3D models (each ~10-20 min)
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
tracking/        video -> measurements (ball edges, outline, shape)                    shared by every model
models/
  lumped_1d/     Family 1: the ball as one or two vertical bodies
    bounce_recovery/     rigid hop (restitution) + exponential height recovery            works on 3 of 4 clips
    two_mass_spring/     bottom + top mass, nonlinear spring-damper                       loses to a plain exponential
    fast_snap/           + stiff deep-compression regime                                  no improvement
  mesh_3d/       Family 2: 3D mass-spring surface mesh with a pressing tool
    gas_shell/           sealed gas inside a stretchy skin                                bulges, rings: abandoned
    foam_core_height_fit/  foam core (radial springs), fit to height/lift/width           first good 3D fit
    foam_core_shape_fit/   + outline squareness and width over time                       matches shape, no hop
    foam_core_no_lift/     hop ignored in the fit                                         hops far too high
    foam_core_with_lift/   hop included (weight 4)                                        deep-squeeze hops match
evaluation/      recovery_time, hop_height, load_cases (flat / point / side / 75 %), real_vs_model
shared/          code several models import (3D engine, scenario runner, renderers, clip preparation)
docs/            assignment PDF, initial plan, write-up of the 1D experiments, glossary
```

Family overviews: [models/lumped_1d](models/lumped_1d/README.md), [models/mesh_3d](models/mesh_3d/README.md), [evaluation](evaluation/README.md). Video to share with the team: [evaluation/real_vs_model/outputs](evaluation/real_vs_model/outputs/).

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

**5. [Hop height](evaluation/hop_height/README.md) (mm):** real 7.0, 7.4 (train) and 3.6, 5.2 (test). Without the hop term the model overshoots (50-63 mm after deep squeezes); with it, deep-squeeze hops match (5.9, 8.9 mm) but the shallow-squeeze test clips get no hop (0.0 mm).

**6. [Other loads](evaluation/load_cases/README.md)** (predictions from parameters fitted on flat top presses only; not validated): `evaluation/load_cases/outputs/with_lift/lift_{flat,point,side}.mp4` (flat on top, point force on top, two flat plates from the sides) and `deep_withlift.mp4` (same folder) (75 % press, outside the training range, mesh crumples).

## Limitations (read these before relying on any number)

- **The press is an input.** The compressed height and release time come from the video; the models predict what happens after release (and the shape under the loads above). The 2D squeeze demos replay the measured tin-driven height before release.
- **Not validated beyond top-down flat presses.** The point-force and side-plate videos are extrapolations.
- **No ball mass was measured**, so stiffness and damping are per unit mass; diameter (6.7 cm) is a rough estimate that sets the pixel scale and the gravity term.
- **Mass-spring parameters depend on the mesh.** A finer mesh would change `ks`, `kb`, `kr`; a finite-element model with Young's modulus would not.
- **Tin interaction is mixed into the results.** Friction or suction from the tin may add to the hop and speed up the first frames after release; the tin itself is not tracked.
- **Fit quality:** none of the physics models beats a plain exponential on held-out height error; the 3D model's optimizer sometimes stalled at its starting point; four clips give a rough spread, not a confidence interval.
- **Tracking:** fixed colour threshold, table line fixed at pixel row 740 (one camera pose), timestamps are from the file and the cause of the irregular frame gaps is not verified. I spot-checked tracks by plot and frames, not every debug frame.

## Credits

Python, NumPy, SciPy, OpenCV, Matplotlib, FFmpeg. Code and analysis were written with Claude Code (Anthropic's AI assistant); results were checked by running the pipeline.
