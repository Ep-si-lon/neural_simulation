# Family 1: lumped 1D models (the ball as one or two vertical bodies)

The first way I tried to explain the video: ignore the ball's 3D shape and describe only its vertical motion after the tin lets go.
Each folder is one attempt; they share the same measurements (`tracking/outputs`) and the same test (train 0536+0537, test 0538+0539, no refit).

| Model | Idea | Outcome |
| --- | --- | --- |
| [bounce_recovery](bounce_recovery/) | Rigid ball hops with restitution + height recovers exponentially | beats both baselines on 3 of 4 clips (leave-one-out) |
| [two_mass_spring](two_mass_spring/) | Bottom and top mass joined by a nonlinear spring-damper, released from the squeezed state | loses to a plain exponential on all clips |
| [fast_snap](fast_snap/) | Same as above plus a much stiffer spring in deep compression, to explain the fast snap-back | no improvement (negative result) |

Shared inputs and conventions: heights are in pixels (about 400 px = 6.7 cm), time is the file timestamp (verified with gravity), stiffness and damping are per unit mass because the ball was never weighed.
Error metric everywhere: RMSE as a percent of ball height, against two baselines (stay at rest, single exponential). Shared code is in `../../shared/clip_prep.py`.
