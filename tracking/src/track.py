"""Track yellow ball top edge, bottom edge, width per frame at full res. Usage: track.py IMG_0536"""
import sys, subprocess, csv
import cv2, numpy as np
from common import TRACK_OUT

W, H, FPS = 1920, 1080, 240
TABLE_Y = 740            # rows >= this are table/reflection (measured from rest-frame gap); same camera for all clips
X0, X1 = 400, 1500       # ignore the yellow-green object at far left

def yellow(img):
    h = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hue = (h[..., 0] > 17) & (h[..., 0] < 40)
    return hue * np.clip((h[..., 1] - 70) / 60, 0, 1)   # soft score in [0,1] -> subpixel edges

def cross(profile, rising):
    """first/last 0.5 crossing of a 1-D soft profile, linearly interpolated"""
    above = profile >= 0.5
    idx = np.flatnonzero(above)
    if len(idx) == 0: return np.nan
    i = idx[0] if rising else idx[-1]
    j = i - 1 if rising else i + 1
    if j < 0 or j >= len(profile): return float(i)
    a, b = profile[j], profile[i]
    return j + (0.5 - a) / (b - a) * (i - j)

def measure(img):
    s = yellow(img)[:TABLE_Y, X0:X1]
    m = (s > 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n < 2: return [np.nan] * 4
    k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    s = s * (lab == k)
    cols = np.flatnonzero((lab == k).any(0))
    cx = (cols[0] + cols[-1]) / 2
    c = slice(int(cx) - 60, int(cx) + 60)            # central columns: robust to hand/tin overlap at the sides
    prof = s[:, c].mean(1)
    top, bot = cross(prof, True), cross(prof, False)
    # width: max row sum of soft mask (px)
    width = float(np.percentile(s.sum(1), 99))
    return [top, bot, width, cx + X0]

def main(name):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', f'videos/{name}.MOV', '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'],
                         stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    vw = cv2.VideoWriter(f'{TRACK_OUT}/debug/{name}_debug.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 30, (960, 540))
    pts = sorted(float(x) for x in subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'packet=pts_time', '-of', 'csv=p=0', f'videos/{name}.MOV'], capture_output=True, text=True).stdout.split())
    rows, f = [], 0
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        img = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        t, b, w, cx = measure(img)
        rows.append([f, f / FPS, pts[f], t, b, w, cx])
        if f % 4 == 0 and not np.isnan(t):          # debug overlay at 60 fps-equivalent subsample
            d = img.copy()
            cv2.line(d, (int(cx) - 250, int(round(t))), (int(cx) + 250, int(round(t))), (0, 0, 255), 3)
            cv2.line(d, (int(cx) - 250, int(round(b))), (int(cx) + 250, int(round(b))), (255, 0, 0), 3)
            cv2.line(d, (0, TABLE_Y), (W, TABLE_Y), (0, 255, 0), 2)
            vw.write(cv2.resize(d, (960, 540)))
        f += 1
    vw.release()
    with open(f'{TRACK_OUT}/{name}.csv', 'w', newline='') as fh:
        wr = csv.writer(fh); wr.writerow(['frame', 't_s', 'pts_s', 'top_px', 'bottom_px', 'width_px', 'cx_px']); wr.writerows(rows)
    print(name, f, 'frames')

if __name__ == '__main__':
    main(sys.argv[1])
