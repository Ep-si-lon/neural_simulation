"""Shared by the lumped models and the 3D fits: constants and clip preparation (release instant, compressed height, edge tracks cut to a window),
plus the error metric and the exponential baseline used in every comparison."""
import numpy as np
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

def rmse(c, h, top, lift):
    s = lambda a, b: 100 * np.sqrt(np.mean((a - b) ** 2)) / c['rest']
    return s(h, c['h']), s(top, c['top']), s(lift, c['lift'])

def baselines(train, cs, c):
    # exp baseline: h(t) = rest - (rest-hc) exp(-t/tau), tau fit on training clips
    f = lambda x: np.concatenate([(cs[n]['rest'] - (cs[n]['rest'] - cs[n]['hc']) * np.exp(-cs[n]['t'] / np.exp(x[0])) - cs[n]['h']) / cs[n]['rest'] for n in train])
    tau = np.exp(least_squares(f, [np.log(.03)]).x[0])
    return c['rest'] - (c['rest'] - c['hc']) * np.exp(-c['t'] / tau), np.full_like(c['t'], c['hc'])

