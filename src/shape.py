"""Robust per-frame shape from the silhouette: width profile w(s) ~ W * (1 - |2s-1|^n)^(1/n), s = 0 (top) .. 1 (bottom).
W = max width (px), n = squareness (n=2 ellipse, large n = flat top/bottom with straight sides). soft-L1 fit ignores glare spikes.
Output data/<clip>_shape.csv: frame, pts_s, top_px, bottom_px, W_px, n, fit_rms_px. Usage: shape.py IMG_0536"""
import sys, csv
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

def main(name):
    z = np.load(f'data/{name}_sil.npz'); rows = []
    for i in range(len(z['top'])):
        w = z['right'][i] - z['left'][i]
        W, n, rms = fit_frame(w, None); rows.append([i, z['pts_s'][i], z['top'][i], z['bottom'][i], W, n, rms])
    with open(f'data/{name}_shape.csv', 'w', newline='') as fh:
        wr = csv.writer(fh); wr.writerow(['frame', 'pts_s', 'top_px', 'bottom_px', 'W_px', 'n', 'fit_rms_px']); wr.writerows(rows)
    print(name, 'done')

if __name__ == '__main__': main(sys.argv[1])
