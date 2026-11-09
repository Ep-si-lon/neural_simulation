"""Real clip | 3D foam model, side view | 3D foam model, oblique view, on ONE clock (t = 0 at release, ms), slowed 8x for viewing.
The model is the with-lift fit (trained on 0536+0537); it is started from the clip's own measured pressed height and released at t = 0.
Real frames are shown at their true file timestamps (the newest frame at or before t). Run from repo root:
PYTHONPATH=src:sim3d python demo_for_team/side_by_side.py IMG_0536"""
import sys, json, subprocess
import numpy as np, cv2
from sim import prep
from ball3d import Ball
from render import draw, PX
from fit3d import DT, SUB
from track import W, H

SLOW, FPS, PRE, POST, SC = 8, 30, 0.06, 0.25, 1.025       # slow-mo factor, output fps, window around release (s), real->panel px scale

def main(name, params='recovery_time_lift/params_3d_lift.json'):
    c = prep(name); t_all, i0 = c['full_t'], c['i_rel']; t_rel = t_all[i0]
    tt = np.arange(-PRE, POST, 1 / (FPS * SLOW))
    d = np.genfromtxt(f'data/{name}.csv', delimiter=',', names=True); cx = int(np.median(d['cx_px'][i0 - 5:i0 + 40]))
    need = sorted({int(np.searchsorted(t_all, t_rel + x, 'right') - 1) for x in tt}); frames, i = {}, 0
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', f'videos/{name}.MOV', '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    y0, x0 = int(740 - 410 / SC), int(cx - 250 / SC)           # table (row 740) lands on panel row 410, as in the 3D panels
    while i <= need[-1]:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        if i in need: frames[i] = cv2.resize(np.frombuffer(buf, np.uint8).reshape(H, W, 3)[y0:y0 + int(500 / SC), x0:x0 + int(500 / SC)], (PX, PX))
        i += 1
    p.kill()
    ks, kb, kr, cd = json.load(open(params))['ks_kb_kr_cd']
    b = Ball(sub=SUB, ks=ks, kb=kb, kr=kr, cd=cd); b.cx = b.cz = 0.0; b.run(0.08, DT, damp=80); rest = b.shape()[0]
    for k in range(60): b.tool = ('plate', rest - rest * (1 - c['hc'] / c['rest']) * (k + 1) / 60, 0); b.run(0.0015, DT, damp=80)
    hold = rest * c['hc'] / c['rest']; b.tool = ('plate', hold, 0)
    out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{3*PX}x{PX+34}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f'demo_for_team/real_vs_3d_{name}.mp4'], stdin=subprocess.PIPE)
    prev = tt[0]
    for x in tt:
        dt = x - prev; prev = x
        if x >= 0: b.tool = None
        b.run(dt, DT, damp=80 if x < 0 else 0.0)
        real = frames[int(np.searchsorted(t_all, t_rel + x, 'right') - 1)].copy(); cv2.putText(real, f'REAL  {name}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .5, (20, 20, 20), 1, cv2.LINE_AA)
        side = draw(b, b.tool, 0, 0, '3D model: side view'); obl = draw(b, b.tool, 35, 25, '3D model: oblique')
        cv = np.full((PX + 34, 3 * PX, 3), 255, np.uint8); cv[34:, :PX], cv[34:, PX:2 * PX], cv[34:, 2 * PX:] = real, side, obl
        cv2.putText(cv, f't = {x*1e3:+6.0f} ms from release   (slowed {SLOW}x; same clock for real and model)   model trained on 0536+0537, with-lift fit', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .55, (20, 20, 20), 1, cv2.LINE_AA)
        out.stdin.write(cv.tobytes())
    out.stdin.close(); out.wait(); print('wrote', f'demo_for_team/real_vs_3d_{name}.mp4')

if __name__ == '__main__': main(sys.argv[1])
