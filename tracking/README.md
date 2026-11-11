# Tracking: video → measurements

Step 1 for every model. Needs the four originals in `videos/IMG_053{6,7,8,9}.MOV` (1080p, 240 fps, not in git). `./run.sh` takes about 4 min.

| Script | What it does | Output (`outputs/`) |
| --- | --- | --- |
| `src/track.py` | Colour-thresholds the yellow ball in every frame, cuts the mask at the table line (row 740) and measures top edge, bottom edge and width with subpixel edges | `<clip>.csv` (frame, pts_s, top_px, bottom_px, width_px, cx_px), `debug/<clip>_debug.mp4` (not in git) |
| `src/silhouette.py` | Left/right edge of the filled outline at 48 levels from top to bottom | `<clip>_sil.npz` |
| `src/shape.py` | Fits the width profile `w(s) = W (1 − |2s−1|ⁿ)^(1/n)` to each frame (soft-L1, ignores spikes) | `<clip>_shape.csv` (W_px, n, fit_rms_px) |

| `src/segment_sam2.py` | **SAM 2** (pretrained Segment Anything 2, tiny) video tracking, prompted automatically once on frame 0 from the colour mask, then propagated; same outline measurement and a frame-by-frame comparison with the colour tracker | `outputs_sam2/<clip>_sil.npz`, `<clip>_compare.txt` |

`./run_sam2.sh` runs the SAM 2 step (needs `.venv-sim`, see `../models/continuum/README.md`; downloads the model weights once from Hugging Face).

## Method and assumptions
- Yellow = HSV hue 17–40 with saturation ramp; largest connected component; holes (smiley line, white seam) filled for the outline.
- Time = file timestamps (`pts_s`), not frame number / 240: the files drop to 1/120 s gaps in a third of frames. Fitting free-flight arcs with these timestamps gives gravity ≈ 8.7 m/s² (uniform 1/240 s gives 9.4–25).
- Table line fixed at pixel row 740 and the yellow-green object left of the ball ignored (x < 400, x > 1500): same camera pose in all clips.

## Which tracker to trust for the top edge: SAM 2
While the ball is pressed, the colour tracker's top edge reads **too high by about 16-20 px (4-5 % of the ball's height)**. The cause is a yellow reflection of the ball on the shiny underside of the tin, which passes the colour threshold. SAM 2 segments the ball itself and ignores the reflection. After release the two agree to within about 2 px, and the bottom edge and width agree throughout (mean differences 0.5-1.6 px and 2-8 px).
Consequences: the **pressed (hold) height is 4-20 px too high in the colour data** (for example 268 and 266 px instead of 252 and 246 px for 0538 and 0539), and so are the squeeze and hold outlines.
- `TRACKER=sam2` makes every script read `outputs_sam2/` instead of `outputs/` (`shared/common.py`); `src/sam2_tables.py` writes the csv and shape tables from the SAM 2 outlines.
- The continuum models (`models/continuum`) are fitted on the SAM 2 data. **The earlier lumped and mesh models were fitted on the colour data**: their release-phase targets are unaffected, but the compressed height they start from is 4-5 % too high, and I did not refit them.
- Mask agreement with the colour tracker (IoU): mean 0.92-0.95, 5th percentile about 0.88 (`outputs_sam2/*_compare.txt`).

## Limitations
Fixed colour threshold; bottom edge clamps at the table line while touching; tin glare corrupts the top edge for a few frames at release (most visible in IMG_0538); the first frames after release are partly hand-driven; I spot-checked traces and frames, not every debug frame.
