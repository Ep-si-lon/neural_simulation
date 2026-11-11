"""Forward-run the continuum models (axisymmetric FEM; 3D MPM with the FEM's damping and with the damping calibrated on the training clips) on all four clips, and collect the
SAM 2 ground truth and the baselines. Runs with TRACKER=sam2 in .venv-sim. Output: outputs/curves_continuum.pkl (same layout as curves_earlier.pkl, plus 'truth')."""
import sys, json, time, pickle
import numpy as np
from common import CLIPS, TRACK_OUT
from clip_prep import prep, baselines
from shape_curve import fit_frame
import warp as wp
sys.path[:0] = ['models/continuum/fem_axisymmetric_warp/src', 'models/continuum/mpm_3d_warp/src']
from fem_axi import FEM, R
from fit_fem import simulate_clip
import mpm3d as M

MM, TRAIN = 67.0, CLIPS[:2]
cs = {n: prep(n) for n in CLIPS}; rel = {n: float(cs[n]['full_t'][cs[n]['i_rel']]) for n in CLIPS}
res = {'truth': {}, 'exp_baseline': {}, 'stay_at_rest': {}}   # time zero = separation frame (the tin has let go of the ball)
for n in CLIPS:
    c = cs[n]; sh = np.genfromtxt(f"{TRACK_OUT}/{n}_shape.csv", delimiter=',', names=True); wm = c['width']; r = c['i_rel']; p = c['i_plat']
    res['truth'][n] = dict(t=c['t'], h=c['h'] / c['rest'], lift_mm=c['lift'] / c['rest'] * MM, tin_T=float(c['tin'][0][-1]), pressed_width=float(np.median(wm[p - 30:p - 5]) / np.median(wm[-len(wm) // 5:])), pressed_width_curve=float(np.median(sh['W_px'][p - 30:p - 5]) / np.median(sh['W_px'][-len(sh) // 5:])), n_hold=float(np.median(sh['n'][p - 30:p - 5])), rel=rel[n], rest_px=c['rest'])
    he, hr = baselines(TRAIN, cs, c); res['exp_baseline'][n] = dict(t=c['t'], h=he / c['rest'], lift_mm=np.zeros_like(c['t']), pressed_width=np.nan, secs=0.0, rel=rel[n])
    res['stay_at_rest'][n] = dict(t=c['t'], h=hr / c['rest'], lift_mm=np.zeros_like(c['t']), pressed_width=np.nan, secs=0.0, rel=rel[n])
# --- axisymmetric FEM: tin-retreat protocol (fitted) and the older instant-release protocol (ablation, its own fit)
tg = np.arange(0, 0.25, 0.002); fem = FEM()
def run_fem(P, use_tin, rd=0.0, mult=1.0):
    prm = np.array(P['prm']); prm[2] *= mult; out = {}
    for n in CLIPS:
        t0 = time.time(); cd, plan, x = simulate_clip(fem, n, prm, use_tin=use_tin, rel=rd); wp.synchronize(); secs = time.time() - t0
        k = np.clip(np.round((plan['n_sep'] * plan['dt'] + tg) / plan['dt']).astype(int), 0, plan['n']); h = (x[k, fem.top, 1] - x[k, fem.bot, 1]) / 0.067
        lift = np.maximum(x[k, fem.bot, 1], 0) * 1e3; kh = plan['n_sq'] + plan['n_hold'] - 1; arc = x[kh, fem.arc]; zt, zb = x[kh, fem.top, 1], x[kh, fem.bot, 1]
        w = np.array([2 * np.interp(zt - (zt - zb) * j / 47, arc[:, 1], arc[:, 0]) for j in range(48)]) * 6000.0; _, nh, _ = fit_frame(w, None)
        out[n] = dict(t=tg, h=h, lift_mm=lift, pressed_width=float(x[kh, :, 0].max() * 2 / 0.067), n_hold=float(nh), secs=secs, rel=rel[n])
    return out
P = json.load(open('models/continuum/fem_axisymmetric_warp/outputs/params_fem.json')); res['fem_axisymmetric_warp'] = run_fem(P, True)
P0 = json.load(open('models/continuum/fem_axisymmetric_warp/outputs/params_fem_instant_release.json')); res['fem_instant_release'] = run_fem(P0, False)
res['fem_relative_damping'] = run_fem(P, True, rd=1.0, mult=16.0)      # damping relative to the centre of mass, 16x the fitted rate (chosen on the training clips: hop_scan.py)
# --- 3D MPM with two damping rates
E_, nu, a_fem, mp, mt = P['params']['E'], P['params']['nu'], P['params']['alpha'], P['params']['mu_plate'], P['params']['mu_table']
a_cal = json.load(open('models/continuum/mpm_3d_warp/outputs/params_mpm.json'))['alpha']
for name, a in (('mpm_3d_warp_fem_damping', a_fem), ('mpm_3d_warp', a_cal)):
    res[name] = {}
    for n in CLIPS:
        c = cs[n]; pxm = c['rest'] / 0.067; t0 = time.time(); out = M.simulate(E_, nu, a, mp, mt, 'flat', depth=c['hc'] / pxm, rec_dt=1 / 240, tin=c['tin']); secs = time.time() - t0
        t = np.array(out['t']); ih = np.flatnonzero(t < -c['tin'][0][-1])[-1]; y0 = out['snaps'][0][:, 1].min()
        lift = np.array([max(s[:, 1].min() - y0, 0) for s in out['snaps']]) * 1e3; w = np.array(out['width'])
        res[name][n] = dict(t=t, h=np.array(out['height']) / 0.067, lift_mm=lift, pressed_width=float(np.max(w[max(ih - 4, 0):ih + 1]) / w[0]), n_hold=np.nan, secs=secs, rel=rel[n], alpha=a)
pickle.dump(res, open('evaluation/model_comparison/outputs/curves_continuum.pkl', 'wb'))
print('timing for IMG_0538 (s):', {k: round(v['IMG_0538']['secs'], 1) for k, v in res.items() if k != 'truth'})
