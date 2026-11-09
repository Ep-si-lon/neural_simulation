"""Same as foam_core_no_lift/src/fit3d_recovery.py but the residual also contains the bottom-lift (hop) term, weighted LIFT_W x.
Train 0536+0537. Run: models/mesh_3d/foam_core_with_lift/run.sh -> outputs/params_3d_lift.json"""
import json
import numpy as np
from scipy.optimize import least_squares
from common import CLIPS
from clip_prep import prep
from scenario3d import scenario, measured

LIFT_W = 4.0

def res(p, cs, meas):
    out = []
    for name, c in cs:
        T, F = scenario(p, c); tm, M = meas[name]
        h = np.interp(c['t'], T, F[:, 0]); l = np.interp(c['t'], T, F[:, 1]); W = np.interp(tm, T, F[:, 2]); n = np.interp(tm, T, F[:, 3])
        if not np.all(np.isfinite(np.r_[h, l, W, n])): h, l, W, n = (np.full_like(a, 3.0) for a in (h, l, W, n))
        out += [h - c['h'] / c['rest'], LIFT_W * (l - c['lift'] / c['rest']), 3 * (W - M[:, 0]), 0.05 * (n - M[:, 1])]
    return np.concatenate(out)

if __name__ == '__main__':
    cs = {n: prep(n) for n in CLIPS}; meas = {n: measured(n, cs[n]) for n in CLIPS}; train = [(n, cs[n]) for n in CLIPS[:2]]
    best = None
    for s in ((110.6, 950.7, 2576.9, 34.5), (126.6, 276.4, 1000.5, 23.0)):     # starts: hopping no-lift fit, and the earlier non-hopping lift fit
        r = least_squares(res, np.log(s), args=(train, meas), bounds=(np.log([1e2, 1e1, 1e1, 0.1]), np.log([2e6, 2e6, 2e6, 50.0])), diff_step=5e-2, loss='soft_l1', f_scale=0.03, max_nfev=20)
        print('start', s, 'cost', round(r.cost, 4), 'params', np.exp(r.x).round(1), flush=True)
        if best is None or r.cost < best.cost: best = r
    json.dump({'ks_kb_kr_cd': list(np.exp(best.x))}, open('models/mesh_3d/foam_core_with_lift/outputs/params_3d_lift.json', 'w'), indent=1); print('done')
