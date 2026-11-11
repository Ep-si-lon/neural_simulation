"""Fit the axisymmetric FEM ball (Warp) to the tracked silhouettes with a PyTorch optimiser.
Parameters (all fitted): Young's modulus E, Poisson ratio nu, Rayleigh damping alpha, friction on the plate and on the table.
Targets per clip: the outline (width at 48 levels from top to bottom, tracked in tracking/outputs/*_sil.npz) and the height, at
  - 3 points along the squeeze (plate at 25 / 50 / 75 % of its travel), the hold, and every 3rd frame of the 0.25 s after release.
Gradients come from Warp's tape (the whole run is differentiable); torch handles the parameter mapping, Adam and the schedule.
Run: models/continuum/fem_axisymmetric_warp/run.sh"""
import os, sys, json, time
import numpy as np, torch, warp as wp
from common import CLIPS, TRACK_OUT
from clip_prep import prep
from fem_axi import FEM, RHO, R

L0, L1 = 3, 45
PROTOCOL = os.environ.get('FEM_PROTOCOL', 'tin')   # 'tin': the plate follows the measured tin retreat; 'instant': plate removed at the separation frame (the older, flawed protocol, kept as an ablation)
TRAIN, TEST = CLIPS[:2], CLIPS[2:]

def safe_dt(cw, alpha):
    """Explicit time step: CFL fraction 0.18 of (1.5 mm / wave speed) (squeezed elements are smaller than the rest mesh), damping step limit, hard cap 1.5e-5 s."""
    return float(np.clip(min(0.18 * 0.0015 / cw, 0.08 / max(alpha, 600.0)), 4e-6, 1.5e-5))

def theta_to_params(th):
    """Unconstrained theta -> physical parameters (all inside sensible bounds)."""
    sg = torch.sigmoid(th)
    E = torch.exp(8.0 + 4.4 * sg[0]); nu = 0.02 + 0.43 * sg[1]
    alpha = 300.0 * (8000.0 / 300.0) ** sg[2]; mup = 0.05 + 1.95 * sg[3]; mut = 0.05 + 1.95 * sg[4]
    mu_l = E / (2 * (1 + nu)); lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    return torch.stack([mu_l, lam, alpha, mup, mut]), dict(E=E, nu=nu, alpha=alpha, mu_plate=mup, mu_table=mut)

def clip_data(name):
    c = prep(name); z = np.load(f'{TRACK_OUT}/{name}_sil.npz'); pxm = c['rest'] / 0.067
    return dict(name=name, c=c, z=z, pxm=pxm, h_hold=c['hc'] / pxm, tin=(c['tin'] if PROTOCOL == 'tin' else None))

def make_events(cd, plan, dev):
    c, z, pxm, dt = cd['c'], cd['z'], cd['pxm'], plan['dt']
    r, p, h_hold = c['i_rel'], c['i_plat'], cd['h_hold']; st, hm, lm, wm, wt = [], [], [], [], []   # r: separation frame, p: end of the pressed plateau
    wprof = lambda fr: (np.nanmedian(z['right'][fr] - z['left'][fr], 0) if np.ndim(fr) else (z['right'][fr] - z['left'][fr])) / pxm
    t0 = plan['n_sep'] * dt                                              # separation instant: the ball is free from here
    for k in range(0, len(c['t']), 3):                                    # release
        st.append(int(round((t0 + c['t'][k]) / dt))); hm.append(c['h'][k] / pxm); lm.append(0.0); wm.append(wprof(r + k)); wt.append((1.0, 1.0, 0.0))
    st.append(plan['n_sq'] + plan['n_hold'] - 1); hm.append(h_hold); lm.append(0.0)       # hold: outline of the pressed ball
    wm.append(wprof(np.arange(p - 30, p - 5))); wt.append((4.0, 0.0, 0.0))
    fh = c['full_h'] / pxm
    for f in (0.25, 0.5, 0.75):                                          # squeeze path: plate at a fraction of its travel
        lvl = plan['z0'] - f * (plan['z0'] - h_hold); idx = np.flatnonzero(fh[:p] > lvl)
        if len(idx) == 0: continue
        fr = min(idx[-1] + 1, p - 1); st.append(int(f * plan['n_sq'])); hm.append(lvl); lm.append(0.0); wm.append(wprof(fr)); wt.append((1.5, 0.3, 0.0))
    st = np.array(st, np.int32); st = np.minimum(st, plan['n'])
    return dict(step=st, w_step=wp.array(st, dtype=int, device=dev), w_h=wp.array(np.array(hm, np.float32), dtype=float, device=dev), w_l=wp.array(np.array(lm, np.float32), dtype=float, device=dev),
                w_w=wp.array(np.array(wm, np.float32), dtype=float, device=dev), w_wt=wp.array(np.array(wt, np.float32), dtype=wp.vec3, device=dev), l0=L0, l1=L1)

def loss_and_grad(fem, cds, p, dt_fixed=None):
    """p: torch tensor [mu, lam, alpha, mu_plate, mu_table]. Returns total loss (float) and dL/dp (numpy), summed over clips."""
    tot, g = 0.0, np.zeros(5)
    for cd in cds:
        mu, lam = float(p[0]), float(p[1]); cw = np.sqrt((lam + 2 * mu) / RHO)
        dt = dt_fixed or safe_dt(cw, float(p[2]))
        plan = fem.plan_with_dt(dt, cd['h_hold'], tin=cd['tin'])
        ev = make_events(cd, plan, fem.dev)
        x_all, loss, prm_w, tp = fem.run(p.detach().numpy().astype(np.float32), plan, ev, tape=True)
        tp.backward(loss=loss)
        tot += float(loss.numpy()[0]); g += prm_w.grad.numpy().astype(np.float64)
        tp.zero()
    return tot, g

def fit(fem, names, iters=45, lr=0.12, th0=None, log=print):
    cds = [clip_data(n) for n in names]
    th = torch.tensor(th0 if th0 is not None else [0.0, -0.3, 0.2, 0.0, 0.0], dtype=torch.float64, requires_grad=True)
    opt = torch.optim.Adam([th], lr=lr); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, iters)
    best = (1e9, None)
    for it in range(iters):
        opt.zero_grad(); p, info = theta_to_params(th)
        t = time.time(); l, g = loss_and_grad(fem, cds, p.to(torch.float32).detach().cpu())
        if not np.isfinite(l) or not np.all(np.isfinite(g)): log(f'  it {it}: non-finite, shrinking step'); th.data = th.data * 0.9; continue
        p.backward(torch.tensor(g, dtype=torch.float64)); torch.nn.utils.clip_grad_norm_([th], 5.0); opt.step(); sch.step()
        if l < best[0]: best = (l, th.detach().clone())
        log(f'  it {it:2d}  loss {l:.5f}  E {info["E"].item():8.0f} Pa  nu {info["nu"].item():.3f}  alpha {info["alpha"].item():6.0f}  mu_plate {info["mu_plate"].item():.2f}  mu_table {info["mu_table"].item():.2f}  ({time.time()-t:.1f}s)')
    return best

OUT = 'models/continuum/fem_axisymmetric_warp/outputs'

def simulate_clip(fem, name, p, use_tin=True):
    """Forward run (no tape) with fitted parameters p; returns plan and per-step arrays of the top/bottom axis nodes and the outline-relevant nodes."""
    cd = clip_data(name); mu, lam = float(p[0]), float(p[1]); cw = np.sqrt((lam + 2 * mu) / RHO)
    if not use_tin: cd['tin'] = None                                      # older protocol: instant removal at the separation frame
    dt = safe_dt(cw, float(p[2])); plan = fem.plan_with_dt(dt, cd['h_hold'], tin=cd['tin'])
    x_all, _, _, _ = fem.run(np.asarray(p, np.float32), plan, None, tape=False)
    return cd, plan, x_all.numpy()

def recovery_time(t, h, rest, thr=0.95):
    i = np.flatnonzero(h >= thr * rest); return float(t[i[0]]) * 1e3 if len(i) else float('nan')

def evaluate(fem, p, names, train, log=print):
    from clip_prep import baselines
    cs = {n: prep(n) for n in CLIPS}; rows = []
    for n in names:
        cd, plan, x = simulate_clip(fem, n, p); c = cd['c']; pxm = cd['pxm']; dt = plan['dt']; t0 = plan['n_sep'] * dt
        k = np.clip(np.round((t0 + c['t']) / dt).astype(int), 0, plan['n'])
        hs = (x[k, fem.top, 1] - x[k, fem.bot, 1]) * pxm                 # model height in px at the measured frame times
        h_rmse = 100 * np.sqrt(np.mean((hs - c['h']) ** 2)) / c['rest']
        he, hr = baselines(train, cs, c); e_rmse = 100 * np.sqrt(np.mean((he - c['h']) ** 2)) / c['rest']; r_rmse = 100 * np.sqrt(np.mean((hr - c['h']) ** 2)) / c['rest']
        t95_m = recovery_time(c['t'], hs, c['rest']); t95_r = recovery_time(c['t'], np.maximum.accumulate(c['h']), c['rest'])
        wd = []                                                           # outline error at the release frames (every 3rd), % of rest width
        for j in range(0, len(c['t']), 3):
            ev = dict(step=np.array([k[j]]))
            zt, zb = x[k[j], fem.top, 1], x[k[j], fem.bot, 1]; arc = x[k[j], fem.arc]
            for lv in range(L0, L1):
                zk = zt - (zt - zb) * lv / 47.0; rk = np.interp(zk, arc[:, 1], arc[:, 0]) if np.all(np.diff(arc[:, 1]) >= -1e-9) else np.nan
                if np.isfinite(rk): wd.append((2 * rk - (cd['z']['right'][c['i_rel'] + j, lv] - cd['z']['left'][c['i_rel'] + j, lv]) / pxm) / 0.067)
        o_rmse = 100 * np.sqrt(np.nanmean(np.square(wd)))
        rows.append(dict(clip=n, set='train' if n in train else 'TEST', height_rmse=h_rmse, exp_baseline=e_rmse, rest_baseline=r_rmse, outline_rmse=o_rmse, t95_model=t95_m, t95_real=t95_r,
                         pressed_width=float(x[plan['n_sq'] + plan['n_hold'] - 1, :, 0].max() * 2 / 0.067)))
        log(f"  {n} ({rows[-1]['set']}): height RMSE {h_rmse:.1f}% (exp baseline {e_rmse:.1f}%, rest {r_rmse:.1f}%)  outline RMSE {o_rmse:.1f}% of ball width  t95 model {t95_m:.0f} ms vs real {t95_r:.0f} ms  pressed width {rows[-1]['pressed_width']:.2f}x")
    return rows

if __name__ == '__main__':
    fem = FEM(); log_lines = []
    def log(s): print(s, flush=True); log_lines.append(s)
    log(f'axisymmetric FEM: {fem.N} nodes, {fem.E} triangles, rho {RHO} kg/m3 (estimate), ball radius {R} m')
    log(f'train {TRAIN} -> test {TEST}')
    loss, th = fit(fem, TRAIN, iters=int(sys.argv[1]) if len(sys.argv) > 1 else 45, log=log)
    p, info = theta_to_params(th); info = {k: float(v) for k, v in info.items()}
    log(f'best loss {loss:.5f}: ' + ', '.join(f'{k} = {v:.4g}' for k, v in info.items()))
    log('Young modulus E assumes density 55 kg/m3; the identified quantity is E / rho = %.0f m2/s2' % (info['E'] / RHO))
    rows = evaluate(fem, p.detach().numpy(), CLIPS, TRAIN, log)
    json.dump(dict(params=info, prm=[float(v) for v in p], rows=rows, rho=RHO), open(f'{OUT}/params_fem.json', 'w'), indent=1)
    open(f'{OUT}/results.txt', 'w').write('\n'.join(log_lines) + '\n')
