import numpy as np
from scipy.signal import medfilt
from scipy.optimize import least_squares

import os
TRACK_OUT = 'tracking/outputs_sam2' if os.environ.get('TRACKER') == 'sam2' else 'tracking/outputs'   # TRACKER=sam2 switches every model to the SAM 2 measurements (scripts run from the repo root)
W, H = 1920, 1080                  # video frame size
CLIPS = ['IMG_0536', 'IMG_0537', 'IMG_0538', 'IMG_0539']
WIN_S = 0.30

def load(name):
    d = np.genfromtxt(f'{TRACK_OUT}/{name}.csv', delimiter=',', names=True)
    h = medfilt(d['bottom_px'] - d['top_px'], 3)          # 3-tap median kills 1-frame tracker glitches
    return d, h

def window(name, base):
    """Return t (s, 0 at first overshoot peak), d (fractional deviation from tail rest height), rest_px.
    base: 'frame' (uniform 1/240 s) or 'pts' (file timestamps)."""
    d, h = load(name)
    rest = np.median(h[-len(h) // 5:])
    t_all = d['frame'] / 240 if base == 'frame' else d['pts_s']
    i_up = np.flatnonzero(h > 0.5 * (h.min() + rest))     # mid-rise crossing, last big rise
    # last crossing of the half-height level going up = release
    up = [i for i in range(1, len(h)) if h[i - 1] <= 0.5 * (h.min() + rest) < h[i]][-1]
    # first local max after rise reaches rest*0.97 (smoothed)
    hs = np.convolve(h, np.ones(3) / 3, 'same')
    j = up + np.flatnonzero(hs[up:] >= 0.95 * rest)[0]
    while hs[j + 1] >= hs[j]: j += 1                      # climb to the peak
    sel = (t_all >= t_all[j]) & (t_all <= t_all[j] + WIN_S)
    return t_all[sel] - t_all[j], h[sel] / rest - 1, rest, (up, j)

def model(p, t, d0):
    kp, cp, dt, off = p                                   # k', c', peak time shift, rest offset
    wn = np.sqrt(kp); z = cp / (2 * wn); wd = wn * np.sqrt(max(1 - z * z, 1e-9))
    tt = t - dt
    return off + (d0 - off) * np.exp(-z * wn * tt) * (np.cos(wd * tt) + z * wn / wd * np.sin(wd * tt))

def fit(t, d, starts=30):
    d0 = d[0]; best = None
    rng = np.random.default_rng(0)
    for _ in range(starts):
        wn = 2 * np.pi * np.exp(rng.uniform(np.log(5), np.log(40))); z = rng.uniform(0.02, 1.5)
        x0 = [np.log(wn ** 2), np.log(2 * z * wn), 0, 0]
        r = least_squares(lambda x: model([np.exp(x[0]), np.exp(x[1]), x[2], x[3]], t, d0) - d, x0,
                          bounds=([-np.inf, -np.inf, -2 / 240, -0.05], [np.inf, np.inf, 2 / 240, 0.05]))
        if best is None or r.cost < best.cost: best = r
    x = best.x
    return dict(kp=np.exp(x[0]), cp=np.exp(x[1]), dt=x[2], off=x[3], rmse=np.sqrt(2 * best.cost / len(t)))
