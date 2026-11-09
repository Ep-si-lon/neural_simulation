"""Fit the 3D shell's (ks, kb, p0, cd) to flat-plate press+release clips; predict held-out clips with no refit.
Scenario per clip: relax -> plate presses quasi-statically to the clip's measured compressed height -> plate removed -> simulate 0.25 s.
Targets: height(t)/rest, bottom lift(t)/rest, and hold-state width/rest. Run: PYTHONPATH=src:sim3d python -u sim3d/fit3d.py"""
import sys, json
import numpy as np
from scipy.optimize import least_squares
from common import CLIPS
from sim import prep, HORIZON
from ball3d import Ball

DT, SUB = 4e-5, 2
_relaxed = {}

def scenario(p, c, rec=1e-3):
    ks, kb, p0, cd = np.exp(p)
    b = Ball(sub=SUB, ks=ks, kb=kb, p0=p0, cd=cd); b.run(0.08, DT, damp=80); rest = b.shape()[0]
    target = rest * c['hc'] / c['rest']
    for i in range(40): b.tool = ('plate', rest - (rest - target) * (i + 1) / 40, 0); b.run(0.0015, DT, damp=80)
    hold = b.shape(); b.tool = None; ts, hs, ls = [0.0], [hold[0] / rest], [0.0]
    for i in range(int(HORIZON / rec)):
        b.run(rec, DT); s = b.shape(); ts.append((i + 1) * rec); hs.append(s[0] / rest); ls.append(max(s[2], 0) / rest)
    return np.array(ts), np.array(hs), np.array(ls), hold[1] / rest

def pred(p, c):
    ts, hs, ls, wh = scenario(p, c)
    return np.interp(c['t'], ts, hs), np.interp(c['t'], ts, ls), wh

def hold_width_ratio(c):
    w = c['width']; return np.median(w[c['i_rel'] - 30:c['i_rel'] - 5]) / np.median(w[-len(w) // 5:])

def res(p, cs):
    out = []
    for c in cs:
        h, l, wh = pred(p, c)
        out += [(h - c['h'] / c['rest']), (l - c['lift'] / c['rest']), [3 * (wh - hold_width_ratio(c))]]
    return np.concatenate([np.ravel(o) for o in out])

def fit(cs, starts=((3e4, 3e3, 3e3, 5.0), (3e5, 3e4, 3e4, 30.0))):
    best = None
    for s in starts:
        r = least_squares(res, np.log(s), args=(cs,), bounds=(np.log([1e2, 1e1, 1e1, 0.1]), np.log([1e8, 1e8, 1e8, 1e3])), diff_step=5e-2, loss='soft_l1', f_scale=0.03, max_nfev=30)
        print('   start', s, 'cost', round(r.cost, 4), 'params', np.exp(r.x).round(1), flush=True)
        if best is None or r.cost < best.cost: best = r
    return best.x

def score(p, c):
    h, l, wh = pred(p, c); r = c['rest']
    return 100 * np.sqrt(np.mean((h - c['h'] / r) ** 2)), 100 * np.sqrt(np.mean((l - c['lift'] / r) ** 2)), wh, hold_width_ratio(c)

if __name__ == '__main__':
    cs = {n: prep(n) for n in CLIPS}; saved = {}
    print('split: train 0536+0537 -> test 0538, 0539', flush=True)
    p = fit([cs[n] for n in CLIPS[:2]]); saved['split'] = list(np.exp(p))
    for n in CLIPS:
        a, b, wp, wm = score(p, cs[n]); print(f'  {n} ({"train" if n in CLIPS[:2] else "TEST"}): height RMSE {a:.1f}%  lift RMSE {b:.1f}%  hold width sim {wp:.3f} vs measured {wm:.3f} (x rest)', flush=True)
    json.dump(saved, open('sim3d/params.json', 'w'), indent=1)
