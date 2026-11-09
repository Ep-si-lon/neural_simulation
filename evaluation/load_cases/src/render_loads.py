"""Render the fitted 3D shell: flat-plate press+release (the fitted scenario) and a point press (a PREDICTION, not validated).
Side view | oblique view, slowed down. Run: evaluation/load_cases/run.sh   (modes: flat, point, side, deep)"""
import sys, json, subprocess
import numpy as np, cv2
from ball3d import Ball, DT, SUB

from render3d import draw, PX

TITLES = {'deep': 'FLAT PLATE on top, DEEP press to 75% compression, release (prediction, not validated)', 'flat': 'FLAT PLATE on top, press + release (fitted scenario)', 'point': 'POINT FORCE on top, press + release (prediction, not validated)', 'side': 'TWO FLAT PLATES from the sides, squeeze + release (prediction, not validated)'}

def main(mode, params='models/mesh_3d/foam_core_no_lift/outputs/params_3d.json', out_path=None):
    ks, kb, kr, cd = json.load(open(params))['ks_kb_kr_cd']   # latest fit (recovery_time study)
    b = Ball(sub=SUB, ks=ks, kb=kb, kr=kr, cd=cd); b.cx = b.cz = 0.0; b.run(0.08, DT, damp=80); rest = b.shape()[0]
    out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{2*PX}x{PX+30}', '-r', '30', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', out_path or f'evaluation/load_cases/outputs/no_lift/latest_{mode}.mp4'], stdin=subprocess.PIPE)
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
        if mode in ('flat', 'deep'): b.tool = ('plate', rest - rest * (0.75 if mode == 'deep' else 0.38) * a_, 0)
        elif mode == 'point': b.tool = ('probe', rest - rest * 0.50 * a_, 0.006)
        else: b.tool = ('side', w0 - w0 * 0.40 * a_, 0)
        b.run(0.0015, DT, damp=80); t[0] += 1.5e-3; frame('pressing')
    for _ in range(10): frame('hold')
    b.tool = None
    for i in range(160): b.run(0.0015, DT); t[0] += 1.5e-3; frame('released')
    out.stdin.close(); out.wait(); print('wrote', out_path or f'evaluation/load_cases/outputs/no_lift/latest_{mode}.mp4')

if __name__ == '__main__': main(*(sys.argv[1:4] if len(sys.argv) > 1 else ['flat']))
