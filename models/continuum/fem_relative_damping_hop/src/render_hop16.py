"""Real clip | FEM side view | FEM oblique, for the relative-damping x16 hop model. Same layout as ../../fem_axisymmetric_warp/src/render_fem.py.
Usage: render_hop16.py CLIP   (repo root, TRACKER=sam2, PYTHONPATH including shared, tracking/src and fem_axisymmetric_warp/src)"""
import sys, json, subprocess
import numpy as np, cv2
from fem_axi import FEM
from fit_fem import simulate_clip
from realclip import real_panels, PX
from render_fem import panel, POST, FPS, SLOW
OUT = 'models/continuum/fem_relative_damping_hop/outputs'; PARAMS = 'models/continuum/fem_axisymmetric_warp/outputs/params_fem.json'
MULT = 16.0       # chosen on the training clips only (hop_scan.py)

def main(name):
    prm = np.array(json.load(open(PARAMS))['prm']); prm[2] *= MULT; fem = FEM()
    cd, plan, x = simulate_clip(fem, name, prm, rel=1.0); dt = plan['dt']; t0 = plan['n_sep'] * dt
    Tr = cd['tin'][0][-1]; tt = np.arange(-(Tr + 0.03), POST, 1 / (FPS * SLOW)); real = real_panels(name, tt); f = f'{OUT}/real_vs_fem_hop16_{name}.mp4'
    out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{3*PX}x{PX+34}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f], stdin=subprocess.PIPE)
    tag = 'TRAINING clip' if name in ('IMG_0536', 'IMG_0537') else 'HELD-OUT clip'
    for t, rp in zip(tt, real):
        k = int(np.clip(round((t0 + t) / dt), 0, plan['n'])); arc = x[k, fem.arc].astype(np.float64); pz = plan['plate'][k]
        side = panel(arc, pz, 0, 0, 'FEM, relative damping x16: side view'); obl = panel(arc, pz, 35, 25, 'FEM: oblique')
        rp = rp.copy(); cv2.putText(rp, f'REAL  {name}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .5, (20, 20, 20), 1, cv2.LINE_AA)
        c = np.full((PX + 34, 3 * PX, 3), 255, np.uint8); c[34:, :PX], c[34:, PX:2 * PX], c[34:, 2 * PX:] = rp, side, obl
        cv2.putText(c, f't = {t*1e3:+6.0f} ms from release   (slowed {SLOW}x; same clock for real and model)   axisymmetric FEM + damping relative to the centre of mass x16 (hop); {tag}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .55, (20, 20, 20), 1, cv2.LINE_AA)
        out.stdin.write(c.tobytes())
    out.stdin.close(); out.wait(); print('wrote', f)

if __name__ == '__main__': main(sys.argv[1])
