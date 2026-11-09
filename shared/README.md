# Shared code (not a model)

Imported by several models; run scripts add this folder to `PYTHONPATH` through `../env.sh`. All paths are relative to the repository root.

| File | Contents |
| --- | --- |
| `common.py` | Clip names, frame size, location of tracking outputs, loader for the per-frame tracks |
| `clip_prep.py` | Per-clip preparation (rest height, compressed height, release frame, edge tracks cut to a 0.25 s window), gravity and contact constants, the RMSE metric and the exponential baseline |
| `shape_curve.py` | The width-profile curve `W (1 − |2s−1|ⁿ)^(1/n)` used for the outline, and its robust fit |
| `ball3d.py` | The 3D mass-spring engine: icosphere mesh, stretch/bending/radial springs, optional gas pressure, table, flat plate, point probe and two side plates |
| `scenario3d.py` | Relax → quasi-static press to the clip's compressed height → release → simulate; returns height, lift, width and squareness over time |
| `render2d.py`, `render3d.py` | Helpers for the 2D ellipsoid demos and the 3D software renderer |
