"""Real clip | axisymmetric FEM ball (revolved into a smooth 3D surface), side view | oblique view, on one clock (t = 0 at release, slowed 8x).
Usage: render_fem.py CLIP   (uses outputs/params_fem.json)  ->  outputs/real_vs_fem_<CLIP>.mp4"""
import sys, json, subprocess
import numpy as np, cv2
from fem_axi import FEM, R
from fit_fem import simulate_clip, OUT
from realclip import real_panels, PX
from render3d import project, S

SLOW, FPS, PRE, POST = 8, 30, 0.06, 0.25
NAZ = 72

def panel(arc, plate_z, az, el, label):
    img = np.full((PX, PX, 3), 238, np.uint8); sx = lambda x: x * S + PX / 2; sy = lambda y: PX - 90 - y * S
    th = np.linspace(0, 2 * np.pi, 48); tab = np.stack([0.12 * np.cos(th), np.zeros_like(th), 0.12 * np.sin(th)], 1); tx, ty, _ = project(tab, az, el)
    cv2.fillPoly(img, [np.stack([sx(tx), sy(ty)], 1).astype(np.int32)], (170, 175, 180))
    r, z = arc[:, 0], arc[:, 1]; ph = np.linspace(0, 2 * np.pi, NAZ, endpoint=False)
    dr, dz = np.gradient(r), np.gradient(z); nr, nz = dz, -dr; nn = np.hypot(nr, nz) + 1e-12; nr, nz = nr / nn, nz / nn       # outward profile normal
    V = np.stack([np.outer(r, np.cos(ph)), np.outer(z, np.ones_like(ph)), np.outer(r, np.sin(ph))], -1)                        # (arc, az, 3)
    Nv = np.stack([np.outer(nr, np.cos(ph)), np.outer(nz, np.ones_like(ph)), np.outer(nr, np.sin(ph))], -1)
    X, Y, Zd = project(V, az, el); nx, ny, nzz = project(Nv, az, el); a, b = len(r), NAZ
    quads = []
    for i in range(a - 1):
        for j in range(b):
            j2 = (j + 1) % b; idx = [(i, j), (i + 1, j), (i + 1, j2), (i, j2)]
            nzq = np.mean([nzz[q] for q in idx])
            if nzq <= -0.05: continue
            quads.append((np.mean([Zd[q] for q in idx]), idx, np.array([np.mean([nx[q] for q in idx]), np.mean([ny[q] for q in idx]), nzq])))
    quads.sort(key=lambda q: q[0]); L = np.array([-0.4, 0.7, 0.6]); L /= np.linalg.norm(L)
    for _, idx, n in quads:
        k = 0.3 + 0.7 * max(0.0, float(n @ L) / (np.linalg.norm(n) + 1e-9)); col = tuple(int(v * k) for v in (40, 215, 250))
        pts = np.array([[sx(X[q]), sy(Y[q])] for q in idx], np.int32); cv2.fillConvexPoly(img, pts, col)
    if plate_z < 1.0:
        for yy, c in ((plate_z, (120, 120, 125)), (plate_z + 0.008, (190, 190, 195))):
            p = np.stack([0.05 * np.cos(th), np.full_like(th, yy), 0.05 * np.sin(th)], 1); px, py, _ = project(p, az, el)
            cv2.fillPoly(img, [np.stack([sx(px), sy(py)], 1).astype(np.int32)], c)
    cv2.putText(img, label, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .5, (20, 20, 20), 1, cv2.LINE_AA); return img

def main(name):
    P = json.load(open(f'{OUT}/params_fem.json')); fem = FEM()
    cd, plan, x = simulate_clip(fem, name, np.array(P['prm'])); dt = plan['dt']; t0 = plan['n_sep'] * dt
    Tr = cd['tin'][0][-1]; tt = np.arange(-(Tr + 0.03), POST, 1 / (FPS * SLOW)); real = real_panels(name, tt)      # window starts just before the tin begins to retreat
    out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{3*PX}x{PX+34}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                            f'{OUT}/real_vs_fem_{name}.mp4'], stdin=subprocess.PIPE)
    tag = 'TRAINING clip' if name in ('IMG_0536', 'IMG_0537') else 'HELD-OUT clip'
    for t, rp in zip(tt, real):
        k = int(np.clip(round((t0 + t) / dt), 0, plan['n'])); arc = x[k, fem.arc].astype(np.float64); pz = plan['plate'][k]
        side = panel(arc, pz, 0, 0, 'FEM (axisymmetric, Warp): side view'); obl = panel(arc, pz, 35, 25, 'FEM: oblique')
        rp = rp.copy(); cv2.putText(rp, f'REAL  {name}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .5, (20, 20, 20), 1, cv2.LINE_AA)
        c = np.full((PX + 34, 3 * PX, 3), 255, np.uint8); c[34:, :PX], c[34:, PX:2 * PX], c[34:, 2 * PX:] = rp, side, obl
        cv2.putText(c, f't = {t*1e3:+6.0f} ms from release   (slowed {SLOW}x; same clock for real and model)   axisymmetric FEM, fitted on 0536+0537; {tag}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .55, (20, 20, 20), 1, cv2.LINE_AA)
        out.stdin.write(c.tobytes())
    out.stdin.close(); out.wait(); print('wrote', f'{OUT}/real_vs_fem_{name}.mp4')

if __name__ == '__main__': main(sys.argv[1])
