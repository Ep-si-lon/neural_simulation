# Family 1: lumped 1D models (the ball as one or two vertical bodies)

The first way I tried to explain the video: ignore the ball's 3D shape and describe only its vertical motion.
Each folder is one attempt; they share the same measurements (SAM 2 tracking, `tracking/outputs_sam2`) and the same test (fit on 0536+0537, predict 0538+0539, no refit).

**Protocol (corrected, see [docs/correction_release_definition.md](../../docs/correction_release_definition.md)).** The models start from the pressed plateau; the tin plate then retreats along the **measured** trajectory (46-121 ms) and the ball is free from the separation frame (time zero). The free recovery is predicted. An earlier version of this repo removed the tin instantly at the wrong frame; every number here was refitted and recomputed.

| Model | Idea | Held-out height error (0538 / 0539) | Outcome |
| --- | --- | --- | --- |
| [bounce_recovery](bounce_recovery/) | rigid hop with restitution + exponential height recovery (after the first hop apex only) | not comparable window | reproduces the hop (peak lift within 1 mm on 3 of 4 clips) |
| [two_mass_spring](two_mass_spring/) | bottom and top mass joined by a nonlinear spring-damper | 1.7 / 1.6 % | beats the plain exponential (3.1 / 3.4 %) |
| [fast_snap](fast_snap/) | same plus a much stiffer spring in deep compression | 1.1 / 1.1 % | best of the 1D models; recovery time within 3 ms |

Shared conventions: heights in pixels (about 400 px = 6.7 cm), file timestamps as the time base (verified with gravity), stiffness and damping per unit mass (the ball was never weighed accurately). Errors are RMSE as a percent of ball height, against two baselines (stay at rest, single exponential). Everything is compared on common footing in [evaluation/model_comparison](../../evaluation/model_comparison/README.md).
