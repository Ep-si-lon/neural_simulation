"""Real clip | 3D model, side view | 3D model, oblique view, on ONE clock (t = 0 at release, ms), slowed 8x for viewing.
Works for any 3D model: pass its parameter file (foam core: ks, kb, kr, cd; the gas shell's file has p0 instead of kr).
The model is started from the clip's own measured pressed height; the plate then retreats along the measured tin trajectory and the ball is free from t = 0, the separation frame (fitted on 0536+0537).
Real frames are shown at their true file timestamps (the newest frame at or before t).
Usage: real_vs_3d.py CLIP PARAMS_JSON OUT_MP4 LABEL     (each 3D model's render.sh calls it)"""
import sys, json, subprocess
import numpy as np, cv2
from clip_prep import prep
from ball3d import Ball, DT, SUB
from render3d import draw, PX
from common import W, H, TRACK_OUT

SLOW, FPS, PRE, POST, SC = 8, 30, 0.06, 0.25, 1.025       # slow-mo factor, output fps, window around release (s), real->panel px scale

def main(name, params, out_path, label):
    c = prep(name); t_all, i0 = c['full_t'], c['i_rel']; t_rel = t_all[i0]
    Tr = c['tin'][0][-1]; tt = np.arange(-(Tr + 0.03), POST, 1 / (FPS * SLOW))          # the tin's retreat (measured) precedes the separation at t = 0
    d = np.genfromtxt(f'{TRACK_OUT}/{name}.csv', delimiter=',', names=True); cx = int(np.median(d['cx_px'][i0 - 5:i0 + 40]))
    need = sorted({int(np.searchsorted(t_all, t_rel + x, 'right') - 1) for x in tt}); frames, i = {}, 0
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', f'videos/{name}.MOV', '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    y0, x0 = int(740 - 410 / SC), int(cx - 250 / SC)           # table (row 740) lands on panel row 410, as in the 3D panels
    while i <= need[-1]:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        if i in need: frames[i] = cv2.resize(np.frombuffer(buf, np.uint8).reshape(H, W, 3)[y0:y0 + int(500 / SC), x0:x0 + int(500 / SC)], (PX, PX))
        i += 1
    p.kill()
    J = json.load(open(params)); ks, kb, third, cd = J['ks_kb_kr_cd'] if 'ks_kb_kr_cd' in J else J['split']
    b = Ball(sub=SUB, ks=ks, kb=kb, **({'p0': third} if 'gas' in params else {'kr': third}), cd=cd); b.cx = b.cz = 0.0; b.run(0.08, DT, damp=80); rest = b.shape()[0]
    for k in range(60): b.tool = ('plate', rest - rest * (1 - c['hc'] / c['rest']) * (k + 1) / 60, 0); b.run(0.0015, DT, damp=80)
    hold = rest * c['hc'] / c['rest']; b.tool = ('plate', hold, 0)
    out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{3*PX}x{PX+34}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out_path], stdin=subprocess.PIPE)
    prev = tt[0]
    for x in tt:
        dt = x - prev; prev = x
        if x >= 0: b.tool = None
        elif x >= -Tr: b.tool = ('plate', float(np.interp(x + Tr, c['tin'][0], c['tin'][1])) * rest / 0.067, 0)     # plate follows the measured tin trajectory
        b.run(dt, DT, damp=80 if x < -Tr else 0.0)
        real = frames[int(np.searchsorted(t_all, t_rel + x, 'right') - 1)].copy(); cv2.putText(real, f'REAL  {name}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .5, (20, 20, 20), 1, cv2.LINE_AA)
        side = draw(b, b.tool, 0, 0, '3D model: side view'); obl = draw(b, b.tool, 35, 25, '3D model: oblique')
        cv = np.full((PX + 34, 3 * PX, 3), 255, np.uint8); cv[34:, :PX], cv[34:, PX:2 * PX], cv[34:, 2 * PX:] = real, side, obl
        cv2.putText(cv, f't = {x*1e3:+6.0f} ms from release   (slowed {SLOW}x; same clock for real and model)   {label}; model fitted on 0536+0537; {"TRAINING clip" if name in ("IMG_0536", "IMG_0537") else "HELD-OUT clip"}', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .55, (20, 20, 20), 1, cv2.LINE_AA)
        out.stdin.write(cv.tobytes())
    out.stdin.close(); out.wait(); print('wrote', out_path)

if __name__ == '__main__': main(*sys.argv[1:5])
