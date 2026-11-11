"""3D MLS-MPM (material point method) simulation of the ball in NVIDIA Warp, APIC transfers, compressible neo-Hookean material.
Kirchhoff stress  tau = mu (F F^T - I) + lam ln(J) I ; Young's modulus E, Poisson ratio nu, density rho; Rayleigh damping rate alpha applied to the grid velocity.
Tools act on the grid: table (y = y_t), flat plate on top, two flat plates at the sides, or a spherical point probe; Coulomb friction limited by the normal velocity change.
Units: m, s, kg. y is up. Loads: 'flat', 'point', 'side'; each = squeeze ramp, hold, release (as in the axisymmetric FEM)."""
import numpy as np
import warp as wp

wp.config.quiet = True
RHO, R = 55.0, 0.0335
DX, NG = 0.0025, 64
L = DX * NG
YT = 0.01                               # table height in the domain
CX = CZ = L / 2
INV = 1.0 / DX

@wp.func
def wq(i: int, f: float):
    """Quadratic B-spline weight of stencil node i (0, 1, 2) for fractional position f."""
    if i == 0:
        return 0.5 * (1.5 - f) * (1.5 - f)
    if i == 1:
        return 0.75 - (f - 1.0) * (f - 1.0)
    return 0.5 * (f - 0.5) * (f - 0.5)

@wp.kernel
def k_clear(gv: wp.array3d(dtype=wp.vec3), gm: wp.array3d(dtype=float)):
    i, j, k = wp.tid()
    gv[i, j, k] = wp.vec3(0.0, 0.0, 0.0)
    gm[i, j, k] = 0.0

@wp.kernel
def k_p2g(x: wp.array(dtype=wp.vec3), v: wp.array(dtype=wp.vec3), C: wp.array(dtype=wp.mat33), F: wp.array(dtype=wp.mat33), mp: float, vol: float,
          mu: float, lam: float, dt: float, gv: wp.array3d(dtype=wp.vec3), gm: wp.array3d(dtype=float)):
    p = wp.tid()
    xp = x[p] * INV
    base = wp.vec3i(int(xp[0] - 0.5), int(xp[1] - 0.5), int(xp[2] - 0.5))
    fx = xp - wp.vec3(float(base[0]), float(base[1]), float(base[2]))
    Fp = F[p]
    J = wp.max(wp.determinant(Fp), 0.05)
    eye = wp.identity(n=3, dtype=float)
    tau = mu * (Fp * wp.transpose(Fp) - eye) + lam * wp.log(J) * eye
    affine = (-dt * vol * 4.0 * INV * INV) * tau + mp * C[p]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                w = wq(i, fx[0]) * wq(j, fx[1]) * wq(k, fx[2])
                dpos = (wp.vec3(float(i), float(j), float(k)) - fx) * DX
                wp.atomic_add(gv, base[0] + i, base[1] + j, base[2] + k, w * (mp * v[p] + affine * dpos))
                wp.atomic_add(gm, base[0] + i, base[1] + j, base[2] + k, w * mp)

@wp.func
def contact(v: wp.vec3, n: wp.vec3, vt_tool: wp.vec3, fric: float):
    """Remove the velocity component into a tool surface (outward normal n of the tool, tool velocity vt_tool), with Coulomb friction."""
    vr = v - vt_tool
    vn = wp.dot(vr, n)
    if vn < 0.0:
        vtan = vr - vn * n
        sp = wp.length(vtan)
        if sp > 1.0e-9:
            vtan = vtan * wp.max(1.0 - fric * (-vn) / sp, 0.0)
        return vt_tool + vtan
    return v

@wp.kernel
def k_grid(gv: wp.array3d(dtype=wp.vec3), gm: wp.array3d(dtype=float), dt: float, damp: float, mu_plate: float, mu_table: float,
           kind: int, plate_y: float, plate_v: float, side_gap: float, side_v: float, probe_c: wp.vec3, probe_r: float, probe_v: wp.vec3):
    i, j, k = wp.tid()
    m = gm[i, j, k]
    if m > 1.0e-12:
        v = gv[i, j, k] / m + wp.vec3(0.0, -9.81, 0.0) * dt
        v = v * (1.0 - damp * dt)
        pos = wp.vec3(float(i), float(j), float(k)) * DX
        if pos[1] < YT:
            v = contact(v, wp.vec3(0.0, 1.0, 0.0), wp.vec3(0.0, 0.0, 0.0), mu_table)
        if kind == 0 and pos[1] > plate_y:
            v = contact(v, wp.vec3(0.0, -1.0, 0.0), wp.vec3(0.0, plate_v, 0.0), mu_plate)
        if kind == 2:
            if pos[0] > CX + 0.5 * side_gap:
                v = contact(v, wp.vec3(-1.0, 0.0, 0.0), wp.vec3(-side_v, 0.0, 0.0), mu_plate)
            if pos[0] < CX - 0.5 * side_gap:
                v = contact(v, wp.vec3(1.0, 0.0, 0.0), wp.vec3(side_v, 0.0, 0.0), mu_plate)
        if kind == 1:
            d = pos - probe_c
            dist = wp.length(d)
            if dist < probe_r and dist > 1.0e-9:
                v = contact(v, d / dist, probe_v, mu_plate)
        if i < 3 and v[0] < 0.0:
            v = wp.vec3(0.0, v[1], v[2])
        if i > NG - 3 and v[0] > 0.0:
            v = wp.vec3(0.0, v[1], v[2])
        if k < 3 and v[2] < 0.0:
            v = wp.vec3(v[0], v[1], 0.0)
        if k > NG - 3 and v[2] > 0.0:
            v = wp.vec3(v[0], v[1], 0.0)
        if j > NG - 3 and v[1] > 0.0:
            v = wp.vec3(v[0], 0.0, v[2])
        gv[i, j, k] = v

@wp.kernel
def k_g2p(x: wp.array(dtype=wp.vec3), v: wp.array(dtype=wp.vec3), C: wp.array(dtype=wp.mat33), F: wp.array(dtype=wp.mat33), gv: wp.array3d(dtype=wp.vec3), dt: float):
    p = wp.tid()
    xp = x[p] * INV
    base = wp.vec3i(int(xp[0] - 0.5), int(xp[1] - 0.5), int(xp[2] - 0.5))
    fx = xp - wp.vec3(float(base[0]), float(base[1]), float(base[2]))
    nv = wp.vec3(0.0, 0.0, 0.0)
    nC = wp.mat33(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                w = wq(i, fx[0]) * wq(j, fx[1]) * wq(k, fx[2])
                gvel = gv[base[0] + i, base[1] + j, base[2] + k]
                dpos = (wp.vec3(float(i), float(j), float(k)) - fx) * DX
                nv = nv + w * gvel
                nC = nC + (4.0 * INV * INV * w) * wp.outer(gvel, dpos)
    v[p] = nv
    C[p] = nC
    x[p] = x[p] + dt * nv
    F[p] = (wp.identity(n=3, dtype=float) + dt * nC) * F[p]

def sample_ball(ppc=2):
    s = DX / ppc; r0 = (np.arange(int(2 * R / s) + 2) + 0.5) * s - R
    g = np.stack(np.meshgrid(r0, r0, r0, indexing='ij'), -1).reshape(-1, 3)
    g = g[np.linalg.norm(g, axis=1) < R - 0.1 * s]
    g = g + np.random.default_rng(0).uniform(-0.2 * s, 0.2 * s, g.shape)          # small fixed jitter: no regular lattice (avoids grid-aligned artefacts)
    return g + np.array([CX, YT + R + 0.0004, CZ]), (s ** 3)

def lame(E, nu): return E / (2 * (1 + nu)), E * nu / ((1 + nu) * (1 - 2 * nu))

def simulate(E, nu, alpha, mu_plate, mu_table, load='flat', depth=None, t_sq=0.12, t_hold=0.04, t_rel=0.25, rec_dt=1 / 240, ppc=2, device=None):
    """Run one load. depth: flat -> plate height above the table; point -> probe-tip height above the table; side -> final gap between the plates (m).
    Returns dict(t (s from release), height, width, snaps (particle positions at each record time), tool (load, position, probe radius))."""
    dev = device or wp.get_preferred_device(); mu, lam = lame(E, nu); c = np.sqrt((lam + 2 * mu) / RHO)
    dt = float(np.clip(min(0.25 * DX / c, 0.08 / max(alpha, 600.0)), 4e-6, 2e-5))
    pos0, vol = sample_ball(ppc); n = len(pos0); mp = RHO * vol
    x = wp.array(pos0.astype(np.float32), dtype=wp.vec3, device=dev); v = wp.zeros(n, dtype=wp.vec3, device=dev)
    C = wp.zeros(n, dtype=wp.mat33, device=dev); F = wp.array(np.tile(np.eye(3, dtype=np.float32), (n, 1, 1)), dtype=wp.mat33, device=dev)
    gv = wp.zeros((NG, NG, NG), dtype=wp.vec3, device=dev); gm = wp.zeros((NG, NG, NG), dtype=float, device=dev)
    top0 = YT + 2 * R + 0.0004
    n_sq, n_hold, n_rel = int(t_sq / dt), int(t_hold / dt), int(t_rel / dt); total = n_sq + n_hold + n_rel
    rec_every = max(int(round(rec_dt / dt)), 1); kind = {'flat': 0, 'point': 1, 'side': 2}[load]
    pr = 0.006 if load == 'point' else 0.0
    out = dict(t=[], height=[], width=[], snaps=[], tool=[], dt=dt, n_particles=n, t_release=(n_sq + n_hold) * dt)
    for s in range(total + 1):
        active = s < n_sq + n_hold; f = min(s / n_sq, 1.0) if active else 1.0; ramp = s < n_sq
        plate_y, plate_v, side_gap, side_v = 1e3, 0.0, 1e3, 0.0; probe_c = wp.vec3(0.0, 1e3, 0.0); probe_v = wp.vec3(0.0, 0.0, 0.0); tool_pos = 1e3
        if active:
            if load == 'flat':
                span = top0 - (YT + depth); plate_y = top0 - span * f; plate_v = -span / t_sq if ramp else 0.0; tool_pos = plate_y - YT
            if load == 'point':
                span = top0 - (YT + depth); tip = top0 - span * f; probe_c = wp.vec3(CX, tip + pr, CZ); probe_v = wp.vec3(0.0, -span / t_sq if ramp else 0.0, 0.0); tool_pos = tip - YT
            if load == 'side':
                span = 2 * R + 0.001 - depth; side_gap = 2 * R + 0.001 - span * f; side_v = (span / 2) / t_sq if ramp else 0.0; tool_pos = side_gap
        if s % rec_every == 0:
            xs = x.numpy(); out['t'].append(s * dt - (n_sq + n_hold) * dt); out['height'].append(float(xs[:, 1].max() - xs[:, 1].min()) + DX / ppc); out['width'].append(float(np.ptp(xs[:, 0])) + DX / ppc)
            out['snaps'].append(xs.astype(np.float32).copy()); out['tool'].append((load, tool_pos, pr, YT))
        if s == total: break
        wp.launch(k_clear, dim=(NG, NG, NG), inputs=[gv, gm], device=dev)
        wp.launch(k_p2g, dim=n, inputs=[x, v, C, F, mp, vol, mu, lam, dt, gv, gm], device=dev)
        gam = 600.0 if active else alpha
        wp.launch(k_grid, dim=(NG, NG, NG), inputs=[gv, gm, dt, gam, mu_plate, mu_table, kind, plate_y, plate_v, side_gap, side_v, probe_c, pr, probe_v], device=dev)
        wp.launch(k_g2p, dim=n, inputs=[x, v, C, F, gv, dt], device=dev)
    return out
