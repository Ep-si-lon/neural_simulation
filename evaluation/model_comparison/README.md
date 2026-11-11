# Comparing every model, on the same footing

All 12 models (and the plain-exponential and stay-at-rest baselines) are run with their saved parameters and scored against the **same SAM 2 measurements** of the real clips. Models were fitted on 0536 and 0537 (deep squeezes, 36-41 % of height) and are tested on 0538 and 0539 (shallow squeezes, 62-63 %) with no refit. Time zero is the **separation frame**, when the ball leaves the tin; every model is driven by the measured tin retreat before that (corrected protocol, see [docs/correction_release_definition.md](../../docs/correction_release_definition.md)).
Run `./run.sh` (about 5 min). Full tables: [outputs/results_tables.md](outputs/results_tables.md); numbers in `outputs/metrics.json`.

## Figures (`outputs/`)
| Figure | Shows |
| --- | --- |
| `fig1_height_curves_all.png` | height over the first 120 ms after separation, every model against the real clip, four clips |
| `fig2_height_by_family.png` | the same, one row per model family, with the exponential baseline |
| `fig3_height_rmse.png` | height error per model, train and held-out |
| `fig4_recovery_time.png` | time to 95 % of rest height, model against real |
| `fig5_width_and_hop.png` | pressed width and hop height, model against real |
| `fig6_scorecard.png` | rank of every model per aspect on the held-out clips |
| `fig7_gallery_IMG_0538.png` | each model's side view at the pressed hold and 32 ms after separation, next to the real clip |

## What the comparison shows
1. **Height after release: most physics models beat the plain exponential, and the spread among the good ones is small.** On the held-out clips: fast-snap 1.1 %, no-lift 3D mesh 1.1 %, two-mass 1.6 %, axisymmetric FEM 1.7 %, 3D shape-fit mesh 1.9 %, with-lift mesh 2.0 %, MPM 2.1 %, against 3.3 % for the exponential. The tracker's own noise is of the order of 1 %, so **the ranking among the top models is not statistically meaningful**. The gas shell (3.9 %) and the height-fit mesh (3.2 %) do not beat the baseline.
2. **The largest single effect is the protocol, not the model.** The same axisymmetric FEM gives 3.1 % with the tin removed instantly (the earlier protocol) and 1.7 % with the measured tin retreat: 1.4 points, more than the difference between most models. Every model that had looked bad (6-8 %) under the old protocol is at 1-4 % now.
3. **Recovery time:** best matched by the fast-snap model and the FEM (24 ms on both test clips against 27 and 24), then the calibrated MPM (27 / 27). The shape-fit and with-lift meshes recover too fast (15-16 ms); the two-mass spring too slowly (34-35 ms).
4. **Pressed shape:** only the continuum models, the gas shell (on the shallow presses) and the height-fit mesh get the pressed width right to within about 0.01 on the shallow presses. The FEM and MPM over-bulge on the deep presses (1.13-1.16× against 1.077×); the three newer spring meshes under-bulge (0.99-1.04× against 1.03-1.07×). Only the FEM and the shape-fit meshes have an outline; the FEM's squareness at the hold (4.0) is close to the real 4.1, the meshes' (3.1-3.2) are not.
5. **Hop:** only the spring models produce one, and none gets it right everywhere: the height-fit mesh is closest (7.4 / 8.2 mm on the deep presses, 2.8 / 2.3 on the shallow, against 7.1 / 7.5 and 3.3 / 5.4); the bounce model (outside the common window) is closest of all (7.1 / 6.5 / 2.5 / 4.7). The continuum models have no hop by construction (mass-proportional damping), and the no-lift mesh none by design.
6. **Physical meaning and generality:** only the continuum models give parameters in physical units that do not depend on the discretisation (E = 38 kPa for an assumed 55 kg/m³, ν = 0.10), a smooth round ball, and a route to other loads (the MPM point and side loads, unvalidated). They are not more accurate on height than the 1D models.
7. **Cost:** a forward run takes milliseconds for the 1D models, 2-3 s for the meshes and the FEM, 6 s for the MPM; fitting takes about a minute (1D), 15-20 min (meshes, CPU), 10 min (FEM, GPU).

## Caveats
- Two training clips and two test clips: a rough spread, not a confidence interval. The test clips are shallower presses, so their errors are smaller for every model; compare models on the skill column (1 − RMSE / RMSE of the exponential), not across train and test.
- The bounce model only covers the time after its first hop apex, when the height is already about 99 %, so its height error and recovery time are not comparable and are left out of the ranking.
- The gas shell's fit never left its starting values; the no-lift mesh ended with the edge stiffness on its lower bound; the mesh fits use two or three starting points and 20-30 optimizer steps.
- The MPM's material is the FEM's; only its damping was calibrated (on the training clips). All stiffnesses of the spring models are per unit mass and mesh-dependent.
- The "instant release" FEM is an ablation of the protocol, kept only to show the effect.

## Aspects that are not numbers
| Model | Representation | Fitted numbers | Units / mesh-independent? | Loads supported (fitted on flat press) | Hop |
| --- | --- | --- | --- | --- | --- |
| bounce + recovery | rigid hop + exponential | 3 (e, τ, t_c) | yes / no mesh | none (post-apex motion) | yes |
| two-mass spring | 2 masses, nonlinear spring-damper | 3 | per unit mass / no mesh | flat | partly |
| fast-snap two-mass | + stiff deep-compression regime | 4 | per unit mass / no mesh | flat | partly |
| 3D gas shell | spring mesh, sealed gas | 4 (stalled) | per unit mass / mesh-dependent | flat (engine: point, sides) | rings |
| 3D foam core (4 variants) | spring mesh, radial foam core | 4 each | per unit mass / mesh-dependent | flat (engine: point, sides) | varies |
| axisymmetric FEM (Warp) | continuum, 2D slice revolved | 5 (E, ν, α, 2 frictions) | Pa (assumed ρ) / yes | flat | no |
| 3D MPM (Warp) | continuum, particles | 0 new + 1 calibrated damping | Pa / yes | flat, point, side (unvalidated) | no |

## Added: FEM with damping relative to the centre of mass (×16)
`fem_relative_damping` reruns the fitted FEM with damping that acts only on motion relative to the ball's centre (so the whole ball can hop) at 16× the fitted rate. The factor was chosen on the training clips only (`models/continuum/fem_axisymmetric_warp/outputs/hop_scan.json`). It has the lowest held-out height error (1.6 / 1.3 %) and hops 4-8 mm (real 3-7 mm), but E, ν and friction were not refitted for it, and on clip 0538 it hops about twice the real height (24× fits that clip better). Tables and figures above include it.
