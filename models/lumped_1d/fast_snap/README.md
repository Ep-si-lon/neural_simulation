# Fast-snap variant (negative result)

**Idea.** The two-mass model recovers too slowly because one spring cannot give both a fast snap-back and a slow tail. Add a much stiffer spring regime in deep compression so the ball snaps back quickly, then hands over to the soft spring.

## Formulas
Same two-mass system as `../two_mass_spring`, with the internal force replaced by

`F_int = k x + k_hi · max(x − x₀, 0) − c ḣ`, `x = h_rest − h`, `x₀ = x0f · h_rest`.

## Parameters
| Symbol | Meaning | Kind | Value |
| --- | --- | --- | --- |
| g, mass split, table K_T, ζ_T | as in two_mass_spring | fixed | 9.81, 0.5/0.5, 4×10⁶, 0.3 |
| h_rest, h_c, release time | rest height, compressed height, release | measured | — |
| k, c | base stiffness / damping per unit mass | fitted | 12,900–18,900; 331–503 |
| k_hi | extra deep-compression stiffness | fitted | 280–10,000 |
| x0f | threshold, fraction of rest height | fitted | 31–60 % |

## Assumptions and limitations
Same as the two-mass model, plus a piecewise-linear stiffening.
**No improvement:** height RMSE is within 0.2 points of the two-mass model on every held-out clip (6.2–8.3 % vs 3.8–5.8 % for the exponential). The fit pushed `k_hi` small, so the extra regime is barely used.
Remaining candidates (untested): the first 1–2 frames after the tin leaves are hand-driven or corrupted by tin glare, so they are not ball dynamics.

## Run
`./run.sh` (about 5 min). Code `src/snap_sim.py`. Outputs `outputs/results.txt`, `params.json`.
