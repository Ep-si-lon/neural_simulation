"""Fit the 3D foam-core ball to measured SHAPE over time: height, bottom lift, max width W and squareness n (from the silhouette fit in tracking/src/shape.py).
The simulated mesh silhouette is analysed with the same width-profile fit, so measured and simulated features are like for like.
Run: models/mesh_3d/foam_core_shape_fit/run.sh   (split: train 0536+0537, test 0538+0539)"""
import json
import numpy as np
from scipy.optimize import least_squares
from common import CLIPS
from clip_prep import prep, HORIZON
from scenario3d import scenario, measured, REC

def residuals_for(p, c, name, meas):
    T, F = scenario(p, c); tm, M = meas[name]; out = []
    h = np.interp(c['t'], T, F[:, 0]); l = np.interp(c['t'], T, F[:, 1])
    W = np.interp(tm, T, F[:, 2]); n = np.interp(tm, T, F[:, 3])
    if not np.all(np.isfinite(np.r_[h, l, W, n])): h, l, W, n = (np.full_like(a, 3.0) for a in (h, l, W, n))
    return h, l, W, n, tm, M

def res(p, cs, meas):
    out = []
    for name, c in cs:
        h, l, W, n, tm, M = residuals_for(p, c, name, meas)
        out += [h - c['h'] / c['rest'], l - c['lift'] / c['rest'], 3 * (W - M[:, 0]), 0.05 * (n - M[:, 1])]
    return np.concatenate(out)

def fit(cs, meas, starts=((128, 321, 778, 18.7), (1500, 30, 750, 19.0))):
    best = None
    for s in starts:
        r = least_squares(res, np.log(s), args=(cs, meas), bounds=(np.log([1e2, 1e1, 1e1, 0.1]), np.log([2e6, 2e6, 2e6, 50.0])), diff_step=5e-2, loss='soft_l1', f_scale=0.03, max_nfev=20)
        print('   start', s, 'cost', round(r.cost, 4), 'params', np.exp(r.x).round(1), flush=True)
        if best is None or r.cost < best.cost: best = r
    return best.x

def score(p, c, name, meas):
    h, l, W, n, tm, M = residuals_for(p, c, name, meas); r = c['rest']
    return 100 * np.sqrt(np.mean((h - c['h'] / r) ** 2)), 100 * np.sqrt(np.mean((l - c['lift'] / r) ** 2)), 100 * np.sqrt(np.mean((W - M[:, 0]) ** 2)), np.sqrt(np.mean((n - M[:, 1]) ** 2))

if __name__ == '__main__':
    cs = {n: prep(n) for n in CLIPS}; meas = {n: measured(n, cs[n]) for n in CLIPS}
    print('shape fit: train 0536+0537 -> test 0538, 0539', flush=True)
    p = fit([(n, cs[n]) for n in CLIPS[:2]], meas); json.dump({'split': list(np.exp(p))}, open('models/mesh_3d/foam_core_shape_fit/outputs/params_shape.json', 'w'), indent=1)
    for n in CLIPS:
        a, b, w, nn = score(p, cs[n], n, meas)
        print(f'  {n} ({"train" if n in CLIPS[:2] else "TEST"}): height {a:.1f}%  lift {b:.1f}%  width {w:.1f}% (of rest width)  squareness n RMSE {nn:.2f}', flush=True)
