# Evaluation: comparing the models

Cross-model comparisons and demonstration videos. Each folder has `src/`, `outputs/` and `run.sh`; they use the saved fitted parameters in `models/*/outputs`, so they run in minutes.

| Folder | Question it answers |
| --- | --- |
| [recovery_time](recovery_time/) | How long does each model take to regain the ball's shape, against the real clips? (hops ignored) |
| [hop_height](hop_height/) | How high does each 3D fit make the ball hop, against the real hops? |
| [load_cases](load_cases/) | What do the 3D models predict for a flat top press, a point force on top, two side plates and a 75 % press? |
| [real_vs_model](real_vs_model/) | Real clip next to the 3D model on one clock (t = 0 at release) |
