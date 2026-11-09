"""Hop height and recovery time: real clips vs the 3D foam model fitted WITHOUT the lift term (foam_core_no_lift) and WITH it (foam_core_with_lift).
Both trained on 0536+0537, run unchanged on 0538+0539. Hop height = peak bottom lift in mm (ball height 67 mm = rest height).
Run: models/mesh_3d/foam_core_with_lift/render.sh -> outputs/hop_check.md, hops.png"""
import json
import numpy as np
from scipy.signal import medfilt
from common import CLIPS
from clip_prep import prep, HORIZON
from scenario3d import scenario

MM = 67.0
def t_first(t, y, thr): i = np.flatnonzero(y >= thr); return float(t[i[0]]) * 1e3 if len(i) else float('nan')

if __name__ == '__main__':
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    cs = {n: prep(n) for n in CLIPS}
    P = {'no-lift fit': np.log(json.load(open('models/mesh_3d/foam_core_no_lift/outputs/params_3d.json'))['ks_kb_kr_cd']), 'with-lift fit': np.log(json.load(open('models/mesh_3d/foam_core_with_lift/outputs/params_3d_lift.json'))['ks_kb_kr_cd'])}
    fig, ax = plt.subplots(1, 4, figsize=(18, 4)); L = ['| Clip | Set | Real hop (mm) | No-lift model hop (mm) | With-lift model hop (mm) | Real t95 (ms) | No-lift t95 | With-lift t95 |', '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for j, n in enumerate(CLIPS):
        c = cs[n]; real_l = medfilt(c['lift'], 3) / c['rest'] * MM; row = [n[-4:], 'train' if j < 2 else 'TEST', f'{real_l.max():.1f}']
        ax[j].plot(c['t'] * 1e3, real_l, 'k.-', label='real'); t95 = {}
        for lab, col in (('no-lift fit', 'tab:blue'), ('with-lift fit', 'tab:red')):
            T, F = scenario(P[lab], c); ax[j].plot(T * 1e3, F[:, 1] * MM, color=col, label=lab); row.append(f'{F[:, 1].max() * MM:.1f}'); t95[lab] = t_first(T, F[:, 0], .95)
        h = medfilt(np.pad(c['h'] / c['rest'], 2, mode='edge'), 5)[2:-2]; row += [f'{t_first(c["t"], h, .95):.0f}', f'{t95["no-lift fit"]:.0f}', f'{t95["with-lift fit"]:.0f}']
        L.append('| ' + ' | '.join(row) + ' |'); ax[j].set_title(f'{n[-4:]} bottom lift (mm)'); ax[j].set_xlabel('ms after release')
    ax[0].legend(); plt.tight_layout(); plt.savefig('models/mesh_3d/foam_core_with_lift/outputs/hops.png', dpi=80)
    pr = {k: [round(float(v), 1) for v in np.exp(p)] for k, p in P.items()}
    out = '\n'.join(L) + f'\n\nparams (ks, kb, kr, cd): {pr}\n'
    open('models/mesh_3d/foam_core_with_lift/outputs/hop_check.md', 'w').write(out); print(out)
