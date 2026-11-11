# Correction: the release instant, the tin's retreat, and what it invalidated

## What went wrong
`shared/clip_prep.py::prep()` is meant to find the instant the tin lets go of the ball. A loop condition was inverted, so instead of walking back to the end of the pressed plateau it stopped at the **mid-rise frame**, where the ball is already at about 70-80 % of its rest height. For IMG_0536 the tracked height around that frame is (px): 173, 174, 179, 183, 192, 207, 215, 246, **289** (the chosen "release"), 308, 320: the plateau had ended about eight frames earlier.

## What the video actually shows
The tin does not vanish. After the plateau it **retreats gradually** (46-121 ms depending on the clip), rising slowly and then accelerating, with the ball's top edge riding on it (while in contact, the ball's top edge *is* the tin's underside). The ball **separates** from the tin at about 70-80 % of its height: the flat contact patch disappears (outline squareness n drops from about 5 to about 2.4) and from then on the ball is free. Only that free recovery (about 25-40 ms to 95 % of rest height) belongs to the ball; the slow first part is the tin's motion.

## What it invalidated
Every model was started at the mid-rise frame as if the ball were still fully pressed and at rest, and was asked to match data that already stood at 72 %. The fits compensated with unphysical, very fast initial dynamics. Consequences:
- **"The real ball snaps back within 1-2 frames" was false** (stated in several READMEs and in my explanations).
- **The fast-snap experiment** (`models/lumped_1d/fast_snap`) was motivated by that artefact.
- The first **recovery-time study** compared the real recovery from 72 % with model recoveries from about 40 %.
- The fitted parameters of the spring models were bent to hide the mismatch, and the **MPM looked "too quick"** for the same reason.
- The finding "the shape recovers as fast as the height" (squareness drops within 2 frames) was the separation event itself.

## The fix
- `prep()` now also returns the end of the plateau and the **measured tin trajectory** (time since plateau end, top-edge height) up to the separation frame, which stays time zero for all comparisons.
- Every simulator (two-mass and fast-snap ODEs, the three 3D mesh scenario runners, the FEM, the MPM) moves a kinematic plate along that trajectory, then removes it at separation. The ball's free recovery is then **predicted**, not replayed; only the tin's motion is an input.
- Evidence the initial condition is now right: for IMG_0538, with the *old* parameters and the new input, the two-mass model reaches 0.812 and the 3D foam mesh 0.815 of rest height at separation, against 0.811 measured.
- All models were **refitted on the SAM 2 measurements** (see `tracking/README.md` for why the colour tracker's pressed top edge is biased high), so every model now sees the same data.
- The old outputs are kept in [archive/v1_instant_release/](../archive/v1_instant_release/) (and `*_instant_release.*` for the continuum models) for transparency; the axisymmetric FEM with the old protocol is kept as an ablation model in the comparison.

## What remains valid
Tracking and its SAM 2 comparison, the time base (verified with gravity), the hop analysis after the first apex (bounce model), and the conclusions about the sealed-gas model's bulge. Everything that depended on the release frame (fitted stiffness and damping, recovery times, rankings) was recomputed; see `evaluation/model_comparison`.
