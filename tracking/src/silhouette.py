"""Per-frame ball silhouette: left/right extent at 48 levels from top to bottom (interior holes from the smiley/seam filled).
Saves tracking/outputs/<clip>_sil.npz with frame, pts_s, top, bottom, left[48], right[48], cx. Usage: silhouette.py IMG_0536"""
import sys, subprocess
import cv2, numpy as np
from common import TRACK_OUT
from track import yellow, W, H, TABLE_Y, X0, X1

NL = 48

def silhouette(img):
    m = (yellow(img)[:TABLE_Y, X0:X1] > 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n < 2: return None
    m = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    ff = m.copy(); cv2.floodFill(ff, np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8), (0, 0), 2)
    m = (ff != 2).astype(np.uint8)                       # holes (dark smiley line, white seam) filled
    rows = np.flatnonzero(m.any(1)); top, bot = rows[0], rows[-1]
    ys = np.linspace(top + 1, bot - 1, NL).round().astype(int)
    left = np.array([np.flatnonzero(m[y])[0] for y in ys], float) + X0; right = np.array([np.flatnonzero(m[y])[-1] for y in ys], float) + X0
    return top, bot, left, right

def main(name):
    pts = sorted(float(x) for x in subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'packet=pts_time', '-of', 'csv=p=0', f'videos/{name}.MOV'], capture_output=True, text=True).stdout.split())
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', f'videos/{name}.MOV', '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    T, B, L, R, f = [], [], [], [], 0
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        s = silhouette(np.frombuffer(buf, np.uint8).reshape(H, W, 3))
        t, b, l, r = s if s else (np.nan, np.nan, np.full(NL, np.nan), np.full(NL, np.nan))
        T.append(t); B.append(b); L.append(l); R.append(r); f += 1
    np.savez(f'{TRACK_OUT}/{name}_sil.npz', frame=np.arange(f), pts_s=np.array(pts[:f]), top=np.array(T, float), bottom=np.array(B, float), left=np.array(L), right=np.array(R))
    print(name, f, 'frames')

if __name__ == '__main__': main(sys.argv[1])
