# FEM with damping relative to the centre of mass (the hop model, ×16)

This is the **same axisymmetric finite-element ball** as [`../fem_axisymmetric_warp`](../fem_axisymmetric_warp/README.md) (same mesh, material law, contact, tin-retreat protocol, same fitted E, ν and friction). **Only the damping term changed**, and that change is what lets the ball hop. The earlier model is untouched and stays the default; this folder holds the hop variant, its parameter scan, its videos and the reasoning.

## 1. What I changed in the damping
Damping in the solver is mass-proportional (Rayleigh) with rate α (units 1/s). Each node's acceleration is `a = F/m − (damping term)`.

| | Earlier model (`fem_axisymmetric_warp`) | This model |
| --- | --- | --- |
| damping term | `α · v` (the node's own velocity) | `α · (v − v_cm)` (its velocity relative to the ball's centre of mass) |
| meaning | drags every node towards standing still, **including the motion of the whole ball** | drags only the *internal* motion (squashing, bulging); **the ball as a whole is free to move** |
| α used | 2806 s⁻¹ (fitted) | 16 × 2806 = **44,896 s⁻¹** |
| code | `rel = 0` in `k_node` (`../fem_axisymmetric_warp/src/fem_axi.py`) | `rel = 1`, and the fitted α multiplied by 16 |

## 2. Why the old model could not hop
With `α·v`, any upward velocity the whole ball gets from the released elastic energy is immediately drained. The ball can only creep back to its rest shape; it can never leave the table. That is correct for a heavily overdamped recovery but it makes a hop of 3-8 mm impossible, whatever E, ν or α are.

## 3. Why simply switching it on was not enough, and why ×16
Switching to the relative form at the fitted α (×1) removes the drag on the whole-ball motion, so almost all the stored energy goes into flight:

| α multiplier | hop (mm), clips 0536 / 0537 / 0538 / 0539 | 95 % recovery (ms) | note |
| --- | --- | --- | --- |
| ×1 | 321 / 356 / 128 / 126 | 4 | the ball flies off like a rocket |
| ×2 | 211 / 233 / 91 / 90 | 6 | |
| ×4 | 111 / 121 / 56 / 54 | 8 | |
| ×8 | 40 / 43 / 27 / 25 | 16 | still too high and too fast |

(source: `outputs/hop_experiment.txt`; real hops are 7.1 / 7.5 / 3.3 / 5.4 mm.) So the drag that is lost when the whole-ball part is excluded has to be put back into the internal motion: **I multiplied α to compensate.** The multiplier is not a physical constant; it is the one extra number this variant introduces. A reasonable reading (my interpretation, not separately tested) is that the relative form acts only on the deformation part of each node's velocity, which is a fraction of its total speed, so it needs a much larger α to damp the shape recovery as strongly as before.

My earlier note that "one damping number cannot match both hop and recovery" was wrong: I had stopped the scan at ×8. The scan was then extended (`src/hop_scan.py`, `outputs/hop_scan.json`, plot `outputs/hop_scan.png`):

| Variant | Height RMSE (% of rest height), 0536 / 0537 / 0538 / 0539 | 95 % recovery (ms) (real 37 / 42 / 29 / 25) | Hop (mm) (real 7.1 / 7.5 / 3.3 / 5.4) |
| --- | --- | --- | --- |
| earlier model (absolute damping) | 3.2 / 3.3 / 2.0 / 1.5 | 30 / 32 / 24 / 24 | 0 / 0 / 0 / 0 |
| relative ×8 | 3.3 / 4.0 / 2.4 / 2.0 | 16 / 16 / 10 / 10 | 40.4 / 43.3 / 26.8 / 25.1 |
| relative ×12 | 2.4 / 2.8 / 1.9 / 1.6 | 24 / 26 / 16 / 16 | 15.2 / 16.1 / 14.6 / 12.8 |
| **relative ×16 (chosen)** | **2.1 / 1.7 / 1.6 / 1.3** | **34 / 34 / 20 / 20** | **4.4 / 4.5 / 8.0 / 6.3** |
| relative ×24 | 3.0 / 1.6 / 1.5 / 1.5 | 58 / 62 / 32 / 34 | 1.4 / 1.8 / 2.1 / 1.0 |
| relative ×32 | 5.0 / 3.7 / 2.1 / 2.4 | 78 / 80 / 48 / 52 | 0.4 / 0.8 / 0.3 / 0.0 |
| relative ×48 | 8.9 / 7.8 / 3.8 / 4.3 | 126 / 130 / 78 / 84 | 0.7 / 0.4 / 0.0 / 0.1 |

**How ×16 was chosen:** score = height RMSE + 0.1·|recovery-time error| + 0.3·|hop error|, averaged over the two **training** clips only (0536, 0537). ×16 has the lowest training score (3.30; absolute damping 6.29) and a test score of 2.99 (absolute 3.35). The held-out clips were reported but not used to pick it. The factors are on a coarse grid (8, 12, 16, 24, 32, 48), so ×16 is "best of the grid", not a precise optimum.

## 4. What it does to the comparison
Held-out height error 1.6 / 1.3 % (test mean 1.4 %), the lowest of every model; hop 4-8 mm like the real 3-7 mm. See [../../../evaluation/model_comparison/README.md](../../../evaluation/model_comparison/README.md) (row "axisymmetric FEM, damping relative to centre of mass ×16 (hop)").

## 5. Limitations
- **Not refitted jointly.** E (38 kPa), ν (0.10) and friction (1.78 / 1.75) were fitted with absolute damping; here only α was rescaled. A joint refit would be expensive (α·dt must stay ≤ ~0.18, so dt falls to a few microseconds; one forward run costs ~7 s against 2 s).
- **Hop timing and size.** The modelled hop starts about 5 ms after separation; the real one starts about 20 ms after, as a series of 4, 2 and 1 mm hops. On clip 0538 ×16 hops about 8 mm against 3.3 real (×24 fits that clip's hop better but is too slow on the others).
- **Recovery a little fast on the held-out clips** (20 ms against 29 / 25).
- **The multiplier is empirical,** chosen on a coarse grid from two clips; it has no physical meaning on its own. Friction of 1.8 or suction with the tin may add to the real hop and are not modelled.
- **MPM** has no relative-damping option yet.

## 6. Run
```bash
./run.sh      # needs ../fem_axisymmetric_warp/outputs/params_fem.json and the SAM 2 tracking; ~10 min on a GPU
```
`src/hop_experiment.py` (×1-×8 test, `outputs/hop_experiment.txt`), `src/hop_scan.py` (the scan), `src/render_hop_experiment.py` (videos with real | absolute | ×12 | ×16 | ×24 and lift plots), `src/render_hop16.py` (real vs ×16 side and oblique). Solver code is imported from `../fem_axisymmetric_warp/src/`.

## 7. Outputs
- `outputs/hop_experiment_IMG_0538.mp4`, `hop_experiment_IMG_0536.mp4`: the real clip beside the absolute-damping model and ×12, ×16, ×24 (zoomed out, time zero = separation, slowed 8×).
- `outputs/hop_experiment_lift_IMG_0538.png`, `..._0536.png`: bottom-edge lift against time, real vs each variant.
- `outputs/real_vs_fem_hop16_IMG_0536.mp4`, `..._0538.mp4`, `..._0539.mp4`: real | FEM ×16 side | oblique.
- `outputs/hop_scan.json`, `hop_scan.png`, `hop_experiment.txt`.
