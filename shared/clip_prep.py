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
    r = up                                                       # separation frame: the ball is free from here (squareness n drops, height ~70 % of rest)
    p = up
    while h[p] > hold + 0.02 * rest: p -= 1                      # last frame still on the pressed plateau = start of the tin's retreat
    b_ref = np.median(d['bottom_px'][-len(h) // 5:])
    top_up = (b_ref - medfilt(d['top_px'], 5))                   # top edge above table-contact bottom reference (px)
    lift = np.clip(b_ref - d['bottom_px'], 0, None)
    s = (t >= t[r]) & (t <= t[r] + HORIZON)
    tin = (t[p:r + 1] - t[p], np.maximum(h[p:r + 1], hold) / (rest / DIAM_M))      # tin retreat: time since plateau end, top-edge height (m) while the tin still carries the ball
    return dict(name=name, rest=rest, hc=hold, pxm=rest / DIAM_M, i_rel=r, i_plat=p, tin=tin, t=t[s] - t[r], h=h[s], top=top_up[s], lift=lift[s],
                full_t=t, full_h=h, full_top=top_up, width=d['width_px'], b_ref=b_ref)

def rmse(c, h, top, lift):
    s = lambda a, b: 100 * np.sqrt(np.mean((a - b) ** 2)) / c['rest']
    return s(h, c['h']), s(top, c['top']), s(lift, c['lift'])

def baselines(train, cs, c):
    # exp baseline: h(t) = rest - (rest-hc) exp(-t/tau), tau fit on training clips
    f = lambda x: np.concatenate([(cs[n]['rest'] - (cs[n]['rest'] - cs[n]['hc']) * np.exp(-cs[n]['t'] / np.exp(x[0])) - cs[n]['h']) / cs[n]['rest'] for n in train])
    tau = np.exp(least_squares(f, [np.log(.03)]).x[0])
    return c['rest'] - (c['rest'] - c['hc']) * np.exp(-c['t'] / tau), np.full_like(c['t'], c['hc'])



def tin_plate_accel(t, yt, vt, tin, pxm):
    """Acceleration (px/s^2, per unit mass) on the top mass from the tin plate while it retreats along the measured trajectory
    tin = (time since plateau end, top-edge height in m); zero after the ball separates from it (t >= tin duration) or when tin is None."""
    if tin is None or t >= tin[0][-1]: return 0.0
    zp = np.interp(t, tin[0], tin[1]) * pxm; vp = (np.interp(t + 1e-4, tin[0], tin[1]) - np.interp(max(t - 1e-4, 0.0), tin[0], tin[1])) / 2e-4 * pxm
    return (-KT * (yt - zp) - 2 * ZT * np.sqrt(KT) * max(vt - vp, 0.0)) if yt > zp else 0.0
