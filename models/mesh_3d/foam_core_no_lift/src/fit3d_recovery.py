"""Refit the 3D foam-core ball on 0536+0537 using ONLY the shape-recovery signals (height, width, squareness n); hop/lift is ignored.
Run: models/mesh_3d/foam_core_no_lift/run.sh  -> outputs/params_3d.json"""
import json
import numpy as np
from scipy.optimize import least_squares
from common import CLIPS
from clip_prep import prep, HORIZON
from scenario3d import scenario, measured, REC

def res(p, cs, meas):
    out = []
    for name, c in cs:
        T, F = scenario(p, c); tm, M = meas[name]
        h = np.interp(c['t'], T, F[:, 0]); W = np.interp(tm, T, F[:, 2]); n = np.interp(tm, T, F[:, 3])
        if not np.all(np.isfinite(np.r_[h, W, n])): h, W, n = (np.full_like(a, 3.0) for a in (h, W, n))
        out += [h - c['h'] / c['rest'], 3 * (W - M[:, 0]), 0.05 * (n - M[:, 1])]   # no lift term: jumping is neglected
    return np.concatenate(out)

if __name__ == '__main__':
    cs = {n: prep(n) for n in CLIPS}; meas = {n: measured(n, cs[n]) for n in CLIPS}; train = [(n, cs[n]) for n in CLIPS[:2]]
    best = None
    for s in ((127, 276, 1000, 23.0), (500, 43, 1190, 23.0)):
        r = least_squares(res, np.log(s), args=(train, meas), bounds=(np.log([1e2, 1e1, 1e1, 0.1]), np.log([2e6, 2e6, 2e6, 50.0])), diff_step=5e-2, loss='soft_l1', f_scale=0.03, max_nfev=20)
        print('start', s, 'cost', round(r.cost, 4), 'params', np.exp(r.x).round(1), flush=True)
        if best is None or r.cost < best.cost: best = r
    json.dump({'ks_kb_kr_cd': list(np.exp(best.x))}, open('models/mesh_3d/foam_core_no_lift/outputs/params_3d.json', 'w'), indent=1); print('done')
