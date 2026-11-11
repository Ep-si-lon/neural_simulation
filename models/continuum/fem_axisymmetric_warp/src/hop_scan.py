"""Scan the strength of the centre-of-mass-relative damping (multiples of the fitted absolute-damping rate). Score = height RMSE (%) + 0.1 x mean |recovery-time error| (ms) + 0.3 x mean |hop error| (mm),
averaged over the TRAINING clips (0536, 0537) only; the held-out clips (0538, 0539) are reported but not used to choose. Writes outputs/hop_scan.json and hop_scan.png. Run from the repo root with TRACKER=sam2."""
import sys, json
import numpy as np
sys.path[:0] = ['shared', 'tracking/src', 'models/continuum/fem_axisymmetric_warp/src']
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from fem_axi import FEM
from fit_fem import simulate_clip, OUT
from clip_prep import prep

P = json.load(open(f'{OUT}/params_fem.json')); base = np.array(P['prm']); fem = FEM(); tg = np.arange(0, 0.25, 0.002)
CL = ['IMG_0536', 'IMG_0537', 'IMG_0538', 'IMG_0539']; TRAIN = CL[:2]; cs = {n: prep(n) for n in CL}; MULTS = [8, 12, 16, 24, 32, 48]
real_hop = {n: float(np.nanmax(cs[n]['lift'] / cs[n]['rest'] * 67)) for n in CL}
def t95(t, h):
    i = np.flatnonzero(np.fmax.accumulate(h) >= 0.95); return float(t[i[0]]) * 1e3 if len(i) else np.nan
real_t95 = {n: t95(cs[n]['t'], cs[n]['h'] / cs[n]['rest']) for n in CL}
def run(n, mult, rel):
    p = base.copy(); p[2] *= mult; cd, plan, x = simulate_clip(fem, n, p, rel=rel); c = cs[n]
    k = np.clip(np.round((plan['n_sep'] * plan['dt'] + tg) / plan['dt']).astype(int), 0, plan['n']); h = (x[k, fem.top, 1] - x[k, fem.bot, 1]) / 0.067; lift = np.maximum(x[k, fem.bot, 1], 0) * 1e3
    rm = 100 * np.sqrt(np.mean((h - np.interp(tg, c['t'], c['h'] / c['rest'])) ** 2)); return dict(rmse=rm, t95_err=abs(t95(tg, h) - real_t95[n]), t95=t95(tg, h), hop=float(lift.max()), hop_err=abs(float(lift.max()) - real_hop[n]), lift=lift.tolist())
rows = {'absolute (as fitted)': {n: run(n, 1.0, 0.0) for n in CL}}
for m in MULTS:
    rows[f'relative x{m}'] = {n: run(n, float(m), 1.0) for n in CL}; print('done x', m, flush=True)
def score(r, names): return float(np.mean([r[n]['rmse'] + 0.1 * r[n]['t95_err'] + 0.3 * r[n]['hop_err'] for n in names]))
print('real hop (mm):', {n[-4:]: round(v, 1) for n, v in real_hop.items()}, '| real t95 (ms):', {n[-4:]: round(v) for n, v in real_t95.items()})
print(f"{'variant':24s} " + ' '.join(f'{n[-4:]:>22s}' for n in CL) + '   train score  test score')
for k, r in rows.items():
    print(f'{k:24s} ' + ' '.join(f"{r[n]['rmse']:4.1f}% {r[n]['t95']:3.0f}ms {r[n]['hop']:5.1f}mm" for n in CL) + f'   {score(r, TRAIN):8.2f}  {score(r, CL[2:]):8.2f}')
best = min((k for k in rows if k.startswith('relative')), key=lambda k: score(rows[k], TRAIN)); print('best relative strength on the training clips:', best)
json.dump({k: {n: {a: b for a, b in v.items() if a != 'lift'} for n, v in r.items()} | {'train_score': score(r, TRAIN), 'test_score': score(r, CL[2:])} for k, r in rows.items()} | {'best_on_training': best, 'real_hop_mm': real_hop, 'real_t95_ms': real_t95}, open(f'{OUT}/hop_scan.json', 'w'), indent=1)
fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
for a, n in zip(ax, ('IMG_0536', 'IMG_0538')):
    a.plot(cs[n]['t'] * 1e3, cs[n]['lift'] / cs[n]['rest'] * 67, 'k.-', label='real')
    for k, r in rows.items(): a.plot(tg * 1e3, r[n]['lift'], label=k, lw=2 if k == best else 1)
    a.set_yscale('symlog', linthresh=2); a.set_title(f'{n}: lift of the bottom edge (mm)'); a.set_xlabel('ms after separation'); a.grid(alpha=.3)
ax[0].legend(fontsize=7); plt.tight_layout(); plt.savefig(f'{OUT}/hop_scan.png', dpi=85)
