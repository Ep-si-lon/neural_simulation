"""Forward-run every earlier model (lumped 1D, spring-mesh 3D) with its saved parameters on all four clips and store height / hop / pressed-width curves.
These models were fitted on the colour-tracker data, so this step runs with the default tracker (.venv). Output: outputs/curves_earlier.pkl
(times are relative to each clip's own release instant; the comparison step aligns them to the SAM 2 release)."""
import sys, json, time, pickle, importlib.util
import numpy as np
from common import CLIPS
from clip_prep import prep

M = 'models/'; TRAIN = CLIPS[:2]; MM = 67.0
def load(path, name):
    sys.path.insert(0, path.rsplit('/', 1)[0]); spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
J = lambda p: json.load(open(p))
cs = {n: prep(n) for n in CLIPS}; rel = {n: float(cs[n]['full_t'][cs[n]['i_rel']]) for n in CLIPS}
res = {}
def put(model, n, t, h, lift_mm, pw, secs, **kw): res.setdefault(model, {})[n] = dict(t=np.asarray(t), h=np.asarray(h), lift_mm=np.asarray(lift_mm), pressed_width=pw, secs=secs, rel=rel[n], **kw)

# --- two-mass spring and fast-snap (px units, simulate(p, c, t_eval) -> h, top, lift)
sim = load(M + 'lumped_1d/two_mass_spring/src/sim.py', 'sim_two_mass'); P = J(M + 'lumped_1d/two_mass_spring/outputs/sim_params.json')['split']
snap = load(M + 'lumped_1d/fast_snap/src/snap_sim.py', 'snap_sim'); Q = J(M + 'lumped_1d/fast_snap/outputs/params.json')['split']
tg = np.arange(0, 0.25, 0.002)
for n in CLIPS:
    c = cs[n]; t0 = time.time(); h, _, l = sim.simulate(np.log(P), c, tg); put('two_mass_spring', n, tg[:len(h)], h / c['rest'], l / c['rest'] * MM, np.nan, time.time() - t0)
    t0 = time.time(); h, _, l = snap.simulate(np.array([np.log(Q[0]), np.log(Q[1]), np.log(Q[2]), Q[3]]), c, tg); put('fast_snap', n, tg[:len(h)], h / c['rest'], l / c['rest'] * MM, np.nan, time.time() - t0)

# --- bounce + recovery (valid only after the first apex of the hop)
bf = load(M + 'lumped_1d/bounce_recovery/src/fit.py', 'bounce_fit'); bcs = {n: bf.prep(n) for n in CLIPS}
e, tau, tc = bf.fit([bcs[n] for n in TRAIN])
for n in CLIPS:
    c = bcs[n]; t0 = time.time(); da = c['h'][0]; A = max(c['y'][0] - c['rest'] * da, 1.0)
    L = bf.lift(np.clip(c['t'], 0, None), A, e, bf.G * c['pxm'], tc); h = 1 + da * np.exp(-np.clip(c['t'], 0, None) / tau)
    put('bounce_recovery', n, c['t'] + (c['ta'] - rel[n]), h, L / c['rest'] * MM, np.nan, time.time() - t0, valid_from_apex=True)

# --- 3D spring meshes
gas = load(M + 'mesh_3d/gas_shell/src/fit_gas.py', 'gas_fit'); G = J(M + 'mesh_3d/gas_shell/outputs/params_gas.json')['split']
hf = load(M + 'mesh_3d/foam_core_height_fit/src/fit3d.py', 'height_fit'); H = J(M + 'mesh_3d/foam_core_height_fit/outputs/params.json')['split']
for n in CLIPS:
    for name, mod, par in (('gas_shell', gas, G), ('foam_core_height_fit', hf, H)):
        t0 = time.time(); ts, hs, ls, wh = mod.scenario(np.log(par), cs[n]); put(name, n, ts, hs, ls * MM, wh, time.time() - t0)
from scenario3d import scenario
for name, f, key in (('foam_core_shape_fit', M + 'mesh_3d/foam_core_shape_fit/outputs/params_shape.json', 'split'), ('foam_core_no_lift', M + 'mesh_3d/foam_core_no_lift/outputs/params_3d.json', 'ks_kb_kr_cd'),
                     ('foam_core_with_lift', M + 'mesh_3d/foam_core_with_lift/outputs/params_3d_lift.json', 'ks_kb_kr_cd')):
    par = J(f)[key]
    for n in CLIPS:
        t0 = time.time(); T, F = scenario(np.log(par), cs[n]); put(name, n, T, F[:, 0], F[:, 1] * MM, F[0, 2], time.time() - t0, n_hold=F[0, 3])
pickle.dump(res, open('evaluation/model_comparison/outputs/curves_earlier.pkl', 'wb'))
print({k: {n: round(v['secs'], 1) for n, v in d.items() if n == 'IMG_0538'} for k, d in res.items()})
