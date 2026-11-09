"""Render the fitted 3D shell: flat-plate press+release (the fitted scenario) and a point press (a PREDICTION, not validated).
Side view | oblique view, slowed down. Run: PYTHONPATH=src:sim3d python sim3d/render.py [flat|point]  -> sim3d/demo_<mode>.mp4"""
import sys, json, subprocess
import numpy as np, cv2
from ball3d import Ball
from fit3d import DT, SUB

S, PX = 6000.0, 500                       # px per metre, panel size
def project(x, az, el):
    a, e = np.radians(az), np.radians(el)
    x1 = x[..., 0] * np.cos(a) + x[..., 2] * np.sin(a); z1 = -x[..., 0] * np.sin(a) + x[..., 2] * np.cos(a)
    return x1, x[..., 1] * np.cos(e) - z1 * np.sin(e), x[..., 1] * np.sin(e) + z1 * np.cos(e)

def draw(ball, tool, az, el, label):
    img = np.full((PX, PX, 3), 238, np.uint8)
    X, Y, Z = project(ball.x, az, el); sx = lambda x: x * S + PX / 2; sy = lambda y: PX - 90 - y * S
    # table: a flat disc at y=0
    th = np.linspace(0, 2 * np.pi, 48); tab = np.stack([0.12 * np.cos(th), np.zeros_like(th), 0.12 * np.sin(th)], 1); tx, ty, _ = project(tab, az, el)
    cv2.fillPoly(img, [np.stack([sx(tx), sy(ty)], 1).astype(np.int32)], (170, 175, 180))
    def disc(y, r, col, cx=0.0, cz=0.0):
        p = np.stack([cx + r * np.cos(th), np.full_like(th, y), cz + r * np.sin(th)], 1); px, py, _ = project(p, az, el)
        cv2.fillPoly(img, [np.stack([sx(px), sy(py)], 1).astype(np.int32)], col)
    near = far = None
    if tool is not None and tool[0] == 'side':
        def slab(xp, col):
            q = np.array([[xp, 0, -0.05], [xp, 0.09, -0.05], [xp, 0.09, 0.05], [xp, 0, 0.05]]); px, py, _ = project(q, az, el)
            cv2.fillPoly(img, [np.stack([sx(px), sy(py)], 1).astype(np.int32)], col)
        xs = [-tool[1] / 2 - 0.004, tool[1] / 2 + 0.004]; zc = [project(np.array([[xp, 0.04, 0.0]]), az, el)[2][0] for xp in xs]
        far, near = (xs[0], xs[1]) if zc[0] <= zc[1] else (xs[1], xs[0]); slab(far, (150, 150, 155))
    f = ball.f; a, b, c = (ball.x[f[:, i]] for i in range(3)); n = np.cross(b - a, c - a); n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    nx, ny, nz = project(n, az, el); order = np.argsort(Z[f].mean(1))
    L = np.array([-0.4, 0.7, 0.6]); L /= np.linalg.norm(L)
    for t in order:
        if nz[t] <= 0: continue
        k = 0.3 + 0.7 * max(0.0, nx[t] * L[0] + ny[t] * L[1] + nz[t] * L[2]); col = tuple(int(v * k) for v in (40, 215, 250))
        pts = np.stack([sx(X[f[t]]), sy(Y[f[t]])], 1).astype(np.int32); cv2.fillConvexPoly(img, pts, col); cv2.polylines(img, [pts], True, tuple(int(v * .7) for v in col), 1, cv2.LINE_AA)
    if tool is not None:
        kind, y, r = tool
        if kind == 'side': slab(near, (120, 120, 125))
        elif kind == 'plate': disc(y, 0.05, (120, 120, 125)); disc(y + 0.008, 0.05, (190, 190, 195))
        else:
            cx, cy, cz = ball.cx, y + r, ball.cz; p = np.array([[cx, cy, cz], [cx, cy + 0.08, cz]]); px_, py_, _ = project(p, az, el)
            cv2.line(img, (int(sx(px_[0])), int(sy(py_[0]))), (int(sx(px_[1])), int(sy(py_[1]))), (90, 90, 95), 6, cv2.LINE_AA)
            cv2.circle(img, (int(sx(px_[0])), int(sy(py_[0]))), max(int(r * S), 3), (60, 60, 200), -1, cv2.LINE_AA)
    cv2.putText(img, label, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .5, (20, 20, 20), 1, cv2.LINE_AA); return img

TITLES = {'flat': 'FLAT PLATE on top, press + release (fitted scenario)', 'point': 'POINT FORCE on top, press + release (prediction, not validated)', 'side': 'TWO FLAT PLATES from the sides, squeeze + release (prediction, not validated)'}

def main(mode):
    ks, kb, kr, cd = json.load(open('recovery_time/params_3d.json'))['ks_kb_kr_cd']   # latest fit (recovery_time study)
    b = Ball(sub=SUB, ks=ks, kb=kb, kr=kr, cd=cd); b.cx = b.cz = 0.0; b.run(0.08, DT, damp=80); rest = b.shape()[0]
    out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{2*PX}x{PX+30}', '-r', '30', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', f'sim3d/latest_{mode}.mp4'], stdin=subprocess.PIPE)
    t = [0.0]
    def frame(phase):
        h = b.shape()[0] / rest; side = draw(b, b.tool, 0, 0, f'side view: {phase}'); obl = draw(b, b.tool, 35, 25, f'oblique 3D: height {100*h:.0f}% of rest')
        c = np.full((PX + 30, 2 * PX, 3), 255, np.uint8); c[30:, :PX] = side; c[30:, PX:] = obl
        cv2.putText(c, f'{TITLES[mode]}   t={t[0]*1e3:.0f} ms', (8, 20), cv2.FONT_HERSHEY_SIMPLEX, .55, (20, 20, 20), 1, cv2.LINE_AA)
        out.stdin.write(c.tobytes())
    for _ in range(8): frame('rest')
    N = 60; w0 = b.shape()[1]
    for i in range(N):
        a_ = (i + 1) / N
        if mode == 'flat': b.tool = ('plate', rest - rest * 0.38 * a_, 0)
        elif mode == 'point': b.tool = ('probe', rest - rest * 0.50 * a_, 0.006)
        else: b.tool = ('side', w0 - w0 * 0.40 * a_, 0)
        b.run(0.0015, DT, damp=80); t[0] += 1.5e-3; frame('pressing')
    for _ in range(10): frame('hold')
    b.tool = None
    for i in range(160): b.run(0.0015, DT); t[0] += 1.5e-3; frame('released')
    out.stdin.close(); out.wait(); print('wrote', f'sim3d/latest_{mode}.mp4')

if __name__ == '__main__': main(sys.argv[1] if len(sys.argv) > 1 else 'flat')
