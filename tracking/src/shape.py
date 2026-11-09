"""Robust per-frame shape from the silhouette: width profile w(s) ~ W * (1 - |2s-1|^n)^(1/n), s = 0 (top) .. 1 (bottom).
W = max width (px), n = squareness (n=2 ellipse, large n = flat top/bottom with straight sides). soft-L1 fit ignores glare spikes.
Output tracking/outputs/<clip>_shape.csv: frame, pts_s, top_px, bottom_px, W_px, n, fit_rms_px. Usage: shape.py IMG_0536"""
import sys, csv
import numpy as np
from scipy.optimize import least_squares

from shape_curve import profile, fit_frame
from common import TRACK_OUT

def main(name):
    z = np.load(f'{TRACK_OUT}/{name}_sil.npz'); rows = []
    for i in range(len(z['top'])):
        w = z['right'][i] - z['left'][i]
        W, n, rms = fit_frame(w, None); rows.append([i, z['pts_s'][i], z['top'][i], z['bottom'][i], W, n, rms])
    with open(f'{TRACK_OUT}/{name}_shape.csv', 'w', newline='') as fh:
        wr = csv.writer(fh); wr.writerow(['frame', 'pts_s', 'top_px', 'bottom_px', 'W_px', 'n', 'fit_rms_px']); wr.writerows(rows)
    print(name, 'done')

if __name__ == '__main__': main(sys.argv[1])
