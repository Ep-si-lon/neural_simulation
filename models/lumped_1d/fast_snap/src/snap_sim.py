"""Fast-snap variant of src/sim.py. Same two-mass ball, but the spring has a second, much stiffer regime in deep compression:
    F = k*x + k_hi*max(x - x0, 0) - c*hdot          (x = rest - h, x0 = fraction of rest height)
so the ball snaps back fast out of deep compression, then hands over to the soft linear spring-damper for the slow tail.
Run from repo root:  models/lumped_1d/fast_snap/run.sh"""
import json
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares
from common import CLIPS
from clip_prep import prep, rmse, baselines, G, KT, ZT, SPLIT

def simulate(p, c, t_eval=None):
    k, cc, khi, x0f = np.exp(p[0]), np.exp(p[1]), np.exp(p[2]), p[3]
    h0, g, x0 = c['rest'], G * c['pxm'], p[3] * c['rest']
    mb, mt = SPLIT, 1 - SPLIT
    def f(_, s):
        yb, vb, yt, vt = s; h = yt - yb; x = h0 - h
        fi = k * x + khi * max(x - x0, 0.0) - cc * (vt - vb)
        tab = (-KT * yb - 2 * ZT * np.sqrt(KT) * vb) if yb < 0 else 0.0
        return [vb, (tab - fi) / mb - g, vt, fi / mt - g]
    t_eval = c['t'] if t_eval is None else t_eval
    sol = solve_ivp(f, (0, t_eval[-1]), [0, 0, c['hc'], 0], t_eval=t_eval, method='Radau', rtol=1e-6, atol=1e-6)
    yb, yt = sol.y[0], sol.y[2]
    return yt - yb, yt, np.clip(yb, 0, None)

def res(p, cs):
    out = []
    for c in cs:
        h, top, lift = simulate(p, c)
        if len(h) != len(c['t']): return np.full(sum(len(x['t']) * 3 for x in cs), 1e3)
        out += [(h - c['h']) / c['rest'], (top - c['top']) / c['rest'], (lift - c['lift']) / c['rest']]
    return np.concatenate(out)

def fit(cs):
    best = None
    for k0, c0, kh0, x00 in ((5e3, 150, 5e4, 0.2), (1.5e4, 300, 2e5, 0.1), (5e3, 80, 1e6, 0.3)):
        r = least_squares(res, [np.log(k0), np.log(c0), np.log(kh0), x00], args=(cs,), loss='soft_l1', f_scale=0.03, max_nfev=80,
                          bounds=([5, 0, 5, 0.02], [14, 8, 17, 0.6]))
        if best is None or r.cost < best.cost: best = r
    return best.x

if __name__ == '__main__':
    cs = {n: prep(n) for n in CLIPS}; saved = {}
    def report(train, test):
        p = fit([cs[n] for n in train]); k, c_, kh, x0 = np.exp(p[0]), np.exp(p[1]), np.exp(p[2]), p[3]
        saved[test[0] if len(test) == 1 else 'split'] = [k, c_, kh, x0]
        print(f'  train {train}: k={k:.0f} c={c_:.0f} k_hi={kh:.0f} x0={100*x0:.0f}% of rest')
        for n in test:
            h, top, lift = simulate(p, cs[n]); a, b, l = rmse(cs[n], h, top, lift)
            he, hs = baselines(train, cs, cs[n]); be = 100 * np.sqrt(np.mean((he - cs[n]['h']) ** 2)) / cs[n]['rest']
            print(f"    {n}: height RMSE fast-snap {a:.1f}% | exp-recovery {be:.1f}%   top {b:.1f}%  lift {l:.1f}%")
    print('split 536+537 -> 538, 539'); report(CLIPS[:2], CLIPS[2:])
    print('leave-one-out')
    for hld in CLIPS: report([c for c in CLIPS if c != hld], [hld])
    json.dump(saved, open('models/lumped_1d/fast_snap/outputs/params.json', 'w'), indent=1)
