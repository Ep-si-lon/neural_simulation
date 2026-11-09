# Squishy Ball: Deformation Model from Video — Procedure and Reasons

Nov 8, 2026 · @Dheeraj

## Goal and grading

The assignment (Dirac Robotics, Research Engineer Intern, 3 days) asks for a simple 3D model of one soft object that is fitted from video of you squishing and releasing it, then tested on a fresh instance of the same interaction. Everything below is chosen to serve three stated grading criteria.

- **Technical understanding:** you can explain each assumption and what the model cannot capture.
- **How visual observations inform the model:** the parameters must come from measurements in the video, not from a replay of the recorded motion.
- **Reproducibility:** someone else must be able to rerun it from the repo.

The assignment says clear reasoning and honest limitations matter more than visual polish, and 3D reconstruction is not assessed, so a simple geometric proxy is enough.

Part 01 (reading 3D Gaussian Splatting and Hybrid Particle-Voxel Dynamics) has nothing to submit, but the follow-up interview covers both papers and your practical work.

## What your clips show

The ball rings after release: it overshoots its rest height, oscillates for 3–4 cycles at roughly 20 Hz, and settles within about 0.25 s. That is why the model must be second order. These are rough numbers from a low-resolution first pass; the full-resolution tracker will replace them.

| Observation | Evidence | Consequence |
| --- | --- | --- |
| Setup is a steel tin pressed on the ball by hand, then pulled away | Contact sheets of all six clips | The first \~8–10 frames of the rise are driven by your hand, not by the ball |
| Overshoot of about 5–10% of ball height, 3–4 cycles | Top-edge traces in all four 240 fps clips | A first-order model cannot overshoot, so use a damped oscillator |
| Ring period about 10–12 frames at 240 fps (45–50 ms) | 240 fps clips (0536–0539) | Timing base is consistent across clips |
| Ring period about 6 frames at 120 fps (50 ms) | First two 4K clips (0531, 0532) | Two different frame rates give the same period in seconds, which supports Δt = 1/240 s |
| Frame timestamps alternate 1/24 s and 2/24 s (about 18 fps average) | ffprobe on the four 240 fps clips | The editor retimed the clips; use frame index, not timestamps |
| No duplicated frames | Frame-difference check on all four clips | Each file frame is a distinct captured frame |
| Ball rests about 3% lower after release | The two 4K clips only; not yet checked in the 240 fps clips | May be slow foam creep or a shifted ball; test with a creep term |
| Ruler visible, but behind the ball | 240 fps clips | Reads slightly small at the ball's plane; use it only as a cross-check |

## Decisions and reasons

Each choice is marked MUST (skipping it makes the result wrong or fails the assignment) or SHOULD (it makes the result stronger but the work is still valid without it).

| # | Decision | Why | Level |
| --- | --- | --- | --- |
| 1 | Use one ball and one tin for every trial | The assignment tests a fresh instance of the same interaction, so the object and interaction must stay fixed | MUST |
| 2 | Time base is 1/240 s per frame, counted by frame index | Every fitted rate scales with it. The file timestamps are editor retiming artifacts, and the 120 fps and 240 fps clips agree on a 50 ms ring period | MUST |
| 3 | Scale from the ball's measured real diameter; ruler only as a cross-check | A guessed diameter would make every length wrong. The ruler sits behind the ball, so it reads small | MUST for results in mm; the fit itself does not need it |
| 4 | Track the ball's top edge, bottom edge and width at full 1080p with subpixel edges | The ring is only a few pixels, so low resolution blurs it. The bottom edge shows whether the ball lifts off the table | MUST |
| 5 | Cut the mask at the table line | The ball's yellow reflection on the table merged into the ball in my first pass and corrupted the bottom edge | MUST |
| 6 | Start the fit at the first overshoot peak, with velocity zero | Before the peak your hand drives the ball. At the peak the velocity really is zero, so the textbook initial condition becomes valid | MUST |
| 7 | Main model: second-order damped oscillator (Kelvin-Voigt) with parameters k/m and c/m | The assignment asks for stiffness and damping, and only a second-order model can overshoot | MUST |
| 8 | Also fit a version with a slow creep term | The ball rests about 3% lower after release in the 4K clips; the data decide whether the extra term is worth it | SHOULD |
| 9 | Fit on displacement normalized by rest height | Removes dependence on pixel scale and zoom, so parameters are comparable across clips | SHOULD |
| 10 | Fit with `scipy.optimize.least_squares` in log-parameters with multi-start | Raw MSE in meters squared is about 1e-4, so L-BFGS-B stops near the starting guess. Several starts avoid local minima | SHOULD |
| 11 | Leave-one-clip-out testing: fit on three clips, predict the fourth with no refit, rotate | The assignment requires a fresh instance and the fitted model. Four rotations are more convincing than one | MUST |
| 12 | Compare against baselines: stay at rest height, and a single exponential | An error number means nothing without a reference to beat | SHOULD |
| 13 | Report parameters per clip and their spread | Shows honestly how repeatable the identification is | SHOULD |
| 14 | 3D proxy is a shaded ellipsoid, height from the model, width from measured width | The assignment says a geometric proxy is enough and 3D reconstruction is not assessed | SHOULD |
| 15 | Render with numpy and OpenCV, not open3d | open3d needs a graphics context that often fails on headless machines | SHOULD |
| 16 | One entry-point script, pinned requirements, videos linked if large | Reproducibility is a stated criterion | MUST |
| 17 | README states assumptions and limitations plainly | The assignment ranks honest limitations above polish | MUST |

## Procedure, day by day

No reshoot is needed. The nine steps run in order, and each one needs the output of the one before it.

**Day 1: measure and track**

1. Measure the ball's diameter at its widest point with a ruler or calipers, twice at different angles, and weigh the ball if you have a scale. The diameter gives the scale; the mass lets you convert k/m and c/m into k and c later.
2. Confirm the capture settings: 1080p at 240 fps, and note which clips are the hold-out candidates.
3. Decode each clip at full resolution. Mask the yellow ball, cut the mask at the table line, and measure the top edge, bottom edge and width per frame with subpixel edges. Save one CSV per clip with frame index and time = frame / 240.
4. Save a debug overlay video per clip and check it by eye. A tracker you have not looked at is not trustworthy.

**Day 2: prepare, fit, validate**

5. Find the rest height from the flat tail of each clip, convert to normalized displacement, and detect the release and the first overshoot peak. Cut the window from that peak to about 0.3 s later.
6. Fit the damped oscillator and the creep variant on three clips. Predict the fourth clip from its own measured peak height, with no refit. Rotate through all four clips and compare against the baselines.

**Day 3: demo, README, interview prep**

7. Render the side-by-side demo: the real clip cropped on the ball next to the shaded ellipsoid, with time and both heights overlaid.
8. Write the README, pin the requirements, add the single run script, and re-run everything from a clean folder.
9. Spend the rest of the day on the two papers (see the deliverables section).

## Model and fitting

The model is a one-dimensional mass-spring-damper along the vertical axis, fitted to the ring-down that starts at the first overshoot peak. Height h is the bottom edge minus the top edge, and d is its fractional deviation from rest.

```latex
d(t) = \frac{h(t)}{h_{rest}} - 1, \qquad \ddot d + c'\,\dot d + k'\,d = 0, \qquad d(0)=d_{peak},\ \dot d(0)=0
```

```latex
\omega_n=\sqrt{k'},\quad \zeta=\frac{c'}{2\sqrt{k'}},\quad \omega_d=\omega_n\sqrt{1-\zeta^2},\quad d(t)=d_{peak}\,e^{-\zeta\omega_n t}\left[\cos\omega_d t+\frac{\zeta\omega_n}{\omega_d}\sin\omega_d t\right]
```

- **Parameters:** k' = k/m in s⁻² and c' = c/m in s⁻¹. Stiffness and damping appear only divided by the moving mass, because no force is measured. Weighing the ball gives an effective k and c, still lumped.
- **Closed form instead of numerical integration:** the equation has an exact solution, so the fit is faster and has no integration error. Integrating it with `odeint` once is a cheap check that the formula is right.
- **Nuisance parameters:** a small shift of the peak time (within ±2 frames, because the peak is picked from sampled data) and a rest-height offset (the tail estimate is uncertain).
- **Creep variant:** adds a slow term b·e^(−t/τc). It is kept only if it lowers held-out error, not just training error.
- **Optimizer:** `scipy.optimize.least_squares` on log(k') and log(c'), starting from about 30 points spread over ωn between 2π·5 and 2π·40 rad/s and ζ between 0.02 and 1.5. The best result across starts is kept.
- **Check on the answer:** if ζ comes out above about 1, the ball is not ringing and the clips contradict the model, so stop and look at the tracking.

## Validation

The model passes only if parameters fitted on three clips predict the fourth clip better than the baselines, with no refitting. The protocol repeats this four times, holding out a different clip each time.

- **What the held-out prediction uses:** only the new clip's own measured peak height and peak time as starting values. It does not see the clip's later frames.
- **Why leave-one-out and not one train/test split:** with only four clips, one split could look good or bad by luck. Four rotations show the spread.
- **Baseline 1, stay at rest height:** the prediction every model must beat to show it captures any dynamics.
- **Baseline 2, single exponential with a time constant fitted on the training clips:** shows whether the ringing term earns its extra parameter.

| Metric | Why it is reported |
| --- | --- |
| RMSE as a percent of ball height | Scale-free, so comparable across clips and cameras |
| RMSE in mm | Only if the diameter is measured; gives a physical sense of error |
| Ring period error in percent | Tests stiffness, the property the assignment names |
| Amplitude of the first trough after the peak, error in percent | Tests damping, the other named property |
| Fitted k/m and c/m per clip, with spread across clips | Shows how repeatable the identification is |

A proposed success rule, to be confirmed against the real numbers: the model beats both baselines on all four held-out clips, and the period error stays small enough that the oscillations stay in phase for the first two cycles. If it fails, the README says where it fails instead of hiding it.

## Assumptions and limitations

The README should state each of these plainly, because the assignment ranks an honest account of limits above visual polish.

- **The model covers the free ring-down only.** It does not predict the squeeze or the fast rise while the tin is leaving, because your hand controls that part.
- **Release speed is not controlled.** The tin leaves at a different speed each trial, which adds variation between clips that the model cannot explain.
- **Lumped one-dimensional model.** The ball is treated as one vertical spring and damper. Shear, rotation, and sideways motion are ignored.
- **Linear response.** Foam is nonlinear at large compression. The model is fitted only to the small ring-down amplitude, so it should not be trusted for deep squeezes.
- **Homogeneous and isotropic material.** The foam is treated as uniform in all directions.
- **Stiffness and damping are mass-normalized.** Without a force measurement, only k/m and c/m are identified. Weighing the ball gives an effective k and c, still lumped.
- **Single camera view.** Depth motion toward or away from the camera appears as a size change and is not separated out.
- **Table contact is not modeled.** If the ball bounces on the table, part of the ringing is rigid motion. The bottom-edge track tests this.
- **Only four trials.** Parameter spread across four clips is a rough estimate of repeatability, not a statistical confidence interval.
- **Lateral bulge is empirical.** Width comes from the measured width change, not from an assumed volume-preserving rule, because foam is compressible.

## Deliverables and interview prep

The submission is a reply to the assignment email with a GitHub repository (private is fine, with access given to the hiring team) and a link to view the result. Tick these off before sending.

- [ ] Code and fitted model in the repo, with one command that reruns tracking, fitting, evaluation and the demo
- [ ] `requirements.txt` with pinned versions
- [ ] Input videos in the repo, or an accessible link if they are too large
- [ ] Demo video: real clip beside the simulated ellipsoid, with time and heights overlaid, playable in a browser
- [ ] README: approach, assumptions, results against baselines, limitations
- [ ] README credits every tool, library and piece of AI-generated code used
- [ ] Link to view the result, and repository access given to the hiring team

**Interview prep (Part 01).** Read both papers and prepare to explain their main ideas, assumptions and limitations. I have not read the Hybrid Particle-Voxel Dynamics paper, so take its contents from the paper itself. Prepare a two-minute answer to each of these:

- Why a lumped one-dimensional model here, instead of a particle, voxel or other volumetric simulation?
- What would you change to move from this to a full 3D deformable model fitted from multi-view video?
- What does a model like this give a robot that manipulates soft objects, and where would it break?

## Open items and risks

Nothing blocks starting the tracker. Two inputs are needed from you, and four risks could change the results.

| Item | Type | What to do |
| --- | --- | --- |
| Ball's real diameter | Input needed | Measure at the widest point, twice; needed for any result in mm |
| Confirm the clips were recorded at 1080p, 240 fps | Input needed | All timing rests on this; the matching ring period at 120 fps supports it but does not prove it |
| Ball mass | Optional input | Lets you convert k/m and c/m to an effective k and c |
| Ringing may be a bounce on the table | Risk | Check that the bottom edge stays put after release |
| Ball rests about 3% lower after release | Risk | Seen in the 4K clips only; check the 240 fps clips, then test the creep term |
| Ring amplitude is only a few pixels | Risk | Needs full-resolution subpixel tracking; low-resolution results here are rough |
| Hand-driven release varies between trials | Risk | Fit only after the first peak; report the spread across clips |
