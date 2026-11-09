# Evaluation: comparing the models

| Folder | Question it answers |
| --- | --- |
| [recovery_time](recovery_time/) | How long does each model take to regain the ball's shape, against the real clips? (hops ignored) |

It uses the saved fitted parameters in `models/*/outputs`, so `recovery_time/run.sh` takes seconds. The hop-height check lives with the model that needs it: `models/mesh_3d/foam_core_with_lift/src/hop_check.py`.
Each model's own real-versus-model videos are in that model's `outputs/` (rendered by `render.sh`, which uses `shared/real_vs_3d.py` for the 3D models).
