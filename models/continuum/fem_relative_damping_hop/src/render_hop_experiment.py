"""Videos and a plot for the hop experiment (see hop_experiment.py): real clip | FEM as fitted (absolute damping, no hop) | FEM damped relative to the centre of mass at 12x, 16x and 24x the fitted strength.
The view is zoomed out (2400 px per metre) so the large hops stay in frame; damped relative to the centre of mass at 12x, 16x and 24x. Time zero = separation, slowed 8x. Usage: render_hop_experiment.py CLIP"""
import sys, json, subprocess
import numpy as np, cv2
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from fem_axi import FEM
from fit_fem import simulate_clip
OUT = 'models/continuum/fem_relative_damping_hop/outputs'; PARAMS = 'models/continuum/fem_axisymmetric_warp/outputs/params_fem.json'
from realclip import real_panels, PX
from render_fem import panel
from clip_prep import prep

S2, BASE, SLOW, FPS = 2400.0, 60, 8, 30
ALL = [('FEM as fitted: absolute damping (no hop)', 0.0, 1.0), ('relative to centre of mass, 12x damping', 1.0, 12.0), ('relative, 16x damping (best on training clips)', 1.0, 16.0), ('relative, 24x damping', 1.0, 24.0)]

def main(name, mults=None):
    VARIANTS = ALL if mults is None else [(f'relative, {m:g}x damping', 1.0, m) for m in mults]; sfx = '' if mults is None else '_14to16'; NP = len(VARIANTS) + 1; COLS = ('C2', 'C0', 'C1', 'C3') if mults is None else ('C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6')
    P = json.load(open(PARAMS)); base = np.array(P['prm']); fem = FEM(); c = prep(name); sims = []
    for lab, rel, mult in VARIANTS:
        p = base.copy(); p[2] *= mult; cd, plan, x = simulate_clip(fem, name, p, rel=rel); sims.append((plan, x))
    Tr = c['tin'][0][-1]; tt = np.arange(-(Tr + 0.03), 0.25, 1 / (FPS * SLOW)); real = real_panels(name, tt, sc=S2 / (c['pxm']), table_row=PX - BASE)
    out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{NP*PX}x{PX+34}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f'{OUT}/hop_experiment{sfx}_{name}.mp4'], stdin=subprocess.PIPE)
    for t, rp in zip(tt, real):
        cv = np.full((PX + 34, NP * PX, 3), 255, np.uint8); r_ = rp.copy(); cv2.putText(r_, f'REAL {name}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .5, (20, 20, 20), 1, cv2.LINE_AA); cv[34:, :PX] = r_
        for j, ((lab, rel, mult), (plan, x)) in enumerate(zip(VARIANTS, sims)):
            k = int(np.clip(round((plan['n_sep'] * plan['dt'] + t) / plan['dt']), 0, plan['n'])); arc = x[k, fem.arc].astype(np.float64)
            pnl = panel(arc, plan['plate'][k], 0, 0, lab, S_=S2, base=BASE); cv[34:, (j + 1) * PX:(j + 2) * PX] = pnl
        cv2.putText(cv, f'hop experiment: t = {t*1e3:+6.0f} ms from separation (slowed {SLOW}x; scale 2400 px/m)   real hop {np.nanmax(c["lift"]) / c["rest"] * 67:.1f} mm', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .55, (20, 20, 20), 1, cv2.LINE_AA)
        out.stdin.write(cv.tobytes())
    out.stdin.close(); out.wait(); print('wrote', f'{OUT}/hop_experiment{sfx}_{name}.mp4')
    tg = np.arange(0, 0.25, 0.002); fig, ax = plt.subplots(figsize=(8, 4.2)); ax.plot(c['t'] * 1e3, c['lift'] / c['rest'] * 67, 'k.-', label='real (SAM 2)')
    for (lab, rel, mult), (plan, x), col in zip(VARIANTS, sims, COLS):
        k = np.clip(np.round((plan['n_sep'] * plan['dt'] + tg) / plan['dt']).astype(int), 0, plan['n']); ax.plot(tg * 1e3, np.maximum(x[k, fem.bot, 1], 0) * 1e3, color=col, label=lab)
    ax.set_yscale('symlog', linthresh=2); ax.set_xlabel('ms after separation'); ax.set_ylabel('lift of the bottom edge (mm, symlog)'); ax.set_title(f'{name}: hop of the real ball and of the FEM variants'); ax.grid(alpha=.3); ax.legend(fontsize=7)
    plt.tight_layout(); plt.savefig(f'{OUT}/hop_experiment_lift{sfx}_{name}.png', dpi=90); plt.close()
    if mults is not None:      # height and lift on linear axes, all multipliers
        fig, ax = plt.subplots(1, 2, figsize=(13, 4.4)); ax[0].plot(c['t'] * 1e3, c['h'] / c['rest'], 'k.-', label='real (SAM 2)'); ax[1].plot(c['t'] * 1e3, c['lift'] / c['rest'] * 67, 'k.-', label='real (SAM 2)')
        for (lab, rel, mult), (plan, x), col in zip(VARIANTS, sims, COLS):
            k = np.clip(np.round((plan['n_sep'] * plan['dt'] + tg) / plan['dt']).astype(int), 0, plan['n']); ax[0].plot(tg * 1e3, (x[k, fem.top, 1] - x[k, fem.bot, 1]) / 0.067, color=col, label=lab); ax[1].plot(tg * 1e3, np.maximum(x[k, fem.bot, 1], 0) * 1e3, color=col, label=lab)
        ax[0].set_ylabel('height / rest height'); ax[1].set_ylabel('lift of the bottom edge (mm)'); ax[0].set_xlim(0, 150); ax[1].set_xlim(0, 150)
        for a in ax: a.set_xlabel('ms after separation'); a.grid(alpha=.3); a.legend(fontsize=7)
        fig.suptitle(f'{name}: real vs relative-damping FEM, multipliers {mults[0]:g}-{mults[-1]:g}'); plt.tight_layout(); plt.savefig(f'{OUT}/hop_curves{sfx}_{name}.png', dpi=90); plt.close()

if __name__ == '__main__': main(sys.argv[1], [float(a) for a in sys.argv[2:]] or None)
