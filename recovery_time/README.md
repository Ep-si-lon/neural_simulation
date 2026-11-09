# Recovery-time study: train on 0536+0537, test on 0538+0539

Question: how long does the ball take to regain its shape after the tin leaves? Hops are ignored; only the shape recovery is scored.
Models are trained on 0536 and 0537 only and then run, with no refit, on 0538 and 0539 (each starts from its own measured compressed height).

Run from the repo root (3D refit takes ~20 min, then compare takes seconds):
```bash
PYTHONPATH=src:sim3d python -u recovery_time/fit3d_recovery.py
PYTHONPATH=src:sim3d python recovery_time/compare.py     # -> results.md, recovery_time.png
```

Metrics, with t = 0 at release (last frame the ball is still held compressed):
- `height 95 %` / `98 %`: first time the height reaches that fraction of rest height.
- `shape n<=2.3`: first time the outline squareness n (flat-sided ~5, ellipse = 2) is back to an ellipse (real + 3D model only).

Models: single exponential; 1-DOF spring-damper (bottom pinned on the table); fast+slow double exponential; 3D foam-core mesh refitted on height, width and squareness with no lift term.

## Results (ms after release)

| Clip | Set | Pressed to | Real 95 % | Exp | 1-DOF | Fast+slow | 3D foam |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0536 | train | 41 % | 37 | 33 | 33 | 38 | 30 |
| 0537 | train | 36 % | 42 | 34 | 34 | 40 | 32 |
| 0538 | TEST | 67 % | 25 | 26 | 26 | 28 | 22 |
| 0539 | TEST | 67 % | 13 | 26 | 26 | 27 | 22 |

Full table (including 98 % and shape times): `results.md`. Curves: `recovery_time.png`.

## Reading the results honestly

- On the two test clips, every model predicts a 95 % recovery of 22-28 ms; the real values are 25 and 13 ms. Errors are -3 to +14 ms.
- **Two clips pressed to the same depth (0538, 0539) differ by 12 ms in reality**, and frame spacing is itself 4-8 ms. The models differ from each other by less than that, so this test cannot tell the models apart.
- All models are slightly too fast on the training clips (30-34 ms against 37-42 ms real), i.e. they under-estimate recovery time for deep squeezes.
- The 98 % metric is dominated by noise: 0539 reaches 95 % in 13 ms but 98 % only at 96 ms (a slow creep), which no model reproduces. Treat it as unreliable.
- Shape time: the 3D model predicts squareness is back to an ellipse after 19 ms on both test clips; real values are 38 and 21 ms. For 0537 the real shape had already recovered at the release frame (0 ms), because release is detected from height, not shape.
- The test clips are pressed to 67 % of height, but training was on deep squeezes (36-41 %), so this also tests extrapolation to shallower presses.
