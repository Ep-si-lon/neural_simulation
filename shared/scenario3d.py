"""Shared 3D scenario runner: relax -> quasi-static plate press to the clip's measured compressed height -> release -> simulate 0.25 s,
reporting height, lift, width W and squareness n (the mesh silhouette is analysed with the same curve fit as the video)."""
import numpy as np
from clip_prep import HORIZON
from shape_curve import fit_frame
from ball3d import Ball, DT, SUB
from common import TRACK_OUT

REC = 2e-3

def mesh_features(b, rest_h):
    x = b.x; ymin, ymax = x[:, 1].min(), x[:, 1].max(); ys = np.linspace(ymax - 1e-4, ymin + 1e-4, 48)
    i, j = b.e[:, 0], b.e[:, 1]; yi, yj = x[i, 1][None], x[j, 1][None]; Y = ys[:, None]
    cross = (yi - Y) * (yj - Y) <= 0; t = np.where(cross, (Y - yi) / (yj - yi + 1e-12), 0)
    xc = x[i, 0][None] + t * (x[j, 0] - x[i, 0])[None]
    w = np.where(cross, xc, np.nan); wd = np.nanmax(w, 1) - np.nanmin(w, 1)
    W, n, _ = fit_frame(wd * 6000.0, None)               # px-like units (6000 px/m); only ratios are used
    return ymax - ymin, ymin, W, n

def scenario(p, c):
    ks, kb, kr, cd = np.exp(p); b = Ball(sub=SUB, ks=ks, kb=kb, kr=kr, cd=cd); b.run(0.08, DT, damp=80)
    rest_h = b.shape()[0]; _, _, Wrest, _ = mesh_features(b, rest_h); target = rest_h * c['hc'] / c['rest']
    for i in range(40): b.tool = ('plate', rest_h - (rest_h - target) * (i + 1) / 40, 0); b.run(0.0015, DT, damp=80)
    if c.get('tin') is not None:                                          # tin retreat: the plate follows the measured trajectory, then the ball is free
        Tr = c['tin'][0][-1]; nr = max(int(round(Tr / 0.0015)), 1)
        for i in range(nr): b.tool = ('plate', float(np.interp((i + 1) * Tr / nr, c['tin'][0], c['tin'][1])) * rest_h / 0.067, 0); b.run(Tr / nr, DT)
    b.tool = None; T, F = [], []
    for k in range(int(HORIZON / REC) + 1):
        if k: b.run(REC, DT)
        h, lo, W, n = mesh_features(b, rest_h); T.append(k * REC); F.append([h / rest_h, max(lo, 0) / rest_h, W / Wrest, n])
    return np.array(T), np.array(F)

def measured(name, c):
    d = np.genfromtxt(f'{TRACK_OUT}/{name}_shape.csv', delimiter=',', names=True)
    Wr = np.median(d['W_px'][-len(d) // 5:]); pts = d['pts_s']; r = c['i_rel']; s = (pts >= pts[r]) & (pts <= pts[r] + HORIZON)
    return pts[s] - pts[r], np.stack([d['W_px'][s] / Wr, d['n'][s]], 1)

