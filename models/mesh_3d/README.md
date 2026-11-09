# Family 2: 3D mass-spring mesh models

The second way to explain the video: represent the ball as a 3D surface mesh (an icosphere with 162 nodes, 480 edges), apply the press as a contact tool (flat plate, point probe or two side plates) and simulate it with gravity and a table.
All five variants share one engine, `../../shared/ball3d.py`, and one scenario runner, `../../shared/scenario3d.py`: relax, press quasi-statically to the clip's measured compressed height, release, simulate 0.25 s. They differ in the internal physics (sealed gas vs foam core) and in what the fit is asked to match.

| Model | Internal physics | Fit targets | Outcome |
| --- | --- | --- | --- |
| [gas_shell](gas_shell/) | sealed gas pocket (pressure ∝ 1/V) + skin springs | height, lift, pressed width | bulges and rings; abandoned |
| [foam_core_height_fit](foam_core_height_fit/) | foam core (radial springs), no gas | height, lift, pressed width | smooth, width right; first foam fit |
| [foam_core_shape_fit](foam_core_shape_fit/) | same | + outline squareness n and width over time | matches width/shape; no hop |
| [foam_core_no_lift](foam_core_no_lift/) | same | height, width, n (hop ignored) | hops far too high (uncontrolled) |
| [foam_core_with_lift](foam_core_with_lift/) | same | height, width, n and hop (weighted 4×) | matches deep-squeeze hops, none for shallow |

## Mesh parameters shared by all variants
| Item | Value | Kind |
| --- | --- | --- |
| nodes / edges / bending pairs / spokes | 162 / 480 / 480 / 162 | fixed (mesh choice) |
| ball radius | 3.35 cm | fixed (6.7 cm diameter, rough) |
| mass | total 1 (per unit mass), 1/162 per node | fixed (not weighed) |
| table contact | penalty `K_T = 10⁷`, damping ratio 0.3, friction 5 | fixed |
| time step | 4×10⁻⁵ s (explicit integrator; limits how stiff or damped a fit may be) | fixed |

Mass-spring parameters depend on the mesh: refining it would change the fitted values. A finite-element model with a Young's modulus would not have that problem.
Loads other than the flat top press (point, sides, 75 % press) are predictions only; see `../../evaluation/load_cases`.
