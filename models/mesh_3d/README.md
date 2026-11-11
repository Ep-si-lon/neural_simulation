# Family 2: 3D mass-spring mesh models

The second way to explain the video: represent the ball as a 3D surface mesh (an icosphere with 162 nodes, 480 edges), apply the press as a contact tool and simulate it with gravity and a table.
All five variants share one engine, `../../shared/ball3d.py`, and one scenario runner, `../../shared/scenario3d.py`: relax, press quasi-statically to the clip's measured compressed height, **retreat the plate along the measured tin trajectory** (the corrected protocol, see [docs/correction_release_definition.md](../../docs/correction_release_definition.md)), release, simulate 0.25 s. They differ in the internal physics (sealed gas vs foam core) and in what the fit is asked to match.
Everything was refitted on the SAM 2 measurements after the correction; earlier results are in each `outputs/archive_v1_instant_release/`.

| Model | Internal physics | Fit targets | Held-out height error (0538 / 0539) | Outcome |
| --- | --- | --- | --- | --- |
| [gas_shell](gas_shell/) | sealed gas pocket (pressure ∝ 1/V) + skin springs | height, lift, pressed width | 3.7 / 4.1 % | fit stalled at its starting guess; overshoots and rings |
| [foam_core_height_fit](foam_core_height_fit/) | foam core (radial springs), no gas | height, lift, pressed width | 3.3 / 3.0 % | about the baseline; best hop among the meshes |
| [foam_core_shape_fit](foam_core_shape_fit/) | same | + outline squareness and width over time | 2.0 / 1.7 % | beats the baseline; recovers too fast |
| [foam_core_no_lift](foam_core_no_lift/) | same | height, width, n (hop ignored) | 1.1 / 1.2 % | smallest height error; no hop |
| [foam_core_with_lift](foam_core_with_lift/) | same | height, width, n and hop (weight 4) | 2.1 / 1.9 % | hop on the deep presses only |

Plain exponential baseline: 3.1 / 3.4 %. Honest status of the fits: parameters are per unit mass and mesh-dependent; the gas fit never left its starting values and the no-lift fit ended with the edge stiffness on its lower bound (100); the fits use two starting points and 20-30 optimizer steps.

## Mesh parameters shared by all variants
| Item | Value | Kind |
| --- | --- | --- |
| nodes / edges / bending pairs / spokes | 162 / 480 / 480 / 162 | fixed (mesh choice) |
| ball radius | 3.35 cm | fixed (6.7 cm diameter, rough) |
| mass | total 1 (per unit mass), 1/162 per node | fixed (not weighed accurately) |
| table contact | penalty `K_T = 10⁷`, damping ratio 0.3, friction 5 | fixed |
| time step | 4×10⁻⁵ s (explicit; limits how stiff or damped a fit may be) | fixed |

Mass-spring parameters depend on the mesh: refining it would change the fitted values; a finite-element model with a Young's modulus would not (see `../continuum`). Only flat top presses were fitted and tested; the engine also supports a point probe and two side plates. Everything is compared on common footing in [evaluation/model_comparison](../../evaluation/model_comparison/README.md).
