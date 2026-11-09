"""Bounce + overdamped height-recovery model, fitted on training clips, predicted (no refit) on held-out clips.
State after the first apex (v=0): lift A of the ball above the table, height deviation delta_a from rest.
  top_up(t) = L(t; A, e) + rest * delta(t),   delta(t) = delta_a * exp(-t/tau)
L = rigid ballistic hops under gravity with restitution e. Time base = file timestamps (verified by g ~ 9.8)."""
import numpy as np
from scipy.signal import find_peaks
from scipy.optimize import least_squares
from scipy.signal import medfilt
from common import CLIPS, load

G, DIAM_M = 9.81, 0.067
WIN = 0.20                                           # s after first apex

def prep(name):
    d, h = load(name)
    rest = np.median(h[-len(h) // 5:])
    up = [i for i in range(1, len(h)) if h[i - 1] <= 0.5 * (h.min() + rest) < h[i]][-1]
    t, top = d['pts_s'], d['top_px'].copy()
    bad = (d['bottom_px'] - top) / rest - 1 > 0.04       # ball cannot be >4% taller than rest: tin glare on the top edge (0538)
    top[bad] = np.interp(np.flatnonzero(bad), np.flatnonzero(~bad), top[~bad]); top = medfilt(top, 5)
    a = up + int(np.argmin(top[up:up + 30]))         # first apex of the hop
    rest_top = np.median(top[-len(top) // 5:])
    pxm = rest / DIAM_M                              # px per metre from measured 6.7 cm diameter
    s = (t >= t[a]) & (t <= t[a] + WIN)
    return dict(name=name, ta=t[a], a=a, t=t[s] - t[a], y=rest_top - top[s], h=h[s] / rest - 1, rest=rest, pxm=pxm)

def lift(t, A, e, gpx, tc):
    tf = np.sqrt(2 * A / gpx); L = np.where(t < tf, A - gpx * t ** 2 / 2, 0.0); s = tf + tc; v = e * gpx * tf   # tc: contact dwell on the table, L=0
    for _ in range(10):
        T = 2 * v / gpx; tau = t - s
        L = np.where((tau >= 0) & (tau < T), v * tau - gpx * tau ** 2 / 2, L); s += T + tc; v *= e
    return L

def predict(c, e, tau, tc, shift=0.0):
    t = c['t'] - shift; da = c['h'][0]; A = max(c['y'][0] - c['rest'] * da, 1.0)
    return lift(np.clip(t, 0, None), A, e, G * c['pxm'], tc) + c['rest'] * da * np.exp(-np.clip(t, 0, None) / tau)

def fit(cs):
    # tau from the height signal alone (cleaner than the top edge), pooled over training clips
    rh = lambda x: np.concatenate([c['h'][0] * np.exp(-c['t'] / np.exp(x[0])) - c['h'] for c in cs])
    tau = np.exp(least_squares(rh, [np.log(.1)], bounds=([np.log(.01)], [np.log(1.0)])).x[0])
    def res(x):
        e, tc = np.exp(x[0]), x[1] * 1e-3
        return np.concatenate([(predict(c, e, tau, tc, x[2 + i] * 1e-3) - c['y']) / c['rest'] for i, c in enumerate(cs)])
    best = min((least_squares(res, [np.log(e0), tc0] + [0] * len(cs), bounds=([-5, 0] + [-2] * len(cs), [0, 40] + [2] * len(cs)))
                for e0 in (.3, .5, .7, .9) for tc0 in (2, 10, 20)), key=lambda r: r.cost)
    return np.exp(best.x[0]), tau, best.x[1] * 1e-3

def rmse_pct(c, y): return 100 * np.sqrt(np.mean((y - c['y']) ** 2)) / c['rest']

def evaluate(train, test, cs):
    e, tau, tc = fit([cs[n] for n in train])
    # baseline 2: single exponential on the top-edge signal, tau fitted on training clips
    def r2(x): return np.concatenate([(cs[n]['y'][0] * np.exp(-cs[n]['t'] / np.exp(x[0])) - cs[n]['y']) / cs[n]['rest'] for n in train])
    tb = np.exp(least_squares(r2, [np.log(.03)]).x[0])
    out = []
    for n in test:
        c = cs[n]
        out.append((n, rmse_pct(c, predict(c, e, tau, tc)), rmse_pct(c, c['y'][0] * np.exp(-c['t'] / tb)), rmse_pct(c, 0 * c['y'])))
    return e, tau, tc, out

if __name__ == '__main__':
    cs = {n: prep(n) for n in CLIPS}
    print('per-clip fit (e, tau ms):')
    for n in CLIPS: e, tau, tc = fit([cs[n]]); print(f'  {n}: e={e:.2f} tau={tau*1e3:.0f}ms tc={tc*1e3:.0f}ms')
    print('\nsplit: train 0536+0537 -> test 0538, 0539 (no refit)'); e, tau, tc, o = evaluate(CLIPS[:2], CLIPS[2:], cs)
    print(f'  e={e:.2f} tau={tau*1e3:.0f}ms tc={tc*1e3:.0f}ms'); [print(f'  {n}: model {m:.2f}%  exp-baseline {b:.2f}%  rest-baseline {r:.2f}%  (RMSE % of ball height)') for n, m, b, r in o]
    print('\nleave-one-clip-out:')
    for h in CLIPS:
        e, tau, tc, o = evaluate([c for c in CLIPS if c != h], [h], cs); n, m, b, r = o[0]
        print(f'  hold {h}: e={e:.2f} tau={tau*1e3:.0f}ms tc={tc*1e3:.0f}ms  model {m:.2f}%  exp {b:.2f}%  rest {r:.2f}%')
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 2, figsize=(12, 7))
    for a, h in zip(ax.ravel(), CLIPS):
        e, tau, tc = fit([cs[n] for n in CLIPS if n != h]); c = cs[h]
        a.plot(c['t'] * 1e3, c['y'], 'k.-', label='measured'); a.plot(c['t'] * 1e3, predict(c, e, tau, tc), 'r', label='model (held out)')
        a.set_title(f'{h}: e={e:.2f} tau={tau*1e3:.0f}ms tc={tc*1e3:.0f}ms'); a.set_xlabel('ms after first apex'); a.set_ylabel('top edge above rest (px)')
    ax[0, 0].legend(); plt.tight_layout(); plt.savefig('models/lumped_1d/bounce_recovery/outputs/loo_predictions.png', dpi=100)
