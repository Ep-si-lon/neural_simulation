"""Squeeze + release demo: real clip | simulated two-mass ball (params fitted on the other three clips, see out/sim_params.json).
Before release the top follows the tin (measured height = input). After release the ball is simulated from rest in the compressed state.
Width = empirical law w = w_rest*(h/h_rest)^-a fitted on the other three clips. Usage: demo_sim.py IMG_0538"""
import sys, json, subprocess
import cv2, numpy as np
from common import CLIPS, W, H, TRACK_OUT
from clip_prep import prep
from sim import simulate
from render2d import shade, CROP

OUT_FPS, SLOW, PRE = 30, 8, 0.25

def main(name):
    cs = {n: prep(n) for n in CLIPS}; c = cs[name]
    p = np.log(json.load(open('models/lumped_1d/two_mass_spring/outputs/sim_params.json'))[name])
    # width law from the other clips: log(w/w_rest) = -a * log(h/h_rest), over frames with h < rest
    xs, ys = [], []
    for n in CLIPS:
        if n == name: continue
        o = cs[n]; m = o['full_h'] < 0.95 * o['rest']; w_rest = np.median(o['width'][-len(o['width']) // 5:])
        xs += list(np.log(o['full_h'][m] / o['rest'])); ys += list(np.log(o['width'][m] / w_rest))
    a = -np.sum(np.array(xs) * np.array(ys)) / np.sum(np.array(xs) ** 2)
    w_rest = np.median(c['width'][-len(c['width']) // 5:])
    t, i0 = c['full_t'], c['i_rel']; t_rel = t[i0]
    tt = np.arange(-PRE, 0.25, 1 / (OUT_FPS * SLOW))
    pos = tt >= 0; sh, _, sl = simulate(p, c, tt[pos])
    h_meas = np.interp(t_rel + tt, t, c['full_h'])
    hm = np.concatenate([h_meas[~pos], sh]); lift = np.concatenate([np.zeros((~pos).sum()), sl])
    need = sorted({int(np.searchsorted(t, t_rel + x, 'right') - 1) for x in tt})
    cxm = int(np.median(np.genfromtxt(f'{TRACK_OUT}/{name}.csv', delimiter=',', names=True)['cx_px'][i0 - 5:i0 + 40]))
    frames, i = {}, 0
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', f'videos/{name}.MOV', '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    while i <= need[-1]:
        buf = pr.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        if i in need: frames[i] = cv2.resize(np.frombuffer(buf, np.uint8).reshape(H, W, 3)[CROP[0]:CROP[1], cxm - 330:cxm + 330].copy(), (528, 440))
        i += 1
    pr.kill()
    out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '1056x500', '-r', str(OUT_FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f'models/lumped_1d/two_mass_spring/outputs/demo_squeeze_{name}.mp4'], stdin=subprocess.PIPE)
    s = 440 / (CROP[1] - CROP[0]); table_y = int((740 - CROP[0]) * s)
    for k, x in enumerate(tt):
        left = frames[int(np.searchsorted(t, t_rel + x, 'right') - 1)].copy()
        right = np.full((440, 528, 3), 238, np.uint8); cv2.line(right, (0, table_y), (528, table_y), (60, 60, 60), 2)
        ry = hm[k] * s / 2; rx = w_rest * (hm[k] / c['rest']) ** (-a) * s / 2
        shade(right, 264, table_y - 18 * s - lift[k] * s - ry, rx, ry)
        canvas = np.full((500, 1056, 3), 255, np.uint8); canvas[60:500, :528] = left; canvas[60:500, 528:] = right
        txt = lambda s_, x_, y_, sz=0.5: cv2.putText(canvas, s_, (x_, y_), cv2.FONT_HERSHEY_SIMPLEX, sz, (20, 20, 20), 1, cv2.LINE_AA)
        txt(f'{name} (held out)  t = {x*1e3:+.0f} ms from release  [{SLOW}x slow-mo]', 8, 20)
        txt(f'measured height {100*np.interp(t_rel+x,t,c["full_h"])/c["rest"]:.0f}% of rest', 8, 42, .45)
        txt(f'model height {100*hm[k]/c["rest"]:.0f}% of rest, lift {lift[k]/c["pxm"]*100:.1f} cm', 536, 42, .45)
        txt('REAL', 8, 78); txt('MODEL: ' + ('tin-driven (measured)' if x < 0 else 'simulated, no refit'), 536, 78)
        out.stdin.write(canvas.tobytes())
    out.stdin.close(); out.wait(); print('wrote', f'models/lumped_1d/two_mass_spring/outputs/demo_squeeze_{name}.mp4', f'width exponent a={a:.2f}')

if __name__ == '__main__': main(sys.argv[1])
