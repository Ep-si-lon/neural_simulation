# Glossary in plain words

## The data
- **Tracking:** finding the yellow ball in every video frame and measuring its top edge, bottom edge and width in pixels.
- **Silhouette / shape:** the ball's outline. I fit a smooth curve to it in each frame to get its **width W** and its **squareness n** (n = 2 is an ellipse, 5-6 is a flat-sided cylinder).
- **Height:** bottom edge minus top edge. **Rest height** is the ball's height when nothing touches it (about 400 px = 6.7 cm).
- **Compression:** how far the ball is pressed. 60 % compression means its height is 40 % of rest.
- **Release:** the instant the tin lets go (the last frame the ball is still held compressed).
- **Timestamps (pts):** each frame's time stored in the file. They are uneven, so I use them instead of "frame number / 240".

## The physics
- **Stiffness (k):** how hard a spring pushes back per unit squeeze. Higher is stiffer.
- **Damping (c):** friction that makes motion die out. **Damping ratio** above 1 means no wobble; below 1 it rings.
- **Restitution (e):** how bouncy a landing is. 0.7 means the rebound speed is 70 % of the landing speed (each bounce keeps about half its energy).
- **Time constant:** about how long a recovery takes (it reaches 63 % of the way back in one time constant).
- **Per unit mass:** stiffness and damping are given divided by the ball's mass because I never weighed it, so only comparisons between them mean anything.
- **Hop:** the whole ball leaving the table after release. Its height is the peak lift of the ball's bottom edge.

## The 3D model
- **Mesh:** the ball as 162 points joined by springs.
- **ks (stretch spring):** resists the surface stretching, like a rubber sheet.
- **kb (bending spring):** resists the surface folding sharply, like cardboard.
- **kr (radial / foam-core spring):** each surface point is tied to the centre; resists squashing, like foam inside.
- **cd:** damping in those springs.
- **Quasi-static press:** the plate is moved down slowly enough that the ball is always at rest, so only the release is simulated in real time.

## Fitting and testing
- **Fit / training clips:** the clips used to adjust the model's numbers (0536, 0537).
- **Held-out / test clips:** clips the model never saw (0538, 0539). It is run on them with no adjustment: this is the "prediction".
- **Leave-one-out:** repeat the test four times, each time holding out a different clip.
- **RMSE:** the typical size of the error between model and video. Quoted as a percent of ball height.
- **Baseline:** a simple guess the model must beat. "Stay at rest" is the dumbest; "single exponential" says the ball just eases back with no physics.
- **Nonlinear least squares:** the search method that tunes the numbers to minimise the error. Same maths as ML training, but with only 3-4 numbers and hand-written physics, so I call it system identification, not ML.
- **Replay vs prediction:** replay copies the measured motion back; prediction runs the model from physics and the inputs only. The measured pressed height and release time are inputs.

## Continuum models and tracking
- **Young's modulus (E):** how stiff the material is, in pascals (force per area for a given stretch). Foam is soft: tens of kilopascals.
- **Poisson ratio (nu):** how much a material bulges sideways when squashed. Rubber is near 0.5 (keeps its volume); foam is near 0 (just compresses).
- **FEM (finite elements):** the ball is cut into small pieces that each store elastic energy; the forces come from that energy. Here one 2D slice is revolved around the vertical axis.
- **MPM (material point method):** the ball is a cloud of particles; each step they hand their motion to a background grid, the physics runs on the grid, and it is handed back. No mesh to tangle, so it copes with big squeezes.
- **NVIDIA Warp / PyTorch:** Warp is a library that runs the simulation on the GPU and can differentiate through it; PyTorch drives the optimizer that adjusts the parameters.
- **SAM 2:** Meta's pretrained model that cuts the ball out of every video frame. It is the only neural network in the project.
- **Rayleigh (mass-proportional) damping:** a drag proportional to velocity. It makes the recovery overdamped (no wobble) but also stops the whole ball from hopping.
