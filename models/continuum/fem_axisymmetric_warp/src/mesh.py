"""Triangle mesh of the axisymmetric slice of a ball: a half disc (r >= 0) of radius R centred at (0, R) in (r, z), resting on z = 0.
Revolving the slice around the z axis gives the whole sphere, so one 2D mesh of a few hundred nodes represents a smooth 3D ball."""
import numpy as np
from scipy.spatial import Delaunay

def half_disc_mesh(R=0.0335, h=0.0015):
    pts = []
    dz = h * np.sqrt(3) / 2
    for j in range(int(2 * R / dz) + 2):                       # hex lattice inside the half disc
        z = j * dz; r = 0.5 * h if j % 2 else 0.0
        while r <= R:
            if np.hypot(r, z - R) < R - 0.6 * h: pts.append((r, z))
            r += h
    n_arc = int(np.pi * R / h)
    phi = np.linspace(0, np.pi, n_arc + 1)                     # phi = 0 bottom pole ... pi top pole
    arc = np.stack([R * np.sin(phi), R - R * np.cos(phi)], 1)
    arc[0, 0] = 0.0; arc[-1, 0] = 0.0
    pts = np.array(pts); keep = ~((pts[:, 0] < 1e-9) & (np.abs(pts[:, 1] - R) > R - 0.6 * h))   # drop lattice axis nodes that crowd the poles
    pts = np.vstack([arc, pts[keep]]); arc_idx = np.arange(len(arc))
    tri = Delaunay(pts).simplices
    c = pts[tri].mean(1); tri = tri[np.hypot(c[:, 0], c[:, 1] - R) < R]
    d1 = pts[tri[:, 1]] - pts[tri[:, 0]]; d2 = pts[tri[:, 2]] - pts[tri[:, 0]]
    cross = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
    flip = cross < 0; tri[flip] = tri[flip][:, [0, 2, 1]]       # counter-clockwise
    area = 0.5 * np.abs(cross)
    ok = area > 1e-3 * h * h; tri = tri[ok]
    return pts.astype(np.float64), tri.astype(np.int32), arc_idx          # arc_idx: boundary nodes ordered bottom pole -> top pole

def describe(R=0.0335, h=0.0015):
    X, tri, arc = half_disc_mesh(R, h)
    d1 = X[tri[:, 1]] - X[tri[:, 0]]; d2 = X[tri[:, 2]] - X[tri[:, 0]]
    A = 0.5 * np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]); rc = X[tri][:, :, 0].mean(1)
    vol = (2 * np.pi * rc * A).sum()
    return dict(nodes=len(X), triangles=len(tri), volume_ratio=vol / (4 / 3 * np.pi * R ** 3), min_area_ratio=A.min() / np.median(A))

if __name__ == '__main__': print(describe())
