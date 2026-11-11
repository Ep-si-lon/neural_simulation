"""The MPM, run with the FEM-fitted material, recovers about 25 % faster than the real ball on the deep-squeeze training clips (grid dissipation differs from the FEM's nodal damping).
One-parameter calibration: scan the damping rate alpha on the TRAINING clips only (0536, 0537), keep E, nu and friction from the FEM, pick the alpha with the lowest score = mean height RMSE (%) + 0.1 x mean |recovery-time error| (ms),
and save it to outputs/params_mpm.json (run_mpm.py then uses it). The held-out clips are not looked at. Writes outputs/alpha_scan.json and alpha_scan.png."""
import json, sys
import numpy as np
import mpm3d as M
from common import CLIPS
from clip_prep import prep

FEM_JSON = 'models/continuum/fem_axisymmetric_warp/outputs/params_fem.json'
OUT = 'models/continuum/mpm_3d_warp/outputs'
ALPHA_FACTORS = [0.6, 0.8, 1.0, 1.25, 1.6]            # scan around the FEM's damping rate

def t95(t, h, rest):
    i = np.flatnonzero(h >= 0.95 * rest); return float(t[i[0]]) * 1e3 if len(i) else float('nan')

def run(E, nu, a, mp, mt, c):
    pxm = c['rest'] / 0.067; out = M.simulate(E, nu, a, mp, mt, 'flat', depth=c['hc'] / pxm, rec_dt=1 / 240, tin=c['tin'])
    t = np.array(out['t']); h = np.array(out['height']) * pxm; hs = np.interp(c['t'], t, h)
    return 100 * np.sqrt(np.mean((hs - c['h']) ** 2)) / c['rest'], t95(t[t >= 0], h[t >= 0], c['rest']), (t, h)

if __name__ == '__main__':
    P = json.load(open(FEM_JSON))['params']; E, nu, mp, mt = P['E'], P['nu'], P['mu_plate'], P['mu_table']; ALPHAS = [int(round(P['alpha'] * f_)) for f_ in ALPHA_FACTORS]
    train = CLIPS[:2]; cs = {n: prep(n) for n in train}; scan = []; curves = {}
    reuse = '--reselect' in sys.argv           # re-pick alpha from outputs/alpha_scan.json without re-simulating
    for a in ([] if reuse else ALPHAS):
        row = dict(alpha=a)
        for n in train:
            r, t95m, curves[(a, n)] = run(E, nu, a, mp, mt, cs[n]); row[n] = dict(height_rmse=r, t95=t95m, t95_real=t95(cs[n]['t'], np.maximum.accumulate(cs[n]['h']), cs[n]['rest']))
        row['mean_rmse'] = float(np.mean([row[n]['height_rmse'] for n in train])); scan.append(row)
        print(f"alpha {a:5d}: " + '  '.join(f"{n} RMSE {row[n]['height_rmse']:.2f}% t95 {row[n]['t95']:.0f} (real {row[n]['t95_real']:.0f}) ms" for n in train) + f"   mean {row['mean_rmse']:.2f}%", flush=True)
    if reuse: scan = json.load(open(f'{OUT}/alpha_scan.json'))
    for r in scan: r['score'] = r['mean_rmse'] + 0.1 * float(np.mean([abs(r[n]['t95'] - r[n]['t95_real']) for n in train]))
    best = min(scan, key=lambda r: r['score'])
    for r in scan: print(f"alpha {r['alpha']:5d}: height RMSE {r['mean_rmse']:.2f}%, mean |t95 error| {np.mean([abs(r[n]['t95'] - r[n]['t95_real']) for n in train]):.1f} ms, score {r['score']:.2f}")
    json.dump(dict(scan=scan, alpha=best['alpha'], note='alpha chosen on the training clips 0536+0537 only, by height RMSE + 0.1 x |t95 error|'), open(f'{OUT}/params_mpm.json', 'w'), indent=1)
    json.dump(scan, open(f'{OUT}/alpha_scan.json', 'w'), indent=1)
    if reuse: print('chosen alpha (training clips only):', best['alpha']); sys.exit()
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for k, n in enumerate(train):
        c = cs[n]; ax[k].plot(c['t'] * 1e3, c['h'] / c['rest'], 'k.-', label='real (SAM 2)')
        for a in ALPHAS:
            t, h = curves[(a, n)]; m = t >= 0; ax[k].plot(t[m] * 1e3, h[m] / c['rest'], label=f'MPM alpha {a}', lw=2 if a == best['alpha'] else 1)
        ax[k].set_xlim(0, 100); ax[k].set_title(f'{n} (training): height after release'); ax[k].set_xlabel('ms after release'); ax[k].set_ylabel('height / rest height')
    ax[0].legend(fontsize=7); plt.tight_layout(); plt.savefig(f'{OUT}/alpha_scan.png', dpi=80)
    print('chosen alpha (training clips only):', best['alpha'])
