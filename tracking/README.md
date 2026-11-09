# Tracking: video → measurements

Step 1 for every model. Needs the four originals in `videos/IMG_053{6,7,8,9}.MOV` (1080p, 240 fps, not in git). `./run.sh` takes about 4 min.

| Script | What it does | Output (`outputs/`) |
| --- | --- | --- |
| `src/track.py` | Colour-thresholds the yellow ball in every frame, cuts the mask at the table line (row 740) and measures top edge, bottom edge and width with subpixel edges | `<clip>.csv` (frame, pts_s, top_px, bottom_px, width_px, cx_px), `debug/<clip>_debug.mp4` (not in git) |
| `src/silhouette.py` | Left/right edge of the filled outline at 48 levels from top to bottom | `<clip>_sil.npz` |
| `src/shape.py` | Fits the width profile `w(s) = W (1 − |2s−1|ⁿ)^(1/n)` to each frame (soft-L1, ignores spikes) | `<clip>_shape.csv` (W_px, n, fit_rms_px) |

## Method and assumptions
- Yellow = HSV hue 17–40 with saturation ramp; largest connected component; holes (smiley line, white seam) filled for the outline.
- Time = file timestamps (`pts_s`), not frame number / 240: the files drop to 1/120 s gaps in a third of frames. Fitting free-flight arcs with these timestamps gives gravity ≈ 8.7 m/s² (uniform 1/240 s gives 9.4–25).
- Table line fixed at pixel row 740 and the yellow-green object left of the ball ignored (x < 400, x > 1500): same camera pose in all clips.

## Limitations
Fixed colour threshold; bottom edge clamps at the table line while touching; tin glare corrupts the top edge for a few frames at release (most visible in IMG_0538); the first frames after release are partly hand-driven; I spot-checked traces and frames, not every debug frame.
