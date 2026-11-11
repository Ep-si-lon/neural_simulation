"""Real-clip panels for the real-vs-model videos: crop of the original 1080p frame around the ball at the model panels' scale (500 x 500 px; table on panel row 410),
picked at true file timestamps (the newest frame at or before t, t = 0 at release)."""
import subprocess
import numpy as np, cv2
from clip_prep import prep
from common import W, H, TRACK_OUT

PX, SC = 500, 1.025       # panel size, real-pixel -> panel-pixel scale (6.7 cm ball ~ 402 px, as in shared/render3d.py)

def real_panels(name, times, sc=SC, table_row=410):
    """times: seconds relative to release. Returns a list of BGR panels (PX x PX), one per time."""
    c = prep(name); t_all, i0 = c['full_t'], c['i_rel']; t_rel = t_all[i0]
    d = np.genfromtxt(f'{TRACK_OUT}/{name}.csv', delimiter=',', names=True); cx = int(np.median(d['cx_px'][i0 - 5:i0 + 40]))
    idx = [int(np.searchsorted(t_all, t_rel + x, 'right') - 1) for x in times]; need = sorted(set(idx)); frames = {}
    ww = int(PX / sc); y0, x0 = int(740 - table_row / sc), int(cx - PX / 2 / sc)       # table (pixel row 740) lands on panel row table_row
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', f'videos/{name}.MOV', '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    i = 0
    while i <= need[-1]:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        if i in need:
            fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3); crop = np.full((ww, ww, 3), 238, np.uint8); ya, yb, xa, xb = max(y0, 0), min(y0 + ww, H), max(x0, 0), min(x0 + ww, W)
            crop[ya - y0:yb - y0, xa - x0:xb - x0] = fr[ya:yb, xa:xb]; frames[i] = cv2.resize(crop, (PX, PX))
        i += 1
    p.kill()
    return [frames[i].copy() for i in idx]
