# Recovery-time comparison (train 0536+0537, test 0538+0539)

Question: how long does the ball take to regain its shape after the tin leaves? Hops are ignored; only shape recovery is scored.
Models are trained on 0536 and 0537 only, then run unchanged on 0538 and 0539, each starting from that clip's own measured compressed height.

**Metrics** (t = 0 at release, the last frame the ball is still held compressed):
- `height 95 %` / `98 %`: first time the height reaches that fraction of rest height.
- `shape n<=2.3`: first time the outline squareness n is back to an ellipse (real clips and the 3D model only).

**Models:** single exponential; 1-DOF spring-damper (bottom pinned on the table); fast+slow double exponential; 3D foam core refitted without the hop term (`models/mesh_3d/foam_core_no_lift`).
Fitted baselines: exponential τ = 13.2 ms; 1-DOF k = 610,000, c = 8,100 (damping ratio 5.2); fast+slow 38 % at 1.0 ms and 62 % at 19 ms.

## Results (ms after release, 95 % of rest height)
| Clip | Set | Pressed to | Real | Exp | 1-DOF | Fast+slow | 3D foam |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0536 | train | 41 % | 37 | 33 | 33 | 38 | 30 |
| 0537 | train | 36 % | 42 | 34 | 34 | 40 | 32 |
| 0538 | TEST | 67 % | 25 | 26 | 26 | 28 | 22 |
| 0539 | TEST | 67 % | 13 | 26 | 26 | 27 | 22 |

Full table: `outputs/results.md`; curves `outputs/recovery_time.png`.

## Reading the results honestly
- Test errors are -3 to +14 ms. Two clips pressed to the same depth differ by 12 ms in reality, and frame spacing is 4–8 ms, so **this test cannot separate the models**.
- All models are slightly too fast on the deep-squeeze training clips (30–34 ms against 37–42 ms).
- The 98 % metric is noise-dominated (0539 reaches 95 % in 13 ms but 98 % only at 96 ms, a slow creep no model reproduces).
- Shape time: the 3D model predicts 19 ms on both test clips; real 38 and 21 ms. For 0537 the real shape had already recovered at the release frame because release is detected from height.
- The test squeezes are shallower (67 %) than training (36–41 %), so this also tests extrapolation.

## Run
`./run.sh` (seconds). Code `src/compare.py`.
