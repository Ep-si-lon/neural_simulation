"""Time to regain shape after release: real clips vs models trained on 0536+0537 and tested on 0538+0539. Jumping/hops are ignored.
Metrics (t = 0 at release, i.e. the last frame the ball is still held compressed):
  t95, t98 : first time the height reaches 95 % / 98 % of rest height      (all models)
  t_n      : first time squareness n <= 2.3, i.e. the outline is a plain ellipse again   (real + 3D model only)
Run: evaluation/recovery_time/run.sh  -> outputs/results.md, recovery_time.png"""
import json, os
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares
from scipy.signal import medfilt
from common import CLIPS, TRACK_OUT
from clip_prep import prep, HORIZON

TRAIN, TEST = CLIPS[:2], CLIPS[2:]
TG = np.arange(0, HORIZON, 5e-4)

def smooth(y, k=5):                                 # median filter with edge padding (scipy's zero-pads and fakes the first samples)
    return medfilt(np.pad(y, k // 2, mode='edge'), k)[k // 2:-(k // 2)]

def first_time(t, y, thr, above=True):
    i = np.flatnonzero(y >= thr) if above else np.flatnonzero(y <= thr)
    return float(t[i[0]]) if len(i) else np.nan

def real_curves(name, c):
    d = np.genfromtxt(f'{TRACK_OUT}/{name}_shape.csv', delimiter=',', names=True); pts = d['pts_s']; r = c['i_rel']
    s = (pts >= pts[r]) & (pts <= pts[r] + HORIZON); t = pts[s] - pts[r]
    h = smooth(c['h'] / c['rest']); n = smooth(d['n'][s])
    return t, h, n

def exp_model(train, cs):
    f = lambda x: np.concatenate([(1 - (1 - cs[n]['hc'] / cs[n]['rest']) * np.exp(-cs[n]['t'] / np.exp(x[0]))) - cs[n]['h'] / cs[n]['rest'] for n in train])
    tau = np.exp(least_squares(f, [np.log(.03)], loss='soft_l1', f_scale=0.03).x[0])
    return lambda c: 1 - (1 - c['hc'] / c['rest']) * np.exp(-TG / tau), dict(tau_ms=1e3 * tau)

def two_exp(p, c):                                 # fast + slow recovery: 1 - x0*(a*exp(-t/tau1) + (1-a)*exp(-t/tau2))
    a, t1, t2 = p; return 1 - (1 - c['hc'] / c['rest']) * (a * np.exp(-TG / t1) + (1 - a) * np.exp(-TG / t2))

def two_exp_model(train, cs):
    f = lambda p: np.concatenate([np.interp(cs[n]['t'], TG, two_exp(p, cs[n])) - cs[n]['h'] / cs[n]['rest'] for n in train])
    best = min((least_squares(f, s, loss='soft_l1', f_scale=0.03, bounds=([0, 1e-3, 1e-3], [1, 0.3, 1.0])) for s in ((.8, .01, .1), (.5, .02, .2), (.9, .005, .05))), key=lambda r: r.cost)
    a, t1, t2 = best.x; return (lambda c: two_exp(best.x, c)), dict(frac_fast=round(a, 2), tau_fast_ms=round(1e3 * t1, 1), tau_slow_ms=round(1e3 * t2, 1))

def sdof(p, c):                                   # bottom pinned on the table: one damped spring, x = (rest - h)/rest
    k, cc = np.exp(p); x0 = 1 - c['hc'] / c['rest']
    sol = solve_ivp(lambda t, s: [s[1], -cc * s[1] - k * s[0]], (0, TG[-1]), [x0, 0], t_eval=TG, rtol=1e-8, atol=1e-10)
    return 1 - sol.y[0]

def sdof_model(train, cs):
    f = lambda p: np.concatenate([np.interp(cs[n]['t'], TG, sdof(p, cs[n])) - cs[n]['h'] / cs[n]['rest'] for n in train])
    best = min((least_squares(f, np.log(s), loss='soft_l1', f_scale=0.03, bounds=([0, 0], [14, 9])) for s in ((1e3, 60), (1e4, 300), (1e5, 600))), key=lambda r: r.cost)
    k, cc = np.exp(best.x); return (lambda c: sdof(best.x, c)), dict(k=k, c=cc, zeta=cc / (2 * np.sqrt(k)))

def model3d(cs):
    from scenario3d import scenario
    pf = 'models/mesh_3d/foam_core_no_lift/outputs/params_3d.json'
    if not os.path.exists(pf): return None, {}
    P = np.log(json.load(open(pf))['ks_kb_kr_cd'])
    def run(c):
        T, F = scenario(P, c); return np.interp(TG, T, F[:, 0]), np.interp(TG, T, F[:, 3])
    return run, dict(params=[round(v, 1) for v in np.exp(P)])

if __name__ == '__main__':
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    cs = {n: prep(n) for n in CLIPS}
    exp_f, ep = exp_model(TRAIN, cs); sd_f, sp = sdof_model(TRAIN, cs); te_f, tp = two_exp_model(TRAIN, cs); m3, p3 = model3d(cs)
    rows, fig, ax = [], *plt.subplots(2, 4, figsize=(18, 7))
    for j, n in enumerate(CLIPS):
        c = cs[n]; t, h, nn = real_curves(n, c); tag = 'train' if n in TRAIN else 'TEST'
        row = dict(clip=n[-4:], split=tag, hold_pct=100 * c['hc'] / c['rest'], real=dict(t95=first_time(t, h, .95), t98=first_time(t, h, .98), tn=first_time(t, nn, 2.3, False)))
        ax[0, j].plot(t * 1e3, h, 'k.-', label='real'); ax[1, j].plot(t * 1e3, nn, 'k.-', label='real')
        for lab, f, col in (('exp', exp_f, 'tab:blue'), ('1-DOF spring', sd_f, 'tab:green'), ('fast+slow exp', te_f, 'tab:orange')):
            y = f(c); row[lab] = dict(t95=first_time(TG, y, .95), t98=first_time(TG, y, .98)); ax[0, j].plot(TG * 1e3, y, color=col, label=lab)
        if m3:
            y, ny = m3(c); row['3D foam'] = dict(t95=first_time(TG, y, .95), t98=first_time(TG, y, .98), tn=first_time(TG, ny, 2.3, False))
            ax[0, j].plot(TG * 1e3, y, color='tab:red', label='3D foam'); ax[1, j].plot(TG * 1e3, ny, color='tab:red', label='3D foam')
        ax[0, j].set_title(f'{n[-4:]} ({tag}), pressed to {row["hold_pct"]:.0f}%'); ax[0, j].set_ylabel('height / rest'); ax[1, j].set_ylabel('squareness n'); ax[1, j].set_xlabel('ms after release')
        rows.append(row)
    ax[0, 0].legend(fontsize=7); ax[1, 0].legend(fontsize=7); plt.tight_layout(); plt.savefig('evaluation/recovery_time/outputs/recovery_time.png', dpi=80)
    f = lambda v: 'never (>250)' if v is None or np.isnan(v) else f'{1e3*v:.0f}'
    L = ['| Clip | Set | Pressed to | Metric | Real (ms) | Exp | 1-DOF spring | Fast+slow exp | 3D foam |', '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in rows:
        for m, nm in (('t95', 'height 95 %'), ('t98', 'height 98 %'), ('tn', 'shape n<=2.3')):
            g = lambda k: f(r[k].get(m)) if k in r and m in r[k] else '-'
            L.append(f"| {r['clip']} | {r['split']} | {r['hold_pct']:.0f} % | {nm} | {f(r['real'][m])} | {g('exp')} | {g('1-DOF spring')} | {g('fast+slow exp')} | {g('3D foam')} |")
    out = '\n'.join(L) + f"\n\nFitted on 0536+0537: exponential {ep}; 1-DOF spring {sp}; fast+slow exp {tp}; 3D foam {p3}\n"
    open('evaluation/recovery_time/outputs/results.md', 'w').write(out); print(out)
