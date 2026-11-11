"""Why there is no hop: the FEM with the fitted material, damped (a) on the absolute node velocity (as fitted, no hop) or (b) only relative to the ball's centre of mass (keeps the hop), at several damping strengths."""
import sys, json, numpy as np
sys.path[:0] = ['shared', 'tracking/src', 'models/continuum/fem_axisymmetric_warp/src']   # run from the repo root with TRACKER=sam2
import warp as wp
from fem_axi import FEM
from fit_fem import simulate_clip
from clip_prep import prep
P = json.load(open('models/continuum/fem_axisymmetric_warp/outputs/params_fem.json')); base = np.array(P['prm']); fem = FEM(); tg = np.arange(0, 0.25, 0.002)
CL = ['IMG_0536', 'IMG_0537', 'IMG_0538', 'IMG_0539']; cs = {n: prep(n) for n in CL}
def metrics(n, p, rel):
    cd, plan, x = simulate_clip(fem, n, p, rel=rel); c = cs[n]; k = np.clip(np.round((plan['n_sep'] * plan['dt'] + tg) / plan['dt']).astype(int), 0, plan['n'])
    h = (x[k, fem.top, 1] - x[k, fem.bot, 1]) / 0.067; lift = np.maximum(x[k, fem.bot, 1], 0) * 1e3
    ht = np.interp(tg, c['t'], c['h'] / c['rest']); rmse = 100 * np.sqrt(np.mean((h - ht) ** 2)); mono = np.fmax.accumulate(h); i = np.flatnonzero(mono >= 0.95)
    return rmse, (tg[i[0]] * 1e3 if len(i) else np.nan), lift.max(), np.isfinite(x).all()
print('real hop (mm):', {n: round(float(np.nanmax(cs[n]['lift'] / cs[n]['rest'] * 67)), 1) for n in CL})
for label, rel, mult in (('absolute damping (as fitted)', 0.0, 1.0), ('centre-of-mass-relative, alpha x1', 1.0, 1.0), ('relative, alpha x2', 1.0, 2.0), ('relative, alpha x4', 1.0, 4.0), ('relative, alpha x8', 1.0, 8.0)):
    p = base.copy(); p[2] *= mult
    row = [metrics(n, p, rel) for n in CL]
    print(f'{label:34s} ' + '  '.join(f'{n[-4:]}: rmse {r[0]:.1f}% t95 {r[1]:.0f}ms hop {r[2]:.1f}mm' + ('' if r[3] else ' NaN') for n, r in zip(CL, row)))
