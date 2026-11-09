"""Two-mass deformable-ball simulation (vertical): bottom mass on the table, top mass, nonlinear spring-damper between them.
Squeeze: top follows the tin (prescribed = measured). Release: tin leaves, ball is simulated from its compressed state.
Units: px and s, masses normalised to 1 (k, c are per unit mass); gravity from the 6.7 cm diameter scale."""
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares
from scipy.signal import medfilt
from common import CLIPS, load

G, DIAM_M, SPLIT = 9.81, 0.067, 0.5
KT, ZT = 4e6, 0.3                       # stiff table penalty spring (1/s^2) and its damping ratio (fixed, numerical)
HORIZON = 0.25                          # s simulated after release

def prep(name):
    d, h = load(name)
    t = d['pts_s']; rest = np.median(h[-len(h) // 5:])
    up = [i for i in range(1, len(h)) if h[i - 1] <= 0.5 * (h.min() + rest) < h[i]][-1]
    hold = np.median(h[up - 60:up - 15])                        # compressed plateau just before release
    r = up
    while h[r] < hold + 0.02 * rest: r -= 1                      # last frame still on the plateau = release instant
    b_ref = np.median(d['bottom_px'][-len(h) // 5:])
    top_up = (b_ref - medfilt(d['top_px'], 5))                   # top edge above table-contact bottom reference (px)
    lift = np.clip(b_ref - d['bottom_px'], 0, None)
    s = (t >= t[r]) & (t <= t[r] + HORIZON)
    return dict(name=name, rest=rest, hc=hold, pxm=rest / DIAM_M, i_rel=r, t=t[s] - t[r], h=h[s], top=top_up[s], lift=lift[s],
                full_t=t, full_h=h, full_top=top_up, width=d['width_px'], b_ref=b_ref)

def simulate(p, c, t_eval=None):
    k, cc, z3 = np.exp(p[:3]); k3 = k * z3 / c['rest'] ** 2; h0 = c['rest']; g = G * c['pxm']
    mb, mt = SPLIT, 1 - SPLIT
    def f(_, s):
        yb, vb, yt, vt = s; h = yt - yb; hd = vt - vb; x = h0 - h
        fi = k * x + k3 * x ** 3 + (-cc * hd)                      # internal force pushing top up / bottom down
        ft = -KT * 0 + fi
        tab = (-KT * yb - 2 * ZT * np.sqrt(KT) * vb) if yb < 0 else 0.0
        return [vb, (tab - fi) / mb - g, vt, ft / mt - g]
    t_eval = c['t'] if t_eval is None else t_eval
    sol = solve_ivp(f, (0, t_eval[-1]), [0, 0, c['hc'], 0], t_eval=t_eval, method='Radau', rtol=1e-6, atol=1e-6)
    yb, yt = sol.y[0], sol.y[2]
    return yt - yb, yt, np.clip(yb, 0, None)                        # height, top above table, lift of bottom

def res(p, cs):
    out = []
    for c in cs:
        h, top, lift = simulate(p, c); n = len(h)
        if n != len(c['t']): return np.full(sum(len(x['t']) * 3 for x in cs), 1e3)
        out += [(h - c['h']) / c['rest'], (top - c['top']) / c['rest'], (lift - c['lift']) / c['rest']]
    return np.concatenate(out)

def fit(cs):
    best = None
    for k0, z0 in ((1e4, .5), (1e5, 3.0), (3e3, 20.0)):
        for c0 in (50, 300):
            r = least_squares(res, [np.log(k0), np.log(c0), np.log(z0)], args=(cs,), bounds=([5, 0, -8], [14, 8, 7]), max_nfev=80, loss='soft_l1', f_scale=0.03)
            if best is None or r.cost < best.cost: best = r
    return best.x

def rmse(c, h, top, lift):
    s = lambda a, b: 100 * np.sqrt(np.mean((a - b) ** 2)) / c['rest']
    return s(h, c['h']), s(top, c['top']), s(lift, c['lift'])

def baselines(train, cs, c):
    # exp baseline: h(t) = rest - (rest-hc) exp(-t/tau), tau fit on training clips
    f = lambda x: np.concatenate([(cs[n]['rest'] - (cs[n]['rest'] - cs[n]['hc']) * np.exp(-cs[n]['t'] / np.exp(x[0])) - cs[n]['h']) / cs[n]['rest'] for n in train])
    tau = np.exp(least_squares(f, [np.log(.03)]).x[0])
    return c['rest'] - (c['rest'] - c['hc']) * np.exp(-c['t'] / tau), np.full_like(c['t'], c['hc'])

if __name__ == '__main__':
    cs = {n: prep(n) for n in CLIPS}
    for n in CLIPS: print(n, f"hc={cs[n]['hc']:.0f}px ({100*cs[n]['hc']/cs[n]['rest']:.0f}% of rest) n={len(cs[n]['t'])}")
    import json; saved = {}
    def report(train, test):
        p = fit([cs[n] for n in train]); k, c_, z3 = np.exp(p); saved[test[0] if len(test) == 1 else 'split'] = list(np.exp(p))
        print(f'  train {train}: k={k:.0f}/s^2 (f={np.sqrt(k)/2/np.pi:.1f}Hz) c={c_:.0f}/s cubic={z3:.2f}')
        for n in test:
            h, top, lift = simulate(p, cs[n]); a, b, l = rmse(cs[n], h, top, lift)
            he, hs = baselines(train, cs, cs[n]); be = 100 * np.sqrt(np.mean((he - cs[n]['h']) ** 2)) / cs[n]['rest']; bs = 100 * np.sqrt(np.mean((hs - cs[n]['h']) ** 2)) / cs[n]['rest']
            print(f"    {n}: height RMSE model {a:.1f}% | exp-recovery {be:.1f}% | stay-compressed {bs:.1f}%   top {b:.1f}%  lift {l:.1f}% (of ball height)")
    print('split 536+537 -> 538, 539'); report(CLIPS[:2], CLIPS[2:])
    print('leave-one-out')
    for hld in CLIPS: report([c for c in CLIPS if c != hld], [hld])
    json.dump(saved, open('out/sim_params.json', 'w'), indent=1)
