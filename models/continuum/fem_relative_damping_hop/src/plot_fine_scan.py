"""Height error, 95 % recovery time, hop and score against the damping multiplier, from outputs/hop_scan_fine.json (14-16 only). Run: python plot_fine_scan.py"""
import json
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
O = 'models/continuum/fem_relative_damping_hop/outputs'; d = json.load(open(f'{O}/hop_scan_fine.json')); CL = ['IMG_0536', 'IMG_0537', 'IMG_0538', 'IMG_0539']
ks = [k for k in d if k.startswith('relative') and 14 <= float(k.split('x')[1]) <= 16]; m = [float(k.split('x')[1]) for k in ks]
fig, ax = plt.subplots(2, 2, figsize=(11, 7.5))
for n, st in zip(CL, ('o-', 's-', 'o--', 's--')):
    lab = n[-4:] + (' train' if n in CL[:2] else ' test')
    ax[0, 0].plot(m, [d[k][n]['rmse'] for k in ks], st, label=lab); ax[0, 1].plot(m, [d[k][n]['t95'] for k in ks], st, label=lab); ax[1, 0].plot(m, [d[k][n]['hop'] for k in ks], st, label=lab)
    ax[0, 1].axhline(d['real_t95_ms'][n], color=ax[0, 1].lines[-1].get_color(), ls=':', lw=1); ax[1, 0].axhline(d['real_hop_mm'][n], color=ax[1, 0].lines[-1].get_color(), ls=':', lw=1)
ax[1, 1].plot(m, [d[k]['train_score'] for k in ks], 'o-', label='training score (used to choose)'); ax[1, 1].plot(m, [d[k]['test_score'] for k in ks], 's--', label='test score (not used)')
for a, t in zip(ax.flat, ('height RMSE (% of rest height)', '95 % recovery time (ms); dotted = real', 'hop (mm); dotted = real', 'score = RMSE + 0.1 |t95 err| + 0.3 |hop err|')): a.set_title(t, fontsize=10); a.set_xlabel('damping multiplier'); a.grid(alpha=.3); a.legend(fontsize=7)
plt.tight_layout(); plt.savefig(f'{O}/hop_fine_scan_14to16.png', dpi=90); print('wrote', f'{O}/hop_fine_scan_14to16.png')
