"""Axisymmetric finite-element simulation of the ball in NVIDIA Warp (differentiable).
The unknowns are (r, z) of the nodes of the half-disc mesh; the hoop direction is handled analytically (hoop stretch = r / R).
Material: compressible neo-Hookean, Cauchy stress  sigma = mu/J (B - I) + lam ln(J)/J I,  (mu, lam) from Young's modulus E and Poisson ratio nu.
Damping: mass-proportional (Rayleigh) rate alpha on the absolute velocity. This gives the overdamped recovery of the real ball and suppresses the hop (the hop is not modelled; physical Kelvin-Voigt viscosity would need ~1e-7 s steps with this mesh).
Contact: flat plate (moving in z) and table as exact kinematic constraints (positions projected), with Coulomb friction limited by the estimated normal reaction. All per-step arrays are separate, so Warp's Tape can differentiate the whole run.
"""
import numpy as np
import warp as wp
from mesh import half_disc_mesh

wp.config.quiet = True
wp.set_module_options({'max_unroll': 128})   # unrolled loops (compile-time trip count) keep the outline loss differentiable
RHO, R, G = 55.0, 0.0335, 9.81          # density (kg/m^3, estimate), ball radius (m), gravity
NL = 48                                  # outline levels (as in the tracked silhouettes)
L0, L1 = 3, 45                           # levels used in the loss (the end levels are unreliable)
NARC = len(half_disc_mesh(R, 0.0015)[2])  # boundary nodes along the profile (compile-time constant)

@wp.kernel
def k_elem(n: int, x_all: wp.array2d(dtype=wp.vec2), tri: wp.array(dtype=wp.vec3i), dminv: wp.array(dtype=wp.mat22), rc0: wp.array(dtype=float),
           prm: wp.array(dtype=float), f_all: wp.array2d(dtype=wp.vec2)):
    e = wp.tid()
    t = tri[e]
    a = t[0]; b = t[1]; c = t[2]
    x0 = x_all[n, a]; x1 = x_all[n, b]; x2 = x_all[n, c]
    d1 = x1 - x0; d2 = x2 - x0
    ds = wp.mat22(d1[0], d2[0], d1[1], d2[1])
    F = ds * dminv[e]
    rc = wp.max((x0[0] + x1[0] + x2[0]) / 3.0, 1.0e-6)
    lt = rc / rc0[e]                                   # hoop stretch
    J = wp.max(wp.determinant(F) * lt, 0.05)           # volume ratio (clamped against inversion)
    lnj = wp.log(J)
    mu = prm[0]; lam = prm[1]
    eye = wp.identity(n=2, dtype=float)
    s_el = (mu / J) * (F * wp.transpose(F) - eye) + (lam * lnj / J) * eye
    s_th = (mu / J) * (lt * lt - 1.0) + lam * lnj / J
    di = wp.inverse(ds)
    g1 = wp.vec2(di[0, 0], di[0, 1]); g2 = wp.vec2(di[1, 0], di[1, 1]); g0 = -(g1 + g2)
    area = wp.max(0.5 * wp.determinant(ds), 1.0e-12)
    vol = 6.2831853 * rc * area
    hoop = wp.vec2(s_th / (3.0 * rc), 0.0)
    wp.atomic_add(f_all, n, a, -vol * (s_el * g0 + hoop))
    wp.atomic_add(f_all, n, b, -vol * (s_el * g1 + hoop))
    wp.atomic_add(f_all, n, c, -vol * (s_el * g2 + hoop))

@wp.kernel
def k_node(n: int, dt: float, x_all: wp.array2d(dtype=wp.vec2), v_all: wp.array2d(dtype=wp.vec2), f_all: wp.array2d(dtype=wp.vec2),
           mass: wp.array(dtype=float), axis: wp.array(dtype=int), prm: wp.array(dtype=float),
           plate_z: wp.array(dtype=float), plate_v: wp.array(dtype=float), mode: wp.array(dtype=int), gam: float):
    i = wp.tid()
    x = x_all[n, i]; v = v_all[n, i]
    a = f_all[n, i] / mass[i] + wp.vec2(0.0, -9.81)
    d = prm[2]
    if mode[n] == 0:
        d = gam                                        # numerical drag while squeezing (quasi-static)
    a = a - d * v
    vn = v + dt * a
    xn = x + dt * vn
    if xn[1] < 0.0:                                    # table: exact kinematic contact, Coulomb friction limited by the estimated reaction
        an = wp.max(-a[1], 0.0)
        lim = prm[4] * an * dt
        vn = wp.vec2(vn[0] - wp.clamp(vn[0], -lim, lim), wp.max(vn[1], 0.0))
        xn = wp.vec2(xn[0], 0.0)
    pz = plate_z[n]
    if xn[1] > pz:                                     # flat plate (moving in z): same treatment
        an = wp.max(a[1], 0.0)
        lim = prm[3] * an * dt
        vn = wp.vec2(vn[0] - wp.clamp(vn[0], -lim, lim), wp.min(vn[1], plate_v[n]))
        xn = wp.vec2(xn[0], pz)
    if axis[i] == 1:
        vn = wp.vec2(0.0, vn[1])
        xn = wp.vec2(0.0, xn[1])
    v_all[n + 1, i] = vn
    x_all[n + 1, i] = xn

@wp.func
def huber(x: float, d: float):
    ax = wp.abs(x)
    if ax < d:
        return 0.5 * x * x
    return d * (ax - 0.5 * d)

@wp.kernel
def k_outline(x_all: wp.array2d(dtype=wp.vec2), arc: wp.array(dtype=int), top: int, bot: int, ev_step: wp.array(dtype=int), wsim: wp.array2d(dtype=float)):
    e, kk = wp.tid()
    n = ev_step[e]
    zt = x_all[n, top][1]; zb = x_all[n, bot][1]
    zk = zt - (zt - zb) * float(kk + 3) / 47.0
    rk = float(0.0)
    for j in range(NARC - 1):                          # static trip count -> unrolled -> differentiable
        pa = x_all[n, arc[j]]; pb = x_all[n, arc[j + 1]]
        den = pb[1] - pa[1]
        t = (zk - pa[1]) / wp.where(wp.abs(den) > 1.0e-9, den, 1.0)
        inside = (t >= 0.0) and (t < 1.0) and (wp.abs(den) > 1.0e-9)
        rk += wp.where(inside, pa[0] + (pb[0] - pa[0]) * t, 0.0)
    wsim[e, kk] = 2.0 * rk

@wp.kernel
def k_loss_w(wsim: wp.array2d(dtype=float), ev_w: wp.array2d(dtype=float), ev_wt: wp.array(dtype=wp.vec3), loss: wp.array(dtype=float)):
    e, kk = wp.tid()
    wp.atomic_add(loss, 0, ev_wt[e][0] * huber((wsim[e, kk] - ev_w[e, kk + 3]) / 0.067, 0.03) / 42.0)

@wp.kernel
def k_loss_h(x_all: wp.array2d(dtype=wp.vec2), top: int, bot: int, ev_step: wp.array(dtype=int), ev_h: wp.array(dtype=float), ev_l: wp.array(dtype=float),
             ev_wt: wp.array(dtype=wp.vec3), loss: wp.array(dtype=float)):
    e = wp.tid()
    n = ev_step[e]
    zt = x_all[n, top][1]; zb = x_all[n, bot][1]
    wp.atomic_add(loss, 0, ev_wt[e][1] * huber((zt - zb - ev_h[e]) / 0.067, 0.02) + ev_wt[e][2] * huber((wp.max(zb, 0.0) - ev_l[e]) / 0.067, 0.02))

class FEM:
    def __init__(self, device=None, h=0.0015):
        X, tri, arc = half_disc_mesh(R, h)
        self.X, self.tri, self.arc = X, tri, arc
        self.N, self.E = len(X), len(tri)
        d1 = X[tri[:, 1]] - X[tri[:, 0]]; d2 = X[tri[:, 2]] - X[tri[:, 0]]
        Dm = np.stack([np.stack([d1[:, 0], d2[:, 0]], 1), np.stack([d1[:, 1], d2[:, 1]], 1)], 1)       # (E,2,2) columns d1, d2
        self.dminv = np.linalg.inv(Dm); A0 = 0.5 * np.abs(np.linalg.det(Dm)); self.rc0 = X[tri][:, :, 0].mean(1)
        m = np.zeros(self.N)
        for k in range(3): np.add.at(m, tri[:, k], RHO * 2 * np.pi * self.rc0 * A0 / 3)
        self.mass = m; self.axis = (X[:, 0] < 1e-9).astype(np.int32)
        self.top = int(np.argmax(np.where(self.axis == 1, X[:, 1], -1))); self.bot = int(np.argmin(np.where(self.axis == 1, X[:, 1], 9)))
        self.dev = device or wp.get_preferred_device()
        d = self.dev
        self.w_tri = wp.array(tri, dtype=wp.vec3i, device=d); self.w_dminv = wp.array(self.dminv.astype(np.float32), dtype=wp.mat22, device=d)
        self.w_rc0 = wp.array(self.rc0.astype(np.float32), dtype=float, device=d); self.w_mass = wp.array(m.astype(np.float32), dtype=float, device=d)
        self.w_axis = wp.array(self.axis, dtype=int, device=d); self.w_arc = wp.array(arc.astype(np.int32), dtype=int, device=d)

    @staticmethod
    def lame(E, nu): return E / (2 * (1 + nu)), E * nu / ((1 + nu) * (1 - 2 * nu))

    def plan_with_dt(self, dt, h_hold, t_sq=0.12, t_hold=0.04, t_rel=0.25, gam=600.0, tin=None):
        """Per-step plate / damping-mode arrays: squeeze ramp, hold, then the tin's retreat (tin = (time since plateau end, top-edge height in m) measured from the video; the plate
        follows it until the ball separates), then the plate is removed and the free recovery is simulated for t_rel. tin=None reproduces the older protocol (instant removal)."""
        n_sq, n_hold, n_rel = int(t_sq / dt), int(t_hold / dt), int(t_rel / dt)
        n_ret = 0 if tin is None else int(round(tin[0][-1] / dt)); n = n_sq + n_hold + n_ret + n_rel
        z0 = 2 * R + 1e-4; plate = np.full(n + 1, 1e6); pv = np.zeros(n + 1); mode = np.zeros(n + 1, np.int32)
        k = np.arange(n_sq); plate[:n_sq] = z0 - (z0 - h_hold) * k / n_sq; pv[:n_sq] = -(z0 - h_hold) / t_sq
        plate[n_sq:n_sq + n_hold] = h_hold
        if n_ret:
            tr = np.arange(n_ret) * dt; zr = np.interp(tr, tin[0], tin[1]); plate[n_sq + n_hold:n_sq + n_hold + n_ret] = zr; pv[n_sq + n_hold:n_sq + n_hold + n_ret] = np.gradient(zr, dt)
        mode[n_sq + n_hold:] = 1
        return dict(dt=dt, n=n, n_sq=n_sq, n_hold=n_hold, n_ret=n_ret, n_sep=n_sq + n_hold + n_ret, n_rel=n_rel, plate=plate, pv=pv, mode=mode, z0=z0, h_hold=h_hold, gam=gam, t_sq=t_sq, t_hold=t_hold)

    def run(self, prm, plan, events=None, tape=False):
        """prm = [mu, lam, alpha, mu_plate, mu_table] (numpy or warp array). Returns (x_all warp array, loss array, prm array, tape)."""
        d, n, N = self.dev, plan['n'], self.N
        x_np = np.zeros((n + 1, N, 2), np.float32); x_np[0] = self.X
        x_all = wp.array(x_np, dtype=wp.vec2, device=d, requires_grad=tape)
        v_all = wp.zeros((n + 1, N), dtype=wp.vec2, device=d, requires_grad=tape); f_all = wp.zeros((n + 1, N), dtype=wp.vec2, device=d, requires_grad=tape)
        prm_w = prm if isinstance(prm, wp.array) else wp.array(np.asarray(prm, np.float32), dtype=float, device=d, requires_grad=tape)
        plate = wp.array(plan['plate'].astype(np.float32), dtype=float, device=d); pv = wp.array(plan['pv'].astype(np.float32), dtype=float, device=d)
        mode = wp.array(plan['mode'], dtype=int, device=d); dt = plan['dt']
        loss = wp.zeros(1, dtype=float, device=d, requires_grad=tape)
        tp = wp.Tape() if tape else None
        def steps():
            for s in range(n):
                wp.launch(k_elem, dim=self.E, inputs=[s, x_all, self.w_tri, self.w_dminv, self.w_rc0, prm_w, f_all], device=d)
                wp.launch(k_node, dim=N, inputs=[s, dt, x_all, v_all, f_all, self.w_mass, self.w_axis, prm_w, plate, pv, mode, plan['gam']], device=d)
            if events is not None:
                ne = len(events['step']); wsim = wp.zeros((ne, L1 - L0), dtype=float, device=d, requires_grad=tape)
                wp.launch(k_outline, dim=(ne, L1 - L0), inputs=[x_all, self.w_arc, self.top, self.bot, events['w_step'], wsim], device=d)
                wp.launch(k_loss_w, dim=(ne, L1 - L0), inputs=[wsim, events['w_w'], events['w_wt'], loss], device=d)
                wp.launch(k_loss_h, dim=ne, inputs=[x_all, self.top, self.bot, events['w_step'], events['w_h'], events['w_l'], events['w_wt'], loss], device=d)
        if tape:
            with tp: steps()
        else: steps()
        return x_all, loss, prm_w, tp
