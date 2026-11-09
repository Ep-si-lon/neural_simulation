# 3D foam model refitted WITH the lift (hop) term

Same data and split as `recovery_time/` (train 0536+0537, test 0538+0539, no refit), but the fit residual also contains the bottom-lift term, weighted 4x.
Fit: `fit3d_lift.py` (log in `fit3d_log.txt`). Hop and recovery comparison against the no-lift fit: `compare_lift.py` -> `results.md`, `hops.png`.
Demo videos with this model's parameters: `lift_flat.mp4` (flat plate on top), `lift_point.mp4` (point force on top), `lift_side.mp4` (two flat plates from the sides).

Hop height (peak bottom lift, mm; ball height = 67 mm):

| Clip | Set | Real | No-lift fit | With-lift fit |
| --- | --- | --- | --- | --- |
| 0536 | train | 7.0 | 50.3 | 5.9 |
| 0537 | train | 7.4 | 63.3 | 8.9 |
| 0538 | TEST | 3.6 | 8.7 | 0.0 |
| 0539 | TEST | 5.2 | 8.5 | 0.0 |

- Without the lift term the model hops far too high after deep squeezes (50-63 mm, nearly a ball height) and about 2x too high after shallow ones. The hop is not constrained by anything in that fit.
- With the lift term it matches the deep-squeeze hops (5.9 and 8.9 mm against 7.0 and 7.4), but predicts no hop at all after the shallow 67 % squeezes (0.0 mm against 3.6 and 5.2).
- The with-lift fit recovers more slowly (95 % height in 40-54 ms against 13-42 ms real), so matching the hop costs recovery-time accuracy.
- In the demo videos the plate presses to about 62 % of height, and this model does not hop there (0.0 mm; a 60 % press gives 6 mm).
- The optimizer's second start ended exactly where it began (stuck), and it still had the lower cost, so the parameters may not be a true optimum.
