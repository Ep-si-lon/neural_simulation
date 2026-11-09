"""Side-by-side demo: real clip (cropped on ball) | shaded-ellipsoid proxy driven by the held-out model prediction.
Height/lift come from the model (fitted on the other three clips); width is the measured width (empirical, see README).
Usage: demo.py IMG_0539   Output: outputs/demo_<clip>.mp4 (H.264, slowed 8x, frame-held to a uniform clock)"""
import sys, subprocess
import cv2, numpy as np
from common import CLIPS, load, W, H
from render2d import shade, CROP
from fit import prep, fit, predict

OUT_FPS, SLOW = 30, 8     # crop rows; slow factor vs. real time
WIN_PRE = 0.03

def main(name):
    cs = {n: prep(n) for n in CLIPS}
    e, tau, tc = fit([cs[n] for n in CLIPS if n != name]); c = cs[name]
    d, hraw = load(name); t_all = d['pts_s']
    rest = c['rest']; pxm = rest / 0.067; ta, a = c['ta'], c['a']
    top = d['top_px']; rest_top = np.median(top[-len(top) // 5:])
    tt = np.arange(-WIN_PRE, 0.20, 1 / (OUT_FPS * SLOW))        # uniform display clock in real seconds
    tt_m = np.clip(tt, 0, None)
    cc = dict(c, t=tt_m)
    pred_y = predict(cc, e, tau, tc)                              # top above rest (px)
    delta = c['h'][0] * np.exp(-tt_m / tau); hm = rest * (1 + delta)
    # bottom lift = top lift - height change
    lift = pred_y - rest * delta
    wmeas = np.interp(ta + tt, t_all, d['width_px'])
    need = sorted({int(np.searchsorted(t_all, ta + x, 'right') - 1) for x in tt})
    frames = {}
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', f'videos/{name}.MOV', '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    i = 0; cxm = int(np.median(d['cx_px'][a - 5:a + 40])); lo, hi = need[0], need[-1]
    while i <= hi:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        if i in need: frames[i] = cv2.resize(np.frombuffer(buf, np.uint8).reshape(H, W, 3)[CROP[0]:CROP[1], cxm - 330:cxm + 330].copy(), (528, 440))
        i += 1
    p.kill()
    out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1056x500', '-r', str(OUT_FPS), '-i', '-',
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f'models/lumped_1d/bounce_recovery/outputs/demo_{name}.mp4'], stdin=subprocess.PIPE)
    s = 440 / (CROP[1] - CROP[0])
    table_y = int((740 - CROP[0]) * s)
    for k, x in enumerate(tt):
        fi = int(np.searchsorted(t_all, ta + x, 'right') - 1)
        left = frames[fi].copy()
        right = np.full((440, 528, 3), 238, np.uint8); cv2.line(right, (0, table_y), (528, table_y), (60, 60, 60), 2)
        ry, rx = hm[k] * s / 2, wmeas[k] * s / 2
        # model bottom = table - lift; rest bottom sits at about the table line minus a small gap (722 vs 740 px in the crop frame)
        bottom = table_y - 18 * s - lift[k] * s
        shade(right, 264, bottom - ry, rx, ry)
        canvas = np.full((500, 1056, 3), 255, np.uint8); canvas[60:500, 0:528] = left; canvas[60:500, 528:] = right
        txt = lambda s_, x_, y_, sz=0.55: cv2.putText(canvas, s_, (x_, y_), cv2.FONT_HERSHEY_SIMPLEX, sz, (20, 20, 20), 1, cv2.LINE_AA)
        txt(f'{name} (held out)  t = {x*1e3:+.0f} ms after first apex  [{SLOW}x slow-mo]', 8, 20)
        txt(f'measured: h={100*(np.interp(ta+x,t_all,hraw)/rest-1):+.1f}% of rest  lift {(rest_top-np.interp(ta+x,t_all,top)-rest*(np.interp(ta+x,t_all,hraw)/rest-1))/pxm*100:.1f} cm', 8, 42, .45)
        txt(f'model: h={100*delta[k]:+.1f}%  lift={lift[k]/pxm*100:.1f} cm   e={e:.2f} tau={tau*1e3:.0f}ms tc={tc*1e3:.0f}ms', 536, 42, .45)
        txt('REAL', 8, 78, .5); txt('MODEL (ellipsoid proxy, measured width)', 536, 78, .5)
        out.stdin.write(canvas.tobytes())
    out.stdin.close(); out.wait(); print('wrote', f'models/lumped_1d/bounce_recovery/outputs/demo_{name}.mp4')

if __name__ == '__main__':
    main(sys.argv[1])
