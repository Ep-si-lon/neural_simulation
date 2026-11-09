# Real clip next to the 3D model, on one clock

`outputs/real_vs_3d_IMG_0536.mp4` and `real_vs_3d_IMG_0537.mp4`: three panels, the real clip, the 3D model's side view and its oblique view. The header shows `t` in ms from release (slowed 8×); real frames are shown at their true file timestamps and the model runs on the same clock.
Model: `models/mesh_3d/foam_core_with_lift`, started from the clip's measured compressed height and released at t = 0.

- 0536 and 0537 are **training** clips: they show the fit, not a prediction. Held-out versions (0538, 0539) are the fairer test and can be rendered with `src/side_by_side.py IMG_0538`.
- In the model panels the plate vanishes instantly at t = 0; the real tin takes a few frames to leave.

Run `./run.sh` (about 2 min); code `src/side_by_side.py`.
