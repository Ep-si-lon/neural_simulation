# neural_simulation — squishy ball: bounce + recovery model from video

A simple model of one foam ball, fitted from 1080p/240 fps clips of a steel tin pressing it and being pulled away,
then **tested on clips held out of the fit (no refitting)**.

```bash
# needs python3, ffmpeg, and the four originals in videos/IMG_053{6,7,8,9}.MOV (not in git, ~157 MB)
./run.sh        # track -> fit/evaluate -> demo videos; results in out/
```

Outputs: `data/*.csv` (per-frame tracks), `out/results.txt`, `out/loo_predictions.png`, `out/demo_IMG_0538.mp4`, `out/demo_IMG_0539.mp4`
(real clip beside the shaded-ellipsoid proxy, 8x slow-mo, times and heights overlaid).

## What the video shows (and how this differs from my first plan)

My initial plan modelled a 20 Hz damped oscillation of the ball's height (Kelvin-Voigt). The full-resolution data do not support that:

- After release the ball's **height barely oscillates**; it recovers from about -2 to -3 % of rest height without overshoot, over roughly 100 ms.
- The visible "ringing" is the **whole ball hopping off the table** (about 0.5-0.8 cm, three hops, ~50 ms period). The ball is lifted by the rebound and lands again.

So the model is: **rigid ballistic hops with restitution + contact dwell, plus an exponential height recovery.**

## Time base

The files are variable frame rate: 2/3 of frame gaps are 1/240 s and 1/3 are 1/120 s (the camera appears to have dropped frames; cause not verified).
I tested both time bases using the ball itself: fitting free-flight arcs of the top edge gives gravity of **7.3-9.6 m/s² (mean ~8.7) with file timestamps**
versus **9.4-25 m/s² with a uniform 1/240 s**. True g is 9.81, so **file timestamps (pts) are used**; frames are never resampled or duplicated.

## Model

State starts at the first apex of the hop (velocity zero), measured from the clip itself: lift `A`, height deviation `δ_a`.

- Hops: gravity 9.81 m/s², restitution `e` (each apex is `e²` of the previous), contact dwell `t_c` on the table per bounce.
- Height: `δ(t) = δ_a · exp(-t/τ)`.
- Observed top edge: `top_up(t) = L(t; A, e, t_c) + rest · δ(t)`.
- Fitted: `τ` from the height signal alone (pooled over training clips), then `e`, `t_c` from the top edge (`scipy.optimize.least_squares`, multi-start, small per-clip time shift nuisance).
- A held-out prediction uses only that clip's own measured apex height, height dip and apex time.

## Results

Training: IMG_0536 + IMG_0537. Test: IMG_0538, IMG_0539. Also leave-one-clip-out over all four. RMSE of the top edge over the 0.2 s after the first apex, as % of ball height.

| Held-out clip | Model | Single exponential | Stay at rest |
| --- | --- | --- | --- |
| 0538 (train 536+537) | 0.99 | **0.52** | 1.14 |
| 0539 (train 536+537) | **0.63** | 1.18 | 1.77 |
| 0536 (leave-one-out) | **1.11** | 1.69 | 4.42 |
| 0537 (leave-one-out) | **0.97** | 1.19 | 3.13 |
| 0538 (leave-one-out) | 1.18 | **0.55** | 1.14 |
| 0539 (leave-one-out) | **0.63** | 1.19 | 1.77 |

Leave-one-out parameters: restitution `e` 0.66-0.71, `τ` 44-59 ms, `t_c` 8-14 ms. Per-clip fits: `e` 0.63-0.80, `τ` 30-72 ms, `t_c` 7-16 ms.

**The model beats both baselines on 3 of 4 leave-one-out clips, not all four.** On IMG_0538 it loses to the single exponential and is about level with stay-at-rest.
Likely cause (not confirmed): tin glare corrupts the top edge around the first apex in that clip, so the starting lift is overestimated; the ball's hops there are also small.

## Squeeze and release: two-mass simulation (negative result)

`src/sim.py` simulates the deformation itself: a bottom mass on the table and a top mass joined by a nonlinear spring-damper, with gravity and a stiff table contact.
Squeeze: the top follows the tin (measured top edge = input). Release: the ball is simulated from its compressed state at rest (measured), with no refit on the held-out clip.
Parameters are mass-normalised (no ball mass measured). Fitted on training clips with `least_squares` (soft-L1, multi-start).

| Held-out clip | Height RMSE, simulation | Height RMSE, exponential recovery | Stay compressed |
| --- | --- | --- | --- |
| 0538 | 6.6 % | **4.0 %** | 32.1 % |
| 0539 | 6.2 % | **3.8 %** | 31.4 % |
| 0536 | 8.3 % | **5.8 %** | 56.3 % |
| 0537 | 7.9 % | **5.6 %** | 62.4 % |

- **The simulation loses to a plain exponential on all four clips.** Fitted stiffness is consistent across folds (spring constant k about 11-16 x 10^3 s^-2 per unit mass; relative-mode frequency 2*sqrt(k) = 33-40 Hz; damping ratio c/sqrt(k) = 2.6-3.2, i.e. strongly overdamped), but the real ball snaps most of the way back within 1-2 frames (5-10 ms) after the tin leaves, while the simulation recovers over about 50 ms. Hop lift is under-predicted for 0538/0539 and over-predicted for 0537. The fitted cubic (stiffening) term went to zero in three of four folds, so the nonlinearity was not supported.
- Likely causes (not confirmed): the first frames after release are partly hand-driven and partly corrupted by tin glare; one lumped spring cannot make a fast snap and a slow tail.
- Not tried: a separate fast-snap phase before the spring-damper takes over. The demo `out/demo_squeeze_*.mp4` shows the squeeze and release next to this simulation, including where it disagrees.
- The bounce + recovery model above remains the better-performing model for the post-release motion. Squeeze compression levels differ (36-41 % of height in 0536/0537, 67 % in 0538/0539), so the 536+537 -> 538/539 split also tests extrapolation to shallower squeezes.

## Assumptions and limitations

- **Scope:** only the free motion after the first apex. The squeeze and the hand-driven release are not modelled; release speed is uncontrolled.
- **Scale depends on a rough diameter (6.7 cm, not accurately measured).** It sets pixels-per-metre and so the gravity term; a 5 % error shifts the hop timing. No ball mass was measured, so no force/stiffness values are reported.
- **Lumped, vertical, rigid-hop model.** Ball treated as one body plus a height recovery; no rotation, shear, or sideways motion. Impact squashing is only represented by the dwell time `t_c`.
- **Recovery `τ` is weakly determined:** the dip is 2-3 % of height, comparable to tracking noise (±1-2 %). Treat `τ` as an estimate, not a material constant.
- **Width in the demo is measured**, not predicted; only height and lift come from the model. Foam is compressible, so no volume-preserving rule is assumed.
- **Top edge doubles as hop proxy.** The bottom edge saturates at the table cut line (row 740) while the ball touches the table, so it is not used for fitting.
- **Tracking:** fixed HSV threshold, table line fixed at row 740 (same camera pose in all clips), soft-edge subpixel crossings. Debug overlays are generated in `out/*_debug.mp4` but I only spot-checked traces, not every frame.
- **Four clips**: parameter spread is a rough repeatability estimate, not a confidence interval. The 3-D object is only a shaded ellipsoid; no 3-D reconstruction.
- Same ball and same tin in all clips; the "fresh instance" is a different clip of the same interaction, not a different ball.

## Credits

Python, NumPy, SciPy, OpenCV, Matplotlib, FFmpeg. Code and analysis were written with Claude Code (Anthropic's AI assistant); results were checked by running the pipeline end to end.
