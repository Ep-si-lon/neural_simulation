"""Width-profile curve used for the ball outline: w(s) = W (1 - |2s-1|^n)^(1/n), s = 0 (top) .. 1 (bottom).
W = max width, n = squareness (2 = ellipse, large = flat top/bottom). Fitted with soft-L1 so tracking spikes are ignored."""
import numpy as np
from scipy.optimize import least_squares

def profile(s, W, n): return W * np.clip(1 - np.abs(2 * s - 1) ** n, 0, None) ** (1 / n)

def fit_frame(w, x0):
    s = np.linspace(0, 1, len(w)); k = slice(3, len(w) - 3)             # edge levels are unreliable
    best = None
    for n0 in (2.0, 5.0):
        r = least_squares(lambda p: profile(s[k], p[0], p[1]) - w[k], [np.nanmax(w) if x0 is None else x0, n0],
                          bounds=([100, 1.2], [900, 14]), loss='soft_l1', f_scale=10.0)
        if best is None or r.cost < best.cost: best = r
    return best.x[0], best.x[1], np.sqrt(np.mean((profile(s[k], *best.x) - w[k]) ** 2))

