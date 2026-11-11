"""Compare every model on the same footing. Truth = SAM 2 measurements of the real clips (height after release, pressed width, squareness, hop).
Models run with their saved parameters (collect_earlier.py, collect_continuum.py); times are aligned to the SAM 2 release instant.
Train = 0536, 0537 (all models fitted on them); test = 0538, 0539. Writes outputs/results.md, results.json and the figures. Usage: compare_all.py"""
import pickle, json, os
import numpy as np, cv2
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

OUT = 'evaluation/model_comparison/outputs'
CLIPS = ['IMG_0536', 'IMG_0537', 'IMG_0538', 'IMG_0539']; TRAIN, TEST = CLIPS[:2], CLIPS[2:]
R = {**pickle.load(open(f'{OUT}/curves_earlier.pkl', 'rb')), **pickle.load(open(f'{OUT}/curves_continuum.pkl', 'rb'))}; TRUTH = R.pop('truth')
INFO = {  # key: (label, family, colour, style)
    'stay_at_rest': ('stay at rest (baseline)', 'baseline', '#999999', ':'), 'exp_baseline': ('single exponential (baseline)', 'baseline', '#555555', '--'),
    'bounce_recovery': ('bounce + recovery', 'lumped 1D', '#1f77b4', '-'), 'two_mass_spring': ('two-mass spring', 'lumped 1D', '#4a98d9', '-'), 'fast_snap': ('fast-snap two-mass', 'lumped 1D', '#8ec1ea', '-'),
    'gas_shell': ('3D gas shell', '3D spring mesh', '#d62728', '-'), 'foam_core_height_fit': ('3D foam core, height fit', '3D spring mesh', '#ff7f0e', '-'), 'foam_core_shape_fit': ('3D foam core, shape fit', '3D spring mesh', '#e8a33d', '-'),
    'foam_core_no_lift': ('3D foam core, no-lift', '3D spring mesh', '#f2c57c', '-'), 'foam_core_with_lift': ('3D foam core, with-lift', '3D spring mesh', '#b5651d', '-'),
    'fem_instant_release': ('axisymmetric FEM, instant release (old protocol)', 'continuum', '#b7e3b7', ':'), 'fem_axisymmetric_warp': ('axisymmetric FEM (Warp)', 'continuum', '#2ca02c', '-'), 'mpm_3d_warp_fem_damping': ('3D MPM, FEM damping', 'continuum', '#9ad39a', '-'), 'mpm_3d_warp': ('3D MPM, calibrated damping', 'continuum', '#006400', '-')}
KEYS = [k for k in INFO if k in R]
GRID = np.arange(0, 0.25, 0.005); FINE = np.arange(0, 0.25, 0.001)
NOT_COMPARABLE = {'bounce_recovery'}                       # only predicts the time after its first hop apex (height already ~99 %), so height error and t95 are not comparable
CURVE_W = {'foam_core_shape_fit', 'foam_core_no_lift', 'foam_core_with_lift'}   # report the width parameter W of the fitted outline curve, not the raw maximum width

def aligned(k, n):
    d = R[k][n]; return d['t'] + (d['rel'] - TRUTH[n]['rel']), d
def curve(k, n, key, grid):
    t, d = aligned(k, n); y = np.asarray(d[key], float); ok = (grid >= t.min() - 1e-9) & (grid <= t.max() + 1e-9)
    out = np.full(len(grid), np.nan); out[ok] = np.interp(grid[ok], t, y); return out
def t95(t, h):
    i = np.flatnonzero(h >= 0.95); return float(t[i[0]]) * 1e3 if len(i) else np.nan
M = {}  # metrics[k][n]
for k in KEYS:
    M[k] = {}
    for n in CLIPS:
        tt, tr = TRUTH[n]['t'], TRUTH[n]['h']; h = curve(k, n, 'h', GRID); ht = np.interp(GRID, tt, tr); ok = ~np.isnan(h)
        hf = curve(k, n, 'h', FINE); mono = np.fmax.accumulate(np.where(np.isnan(hf), -1, hf))
        nc = k in NOT_COMPARABLE
        M[k][n] = dict(rmse=np.nan if nc else (100 * np.sqrt(np.mean((h[ok] - ht[ok]) ** 2)) if ok.any() else np.nan), rmse_window=100 * np.sqrt(np.mean((h[ok] - ht[ok]) ** 2)) if ok.any() else np.nan, t95=np.nan if nc else t95(FINE, mono), hop=float(np.nanmax(curve(k, n, 'lift_mm', GRID))) if ok.any() else np.nan,
                       pw=R[k][n].get('pressed_width', np.nan), nh=R[k][n].get('n_hold', np.nan), secs=R[k][n]['secs'], window=('after first apex only' if R[k][n].get('valid_from_apex') else 'from release'))
TW = lambda k, n: TRUTH[n]['pressed_width_curve'] if k in CURVE_W else TRUTH[n]['pressed_width']
TR = {n: dict(t95=t95(FINE, np.fmax.accumulate(np.interp(FINE, TRUTH[n]['t'], TRUTH[n]['h']))), hop=float(np.nanmax(TRUTH[n]['lift_mm'])), pw=TRUTH[n]['pressed_width'], nh=TRUTH[n]['n_hold']) for n in CLIPS}
avg = lambda k, m, names: float(np.nanmean([M[k][n][m] for n in names]))
fm = lambda v, f='{:.1f}': ('-' if v is None or (isinstance(v, float) and np.isnan(v)) else f.format(v))

# ---------------- figures
cl = {'IMG_0536': '0536 (train, 41 % pressed)', 'IMG_0537': '0537 (train, 36 %)', 'IMG_0538': '0538 (TEST, 63 %)', 'IMG_0539': '0539 (TEST, 62 %)'}
fig, ax = plt.subplots(2, 2, figsize=(16, 9), sharey=True)
for a, n in zip(ax.ravel(), CLIPS):
    a.plot(TRUTH[n]['t'] * 1e3, TRUTH[n]['h'], 'k.', ms=4, label='real (SAM 2)')
    for k in KEYS:
        t, d = aligned(k, n); a.plot(t * 1e3, d['h'], color=INFO[k][2], ls=INFO[k][3], lw=1.6, label=INFO[k][0])
    a.set_xlim(0, 120); a.set_ylim(0.3, 1.12); a.set_title(cl[n]); a.set_xlabel('ms after release'); a.set_ylabel('height / rest height'); a.grid(alpha=.3)
ax[0, 0].legend(fontsize=7, ncol=2, loc='lower right'); plt.tight_layout(); plt.savefig(f'{OUT}/fig1_height_curves_all.png', dpi=85); plt.close()

fams = ['lumped 1D', '3D spring mesh', 'continuum']; fig, ax = plt.subplots(3, 2, figsize=(14, 11), sharey=True)
for r, fam in enumerate(fams):
    for c_, n in enumerate(('IMG_0536', 'IMG_0538')):
        a = ax[r, c_]; a.plot(TRUTH[n]['t'] * 1e3, TRUTH[n]['h'], 'k.', ms=4, label='real'); 
        for k in ('exp_baseline',) + tuple(x for x in KEYS if INFO[x][1] == fam):
            t, d = aligned(k, n); a.plot(t * 1e3, d['h'], color=INFO[k][2], ls=INFO[k][3], lw=1.8, label=INFO[k][0])
        a.set_xlim(0, 120); a.set_ylim(0.3, 1.12); a.grid(alpha=.3); a.set_title(f'{fam}: {cl[n]}', fontsize=10); a.legend(fontsize=7, loc='lower right')
        if r == 2: a.set_xlabel('ms after release')
        if c_ == 0: a.set_ylabel('height / rest height')
plt.tight_layout(); plt.savefig(f'{OUT}/fig2_height_by_family.png', dpi=85); plt.close()

def bars(metric, ylabel, fname, title, truth_lines=None, test_only=False, logy=False):
    fig, ax = plt.subplots(figsize=(14, 5)); keys = [k for k in KEYS if not np.isnan(avg(k, metric, TEST))]; x = np.arange(len(keys)); w = 0.38
    if not test_only: ax.bar(x - w / 2, [avg(k, metric, TRAIN) for k in keys], w, color='#bbbbbb', label='train clips (0536, 0537)')
    ax.bar(x + (0 if test_only else w / 2), [avg(k, metric, TEST) for k in keys], w, color=[INFO[k][2] for k in keys], edgecolor='k', label='held-out clips (0538, 0539)')
    if truth_lines is not None:
        for lab, v, ls in truth_lines: ax.axhline(v, color='k', ls=ls, lw=1, label=lab)
    ax.set_xticks(x); ax.set_xticklabels([INFO[k][0] for k in keys], rotation=35, ha='right', fontsize=8); ax.set_ylabel(ylabel); ax.set_title(title); ax.grid(axis='y', alpha=.3); ax.legend(fontsize=8)
    if logy: ax.set_yscale('log')
    plt.tight_layout(); plt.savefig(f'{OUT}/{fname}', dpi=85); plt.close()
bars('rmse', 'height RMSE (% of rest height)', 'fig3_height_rmse.png', 'Height error after release, 0-250 ms (lower is better; bounce model only covers the time after its first hop apex)', [('plain exponential, held-out', avg('exp_baseline', 'rmse', TEST), '--')])
fig, ax = plt.subplots(figsize=(14, 5)); keys = [k for k in KEYS if k != 'stay_at_rest']; x = np.arange(len(keys))
for j, n in enumerate(CLIPS): ax.plot(x + (j - 1.5) * 0.12, [M[k][n]['t95'] for k in keys], 'o', color='C%d' % j, label=cl[n])
for j, n in enumerate(CLIPS): ax.axhline(TR[n]['t95'], color='C%d' % j, ls=':', lw=1)
ax.set_xticks(x); ax.set_xticklabels([INFO[k][0] for k in keys], rotation=35, ha='right', fontsize=8); ax.set_ylabel('time to 95 % of rest height (ms)'); ax.set_title('Recovery time: models (dots) against the real clips (dotted lines of the same colour)'); ax.legend(fontsize=8); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig(f'{OUT}/fig4_recovery_time.png', dpi=85); plt.close()
fig, ax = plt.subplots(1, 2, figsize=(15, 4.8))
for a, (m, lab, title) in zip(ax, (('pw', 'width pressed / width at rest', 'Pressed width (mesh shape fits: curve width, own truth)'), ('hop', 'peak lift of the bottom edge (mm)', 'Hop height'))):
    keys = [k for k in KEYS if not all(np.isnan([M[k][n][m] for n in CLIPS]))]; x = np.arange(len(keys))
    for j, n in enumerate(CLIPS): a.plot(x + (j - 1.5) * 0.12, [M[k][n][m] for k in keys], 'o', color='C%d' % j, label=cl[n]); a.axhline(TR[n][m], color='C%d' % j, ls=':', lw=1)
    a.set_xticks(x); a.set_xticklabels([INFO[k][0] for k in keys], rotation=40, ha='right', fontsize=7); a.set_ylabel(lab); a.set_title(title + ' (dotted = real)'); a.grid(alpha=.3)
    if m == 'hop': a.set_yscale('symlog', linthresh=1)
ax[0].legend(fontsize=7); plt.tight_layout(); plt.savefig(f'{OUT}/fig5_width_and_hop.png', dpi=85); plt.close()

# scorecard heat map (test clips): lower is better in every column
cols = [('height RMSE, test (%)', lambda k: avg(k, 'rmse', TEST)), ('skill vs exponential, all 4 clips', lambda k: float(np.nanmean([1 - M[k][n]['rmse'] / M['exp_baseline'][n]['rmse'] for n in CLIPS])) * -1), ('|t95 error| (ms)', lambda k: float(np.nanmean([abs(M[k][n]['t95'] - TR[n]['t95']) for n in TEST]))),
        ('|pressed width error|', lambda k: float(np.nanmean([abs(M[k][n]['pw'] - TW(k, n)) for n in TEST]))), ('|hop error| (mm)', lambda k: float(np.nanmean([abs(M[k][n]['hop'] - TR[n]['hop']) for n in TEST]))),
        ('forward run (s)', lambda k: M[k]['IMG_0538']['secs'])]
keys = [k for k in KEYS if k not in ('stay_at_rest',)]; V = np.array([[f(k) for _, f in cols] for k in keys], float)
rank = np.full_like(V, np.nan)
for j in range(V.shape[1]):
    ok = ~np.isnan(V[:, j]); r = np.argsort(np.argsort(V[ok, j])); rank[ok, j] = r / max(ok.sum() - 1, 1)
fig, ax = plt.subplots(figsize=(11, 6.2)); ax.imshow(np.ma.masked_invalid(rank), cmap='RdYlGn_r', vmin=0, vmax=1, aspect='auto')
for i in range(V.shape[0]):
    for j in range(V.shape[1]): ax.text(j, i, '-' if np.isnan(V[i, j]) else (f'{-V[i, j]:+.2f}' if j == 1 else (f'{V[i, j]:.1f}' if j != 3 else f'{V[i, j]:.3f}')), ha='center', va='center', fontsize=8)
ax.set_xticks(range(len(cols))); ax.set_xticklabels([c[0] for c in cols], fontsize=8); ax.set_yticks(range(len(keys))); ax.set_yticklabels([INFO[k][0] for k in keys], fontsize=8); ax.set_title('Scorecard on the held-out clips (green = better rank in that column)')
plt.tight_layout(); plt.savefig(f'{OUT}/fig6_scorecard.png', dpi=85); plt.close()

# gallery of the model panels from the existing videos (held-out clip 0538): pressed state and 32 ms after release
def grab(path, idx, box):
    cap = cv2.VideoCapture(path); cap.set(cv2.CAP_PROP_POS_FRAMES, idx); ok, f = cap.read(); cap.release()
    return None if not ok else cv2.cvtColor(f[box[0]:box[1], box[2]:box[3]], cv2.COLOR_BGR2RGB)
V3 = lambda m, n='IMG_0538': f'models/mesh_3d/{m}/outputs/real_vs_3d_{n}.mp4'
Tr = TRUTH['IMG_0538']['tin_T']; T_PRESS, T_FREE = -(Tr + 0.02), 0.032      # pressed hold (just before the tin retreats) and 32 ms after the ball separates from the tin
i3 = lambda t: int(round((t + Tr + 0.03) * 240)); i1 = lambda t: int(round((t + 0.25) * 240))   # frame index on the 3D videos' axis (starts at -(Tr + 30 ms)) and on the 1D demos' axis (starts at -250 ms)
tiles = [('real clip', 'models/continuum/fem_axisymmetric_warp/outputs/real_vs_fem_IMG_0538.mp4', (34, 534, 0, 500), 'v3')]
tiles += [(INFO[m][0], V3(m), (34, 534, 500, 1000), 'v3') for m in ('gas_shell', 'foam_core_height_fit', 'foam_core_shape_fit', 'foam_core_no_lift', 'foam_core_with_lift')]
tiles += [('two-mass spring (ellipsoid proxy)', 'models/lumped_1d/two_mass_spring/outputs/demo_squeeze_IMG_0538.mp4', (60, 500, 528, 1056), 'v1'), ('fast-snap two-mass (ellipsoid proxy)', 'models/lumped_1d/fast_snap/outputs/demo_snap_IMG_0538.mp4', (60, 500, 528, 1056), 'v1'),
          ('axisymmetric FEM (Warp)', 'models/continuum/fem_axisymmetric_warp/outputs/real_vs_fem_IMG_0538.mp4', (34, 534, 500, 1000), 'v3'), ('3D MPM (Warp)', 'models/continuum/mpm_3d_warp/outputs/real_vs_mpm_IMG_0538.mp4', (34, 534, 500, 1000), 'v3')]
fig, ax = plt.subplots(2, len(tiles), figsize=(2.3 * len(tiles), 5.4))
for j, (lab, path, box, kind) in enumerate(tiles):
    ix = i3 if kind == 'v3' else i1
    for r, idx in enumerate((ix(T_PRESS), ix(T_FREE))):
        a = ax[r, j]; a.axis('off'); im = grab(path, idx, box) if os.path.exists(path) else None
        if im is not None: a.imshow(im)
        if r == 0: a.set_title(lab, fontsize=7)
ax[0, 0].text(-0.05, 0.5, 'pressed (hold)', transform=ax[0, 0].transAxes, rotation=90, va='center', ha='right', fontsize=8); ax[1, 0].text(-0.05, 0.5, '+32 ms after separation', transform=ax[1, 0].transAxes, rotation=90, va='center', ha='right', fontsize=8)
plt.tight_layout(); plt.savefig(f'{OUT}/fig7_gallery_IMG_0538.png', dpi=90); plt.close()

# ---------------- tables
L = []; hdr = lambda cols_: ['| ' + ' | '.join(cols_) + ' |', '| ' + ' | '.join(['---'] * len(cols_)) + ' |']
L += ['## 1. Height error after release (RMSE, % of rest height; 0-250 ms; lower is better)'] + hdr(['Model', 'Family', 'Window', '0536 train', '0537 train', '0538 TEST', '0539 TEST', 'test mean'])
for k in KEYS: L.append(f"| {INFO[k][0]} | {INFO[k][1]} | {M[k]['IMG_0538']['window']} | " + ' | '.join(fm(M[k][n]['rmse']) for n in CLIPS) + f" | **{fm(avg(k, 'rmse', TEST))}** |")
L += ['', '**Skill against the plain exponential** (1 - model RMSE / exponential RMSE on the same clip; positive = better than the baseline)'] + hdr(['Model', '0536 train', '0537 train', '0538 TEST', '0539 TEST'])
for k in KEYS:
    if k in ('stay_at_rest', 'exp_baseline') or k in NOT_COMPARABLE: continue
    L.append(f"| {INFO[k][0]} | " + ' | '.join(fm(1 - M[k][n]['rmse'] / M['exp_baseline'][n]['rmse'], '{:+.2f}') for n in CLIPS) + ' |')
L += ['', '## 2. Time to 95 % of rest height (ms)'] + hdr(['Model', '0536 train', '0537 train', '0538 TEST', '0539 TEST', 'mean |error| on test'])
L.append('| **real (SAM 2)** | ' + ' | '.join(fm(TR[n]['t95'], '{:.0f}') for n in CLIPS) + ' | - |')
for k in KEYS:
    if k == 'stay_at_rest': continue
    L.append(f"| {INFO[k][0]} | " + ' | '.join(fm(M[k][n]['t95'], '{:.0f}') for n in CLIPS) + f" | {fm(np.nanmean([abs(M[k][n]['t95'] - TR[n]['t95']) for n in TEST]), '{:.0f}')} |")
L += ['', '## 3. Pressed width (width while pressed / width at rest) and squeezed-outline squareness n'] + hdr(['Model', '0536 train', '0537 train', '0538 TEST', '0539 TEST', 'n at hold (mean of clips)'])
L.append('| **real (SAM 2)** | ' + ' | '.join(fm(TR[n]['pw'], '{:.3f}') for n in CLIPS) + f" | {fm(np.nanmean([TR[n]['nh'] for n in CLIPS]), '{:.1f}')} |")
for k in KEYS:
    if all(np.isnan([M[k][n]['pw'] for n in CLIPS])): continue
    L.append(f"| {INFO[k][0]}{' (curve width; real = ' + ', '.join(fm(TW(k, n), '{:.3f}') for n in CLIPS) + ')' if k in CURVE_W else ''} | " + ' | '.join(fm(M[k][n]['pw'], '{:.3f}') for n in CLIPS) + f" | {fm(np.nanmean([M[k][n]['nh'] for n in CLIPS]), '{:.1f}')} |")
L += ['', '## 4. Hop: peak lift of the bottom edge (mm; real hops are 3-8 mm)'] + hdr(['Model', '0536 train', '0537 train', '0538 TEST', '0539 TEST'])
L.append('| **real (SAM 2)** | ' + ' | '.join(fm(TR[n]['hop']) for n in CLIPS) + ' |')
for k in KEYS:
    if k in ('stay_at_rest', 'exp_baseline'): continue
    L.append(f"| {INFO[k][0]} | " + ' | '.join(fm(M[k][n]['hop']) for n in CLIPS) + ' |')
L += ['', '## 5. Cost of one forward run (s, clip 0538, laptop CPU/GPU)'] + hdr(['Model', 'seconds'])
for k in KEYS:
    if k in ('stay_at_rest', 'exp_baseline'): continue
    L.append(f"| {INFO[k][0]} | {fm(M[k]['IMG_0538']['secs'], '{:.1f}')} |")
open(f'{OUT}/results_tables.md', 'w').write('\n'.join(L) + '\n')
json.dump({k: {n: {a: (None if isinstance(b, float) and np.isnan(b) else b) for a, b in v.items()} for n, v in d.items()} for k, d in M.items()} | {'truth': TR}, open(f'{OUT}/metrics.json', 'w'), indent=1, default=float)
print('\n'.join(L))
