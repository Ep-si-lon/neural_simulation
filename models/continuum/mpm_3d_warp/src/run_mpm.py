"""3D MPM (Warp) with the material fitted by the axisymmetric FEM (same E, nu, damping, friction; nothing refitted):
 eval  : flat press to each clip's measured compressed height, release; compare height(t) and the pressed width with the real clips; real-vs-MPM videos.
 loads : the same material pressed by a point probe, by two side plates, and by the flat plate (predictions; no video of these loads exists to test against).
Usage: run_mpm.py eval | loads | all"""
import sys, json, subprocess
import numpy as np, cv2
import warp as wp
import mpm3d as M
from common import CLIPS
from clip_prep import prep, baselines
from realclip import real_panels, PX
from render3d import project, S

FEM_JSON = 'models/continuum/fem_axisymmetric_warp/outputs/params_fem.json'
OUT = 'models/continuum/mpm_3d_warp/outputs'
SLOW, FPS = 8, 30

def material():
    P = json.load(open(FEM_JSON))['params']; return P['E'], P['nu'], P['alpha'], P['mu_plate'], P['mu_table']

def panel(xs, tool, az, el, label):
    img = np.full((PX, PX, 3), 238, np.uint8); sx = lambda x: x * S + PX / 2; sy = lambda y: PX - 90 - y * S
    th = np.linspace(0, 2 * np.pi, 48); tab = np.stack([0.12 * np.cos(th), np.zeros_like(th), 0.12 * np.sin(th)], 1); tx, ty, _ = project(tab, az, el)
    cv2.fillPoly(img, [np.stack([sx(tx), sy(ty)], 1).astype(np.int32)], (170, 175, 180))
    load, pos, pr, yt = tool
    def slab(xp, col):
        q = np.array([[xp, 0, -0.05], [xp, 0.09, -0.05], [xp, 0.09, 0.05], [xp, 0, 0.05]]); px, py, _ = project(q, az, el); cv2.fillPoly(img, [np.stack([sx(px), sy(py)], 1).astype(np.int32)], col)
    near = None
    if load == 'side' and pos < 1.0:
        xs_ = [-pos / 2 - 0.004, pos / 2 + 0.004]; zc = [project(np.array([[xp, 0.04, 0.0]]), az, el)[2][0] for xp in xs_]
        far, near = (xs_[0], xs_[1]) if zc[0] <= zc[1] else (xs_[1], xs_[0]); slab(far, (150, 150, 155))
    P = xs - np.array([M.CX, yt, M.CZ], np.float32); X, Y, Zd = project(P, az, el)
    px = (X * S + PX / 2).round().astype(int); py = (PX - 90 - Y * S).round().astype(int); rad = 3
    offs = [(dx, dy) for dx in range(-rad, rad + 1) for dy in range(-rad, rad + 1) if dx * dx + dy * dy <= rad * rad + 1]
    I = np.concatenate([np.clip(py + dy, 0, PX - 1) * PX + np.clip(px + dx, 0, PX - 1) for dx, dy in offs]); D = np.tile(Zd, len(offs))
    o = np.lexsort((D, I)); I, D = I[o], D[o]; last = np.r_[I[1:] != I[:-1], True]; I, D = I[last], D[last]          # depth buffer: nearest particle per pixel
    zb = np.full(PX * PX, np.nan, np.float32); zb[I] = D * S; zb = zb.reshape(PX, PX); mask = ~np.isnan(zb)
    zf = np.where(mask, zb, np.nanmean(zb)); zf = cv2.GaussianBlur(zf, (0, 0), 2.0)
    gx = np.gradient(zf, axis=1); gy = np.gradient(zf, axis=0); n3 = np.stack([-gx, gy, np.ones_like(gx)], -1); n3 /= np.linalg.norm(n3, axis=-1, keepdims=True)
    Ld = np.array([-0.4, 0.7, 0.6]); Ld /= np.linalg.norm(Ld); k = 0.3 + 0.7 * np.clip(n3 @ Ld, 0, 1)
    img[mask] = (np.array([40, 215, 250])[None] * k[mask][:, None]).astype(np.uint8)
    if load == 'flat' and pos < 1.0:
        for yy, c in ((pos, (120, 120, 125)), (pos + 0.008, (190, 190, 195))):
            p = np.stack([0.05 * np.cos(th), np.full_like(th, yy), 0.05 * np.sin(th)], 1); a, b, _ = project(p, az, el); cv2.fillPoly(img, [np.stack([sx(a), sy(b)], 1).astype(np.int32)], c)
    if load == 'point' and pos < 1.0:
        q = np.array([[0, pos + pr, 0], [0, pos + pr + 0.08, 0]]); a, b, _ = project(q, az, el)
        cv2.line(img, (int(sx(a[0])), int(sy(b[0]))), (int(sx(a[1])), int(sy(b[1]))), (90, 90, 95), 6, cv2.LINE_AA); cv2.circle(img, (int(sx(a[0])), int(sy(b[0]))), max(int(pr * S), 3), (60, 60, 200), -1, cv2.LINE_AA)
    if near is not None: slab(near, (120, 120, 125))
    cv2.putText(img, label, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .5, (20, 20, 20), 1, cv2.LINE_AA); return img

def write_video(path, frames_fn, n, size):
    out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{size[0]}x{size[1]}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path], stdin=subprocess.PIPE)
    for i in range(n): out.stdin.write(frames_fn(i).tobytes())
    out.stdin.close(); out.wait(); print('wrote', path)

def recovery(t, h, rest, thr=0.95):
    i = np.flatnonzero(h >= thr * rest); return float(t[i[0]]) * 1e3 if len(i) else float('nan')

def run_eval(log):
    E, nu, al, mp, mt = material(); cs = {n: prep(n) for n in CLIPS}; train = CLIPS[:2]; rows = []
    log(f'MPM material from the FEM fit: E {E:.0f} Pa, nu {nu:.3f}, alpha {al:.0f} 1/s, friction plate {mp:.2f} table {mt:.2f}, density {M.RHO} kg/m3 (estimate)')
    for n in CLIPS:
        c = cs[n]; pxm = c['rest'] / 0.067; out = M.simulate(E, nu, al, mp, mt, 'flat', depth=c['hc'] / pxm, rec_dt=1 / 240)
        t = np.array(out['t']); h = np.array(out['height']) * pxm; w = np.array(out['width'])
        hs = np.interp(c['t'], t, h); h_rmse = 100 * np.sqrt(np.mean((hs - c['h']) ** 2)) / c['rest']
        he, hr = baselines(train, cs, c); e_rmse = 100 * np.sqrt(np.mean((he - c['h']) ** 2)) / c['rest']
        i_h = np.flatnonzero(t < 0)[-1]; wm = c['width']; w_real = np.median(wm[c['i_rel'] - 30:c['i_rel'] - 5]) / np.median(wm[-len(wm) // 5:]); w_sim = w[i_h] / w[0]
        rows.append(dict(clip=n, set='train' if n in train else 'TEST', height_rmse=h_rmse, exp_baseline=e_rmse, t95_model=recovery(t[t >= 0], h[t >= 0], c['rest']) if False else recovery(t[t >= 0] - t[t >= 0][0], h[t >= 0], c['rest']),
                         t95_real=recovery(c['t'], np.maximum.accumulate(c['h']), c['rest']), pressed_width_sim=w_sim, pressed_width_real=w_real, particles=out['n_particles']))
        r = rows[-1]; log(f"  {n} ({r['set']}): height RMSE {h_rmse:.1f}% (exp baseline {e_rmse:.1f}%)  t95 MPM {r['t95_model']:.0f} ms vs real {r['t95_real']:.0f} ms  pressed width MPM {w_sim:.3f}x vs real {w_real:.3f}x  [{out['n_particles']} particles]")
        if n in ('IMG_0536', 'IMG_0538', 'IMG_0539'):
            tt = np.arange(-0.06, 0.25, 1 / (FPS * SLOW)); real = real_panels(n, tt); tagc = 'TRAINING clip (FEM fit)' if n in train else 'HELD-OUT clip'
            def fr(i, out=out, tt=tt, real=real, n=n, tagc=tagc):
                k = int(np.argmin(np.abs(np.array(out['t']) - tt[i]))); rp = real[i].copy(); cv2.putText(rp, f'REAL  {n}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .5, (20, 20, 20), 1, cv2.LINE_AA)
                c_ = np.full((PX + 34, 3 * PX, 3), 255, np.uint8); c_[34:, :PX] = rp; c_[34:, PX:2 * PX] = panel(out['snaps'][k], out['tool'][k], 0, 0, 'MPM (3D, Warp): side view'); c_[34:, 2 * PX:] = panel(out['snaps'][k], out['tool'][k], 35, 25, 'MPM: oblique')
                cv2.putText(c_, f't = {tt[i]*1e3:+6.0f} ms from release   (slowed {SLOW}x)   3D MPM with the FEM-fitted material, nothing refitted; {tagc}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .55, (20, 20, 20), 1, cv2.LINE_AA); return c_
            write_video(f'{OUT}/real_vs_mpm_{n}.mp4', fr, len(tt), (3 * PX, PX + 34))
    return rows

def run_loads(log):
    E, nu, al, mp, mt = material(); rest = 0.067
    specs = {'flat': ('flat press to 40 % of the height (60 % compression)', 0.40 * rest), 'point': ('point probe (6 mm) pressed 45 % of the height', 0.55 * rest), 'side': ('two flat plates squeezing the width by 40 %', 0.60 * rest)}
    for load, (desc, depth) in specs.items():
        out = M.simulate(E, nu, al, mp, mt, load, depth=depth, rec_dt=1 / 240); log(f'  load {load}: {desc}; min height {min(out["height"])*1e3:.1f} mm, max width {max(out["width"])*1e3:.1f} mm')
        def fr(i, out=out, load=load, desc=desc):
            c_ = np.full((PX + 34, 2 * PX, 3), 255, np.uint8); c_[34:, :PX] = panel(out['snaps'][i], out['tool'][i], 0, 0, 'MPM: side view'); c_[34:, PX:] = panel(out['snaps'][i], out['tool'][i], 35, 25, 'MPM: oblique')
            cv2.putText(c_, f'{desc} (prediction, not validated)   t = {out["t"][i]*1e3:+.0f} ms from release (slowed {SLOW}x)', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .5, (20, 20, 20), 1, cv2.LINE_AA); return c_
        write_video(f'{OUT}/mpm_load_{load}.mp4', fr, len(out['t']), (2 * PX, PX + 34))

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'all'; lines = []
    def log(s): print(s, flush=True); lines.append(s)
    rows = []
    if mode in ('eval', 'all'): rows = run_eval(log)
    if mode in ('loads', 'all'): run_loads(log)
    if rows:
        json.dump(rows, open(f'{OUT}/results_mpm.json', 'w'), indent=1); open(f'{OUT}/results.txt', 'w').write('\n'.join(lines) + '\n')
