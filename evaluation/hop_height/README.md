# Hop-height comparison: 3D foam fit without vs with the hop term

Both fits are trained on 0536+0537 and run unchanged on 0538+0539. Hop height = peak lift of the bottom edge in mm (ball height = 67 mm).
Models: `models/mesh_3d/foam_core_no_lift` (hop ignored in the fit) and `models/mesh_3d/foam_core_with_lift` (hop term weighted 4×).

| Clip | Set | Real | No-lift fit | With-lift fit |
| --- | --- | --- | --- | --- |
| 0536 | train | 7.0 | 50.3 | 5.9 |
| 0537 | train | 7.4 | 63.3 | 8.9 |
| 0538 | TEST | 3.6 | 8.7 | 0.0 |
| 0539 | TEST | 5.2 | 8.5 | 0.0 |

- Without the hop term the model hops far too high after deep squeezes (50–63 mm, nearly a ball height) and about 2× too high after shallow ones: nothing in that fit constrains the hop.
- With it, deep-squeeze hops match (5.9, 8.9 mm against 7.0, 7.4) but the shallow-squeeze test clips get no hop (0.0 mm against 3.6 and 5.2).
- The with-lift fit recovers more slowly (95 % height in 40–54 ms against 13–42 ms real): matching the hop costs recovery-time accuracy.
- A flat press to 62 % of height gives 13 mm (no-lift) and 0.0 mm (with-lift); a 60 % press gives 50 mm and 6 mm; at 75 % compression the no-lift model hops 90 mm.
- The with-lift optimizer's second start stalled at its starting point, so its parameters may not be a true optimum.

Full table `outputs/results.md`, curves `outputs/hops.png`. Run `./run.sh` (seconds); code `src/compare_lift.py`.
