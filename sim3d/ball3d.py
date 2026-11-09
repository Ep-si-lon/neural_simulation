"""Air-filled 3D shell ball: icosphere mesh, edge springs (stretch) + cross springs (bending) + internal gas pressure p = p0*V0/V,
gravity, table plane, and a pressing tool (flat plate or point probe). Semi-implicit Euler, numpy + scipy.sparse.
Mass-normalised: total mass = 1, so ks, kb, p0, cd are per unit mass (no ball mass was measured). Orthographic side camera (x right, y up)."""
import numpy as np
import scipy.sparse as sp

def icosphere(sub):
    t = (1 + 5 ** .5) / 2
    v = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    v = [np.array(x, float) / np.linalg.norm(x) for x in v]
    for _ in range(sub):
        cache, nf = {}, []
        def mid(a, b):
            k = (min(a, b), max(a, b))
            if k not in cache:
                m = v[a] + v[b]; v.append(m / np.linalg.norm(m)); cache[k] = len(v) - 1
            return cache[k]
        for a, b, c in f:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a); nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        f = nf
    return np.array(v), np.array(f)

class Ball:
    def __init__(self, R=0.0335, sub=2, ks=3e5, kb=1e5, p0=2e5, cd=30.0, g=9.81, kt=1e7):
        self.R, self.g, self.ks, self.kb, self.p0, self.cd, self.kt = R, g, ks, kb, p0, cd, kt
        v, f = icosphere(sub); self.x = v * R; self.f = f; self.N = len(v); self.m = 1.0 / self.N
        e = {tuple(sorted(p)) for t in f for p in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0]))}
        self.e = np.array(sorted(e)); opp = {}
        for t in f:
            for i in range(3):
                a, b, c = t[i], t[(i + 1) % 3], t[(i + 2) % 3]; opp.setdefault((min(a, b), max(a, b)), []).append(c)
        self.b = np.array([o for o in opp.values() if len(o) == 2])          # bending: spring between opposite vertices of adjacent triangles
        self.l0 = np.linalg.norm(self.x[self.e[:, 0]] - self.x[self.e[:, 1]], axis=1)
        self.lb0 = np.linalg.norm(self.x[self.b[:, 0]] - self.x[self.b[:, 1]], axis=1)
        E, B = len(self.e), len(self.b)
        self.Se = sp.csr_matrix((np.r_[np.ones(E), -np.ones(E)], (np.r_[self.e[:, 0], self.e[:, 1]], np.r_[np.arange(E), np.arange(E)])), shape=(self.N, E))
        self.Sb = sp.csr_matrix((np.r_[np.ones(B), -np.ones(B)], (np.r_[self.b[:, 0], self.b[:, 1]], np.r_[np.arange(B), np.arange(B)])), shape=(self.N, B))
        T = len(f); self.St = sp.csr_matrix((np.ones(3 * T) / 3, (f.ravel(), np.repeat(np.arange(T), 3))), shape=(self.N, T))
        self.v = np.zeros_like(self.x); self.V0 = self.volume(); self.x[:, 1] += R   # sits on y=0 table
        self.tool = None

    def volume(self):
        a, b, c = (self.x[self.f[:, i]] for i in range(3)); return np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6

    def forces(self):
        x, v = self.x, self.v
        d = x[self.e[:, 0]] - x[self.e[:, 1]]; l = np.linalg.norm(d, axis=1) + 1e-12; u = d / l[:, None]
        rv = np.einsum('ij,ij->i', v[self.e[:, 0]] - v[self.e[:, 1]], u)
        fe = (-self.ks * (l - self.l0) - self.cd * rv)[:, None] * u
        db = x[self.b[:, 0]] - x[self.b[:, 1]]; lb = np.linalg.norm(db, axis=1) + 1e-12
        fb = (-self.kb * (lb - self.lb0) / lb)[:, None] * db
        a, b_, c = (x[self.f[:, i]] for i in range(3)); nA = np.cross(b_ - a, c - a) / 2          # outward area-weighted normals
        p = self.p0 * self.V0 / max(self.volume(), 1e-9 * self.V0)
        F = self.Se @ fe + self.Sb @ fb + self.St @ (p * nA)
        F[:, 1] -= self.g * self.m
        F[:, 1] += np.where(x[:, 1] < 0, -self.kt * x[:, 1] * self.m - 2 * 0.3 * np.sqrt(self.kt) * v[:, 1] * self.m, 0)   # table penalty
        F[:, [0, 2]] -= np.where(x[:, 1] < 0, 5.0, 0)[:, None] * v[:, [0, 2]] * self.m                                 # table friction
        if self.tool is not None: F += self.tool_force()
        return F

    def tool_force(self):
        kind, y, r = self.tool; x, v = self.x, self.v
        if kind == 'plate':
            pen = np.clip(x[:, 1] - y, 0, None); on = pen > 0
            fy = np.where(on, -self.kt * pen - 2 * .3 * np.sqrt(self.kt) * np.minimum(v[:, 1], 0), 0) * self.m
            return np.stack([np.zeros(self.N), fy, np.zeros(self.N)], 1)
        c = np.array([self.cx, y + r, self.cz]); d = x - c; dist = np.linalg.norm(d, axis=1) + 1e-12; pen = np.clip(r - dist, 0, None)
        return ((self.kt * pen)[:, None] * d / dist[:, None]) * self.m

    def step(self, dt):
        F = self.forces(); self.v += dt * F / self.m; self.v *= 1 - 0.0 * dt; self.x += dt * self.v

    def run(self, T, dt=2e-5, damp=0.0):
        for _ in range(int(T / dt)):
            self.v *= (1 - damp * dt); self.step(dt)

    def shape(self):
        y = self.x[:, 1]; return y.max() - y.min(), np.ptp(self.x[:, 0]), y.min(), y.max()   # height, width, bottom, top
