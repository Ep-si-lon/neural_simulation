"""SAM 2 (pretrained Segment Anything 2, tiny) video tracking of the ball, as an alternative to the colour threshold in track.py.
One automatic prompt on frame 0 (positive point at the ball centre, negative point on the table reflection, both taken from the colour mask), then SAM 2 propagates the mask.
Outputs tracking/outputs_sam2/<clip>_sil.npz (same fields as the colour silhouette) and <clip>_compare.txt (agreement with the colour tracker).
Needs .venv-sim (PyTorch + sam2). Usage: segment_sam2.py IMG_0536"""
import os, sys, subprocess, shutil
import numpy as np, cv2, torch
from common import W, H
from track import measure, yellow, TABLE_Y, X0, X1
from sam2.build_sam import build_sam2_video_predictor_hf

SC = 2                                   # work at half resolution (960 x 540); outputs are scaled back to 1080p pixels
NL = 48
FRAMES = os.environ.get('SAM2_FRAMES', '/tmp/sam2_frames')

def sil_from_mask(m):
    """Same outline measurement as silhouette.py, on a boolean mask at half resolution."""
    m = m.astype(np.uint8); m[TABLE_Y // SC:] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n < 2: return None
    m = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    ff = m.copy(); cv2.floodFill(ff, np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8), (0, 0), 2); m = (ff != 2).astype(np.uint8)
    rows = np.flatnonzero(m.any(1)); top, bot = rows[0], rows[-1]
    ys = np.linspace(top + 1, bot - 1, NL).round().astype(int)
    left = np.array([np.flatnonzero(m[y])[0] for y in ys], float); right = np.array([np.flatnonzero(m[y])[-1] for y in ys], float)
    return m, top, bot, left, right

def colour_mask(img):
    s = yellow(img)[:TABLE_Y // SC * 1, X0 // SC:X1 // SC] > 0.5
    full = np.zeros(img.shape[:2], bool); full[:s.shape[0], X0 // SC:X1 // SC] = s
    return full

def main(name):
    d = f'{FRAMES}/{name}'; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    subprocess.run(['ffmpeg', '-v', 'error', '-i', f'videos/{name}.MOV', '-fps_mode', 'passthrough', '-vf', f'scale={W // SC}:{H // SC}', '-q:v', '3', '-start_number', '0', f'{d}/%05d.jpg'], check=True)
    nfr = len(os.listdir(d))
    first = cv2.imread(f'{d}/00000.jpg'); full0 = cv2.resize(first, (W, H))
    top, bot, w, cx = measure(full0)
    pos = [cx / SC, (top + bot) / 2 / SC]; neg = [cx / SC, (bot + 70) / SC]            # ball centre; table reflection below the ball
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    pred = build_sam2_video_predictor_hf('facebook/sam2.1-hiera-tiny', device=dev)
    pts_s = sorted(float(x) for x in subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'packet=pts_time', '-of', 'csv=p=0', f'videos/{name}.MOV'], capture_output=True, text=True).stdout.split())[:nfr]
    T, B, L, R, iou, dtop, dbot, dw = [], [], [], [], [], [], [], []
    with torch.inference_mode(), torch.autocast(dev, dtype=torch.bfloat16, enabled=dev == 'cuda'):
        state = pred.init_state(video_path=d, offload_video_to_cpu=True, offload_state_to_cpu=True)
        pred.add_new_points_or_box(state, frame_idx=0, obj_id=1, points=np.array([pos, neg], np.float32), labels=np.array([1, 0], np.int32))
        for fi, ids, logits in pred.propagate_in_video(state):
            m = (logits[0, 0] > 0).float().cpu().numpy() > 0
            s = sil_from_mask(m)
            if s is None: T.append(np.nan); B.append(np.nan); L.append(np.full(NL, np.nan)); R.append(np.full(NL, np.nan)); iou.append(0); continue
            mm, t, b, l, r = s
            T.append(t * SC); B.append(b * SC); L.append(l * SC); R.append(r * SC)
            cm = sil_from_mask(colour_mask(cv2.imread(f'{d}/{fi:05d}.jpg')))
            if cm is not None:
                m2 = cm[0] > 0; iou.append((mm & m2).sum() / max((mm | m2).sum(), 1)); dtop.append(abs(t - cm[1]) * SC); dbot.append(abs(b - cm[2]) * SC)
                dw.append(abs((r - l).max() - (cm[4] - cm[3]).max()) * SC)
    os.makedirs('tracking/outputs_sam2', exist_ok=True)
    np.savez(f'tracking/outputs_sam2/{name}_sil.npz', frame=np.arange(len(T)), pts_s=np.array(pts_s[:len(T)]), top=np.array(T, float), bottom=np.array(B, float), left=np.array(L), right=np.array(R))
    txt = (f'{name}: {len(T)} frames, device {dev}\nmask IoU vs colour tracker: mean {np.mean(iou):.3f}, 5th percentile {np.percentile(iou, 5):.3f}, min {np.min(iou):.3f}\n'
           f'mean |top edge diff| {np.mean(dtop):.1f} px, |bottom edge diff| {np.mean(dbot):.1f} px, |max width diff| {np.mean(dw):.1f} px (1080p pixels; ball is about 400 px)\n')
    open(f'tracking/outputs_sam2/{name}_compare.txt', 'w').write(txt); print(txt)
    shutil.rmtree(d, ignore_errors=True)

if __name__ == '__main__': main(sys.argv[1])
