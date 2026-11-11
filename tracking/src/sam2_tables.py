"""Turn the SAM 2 silhouettes (tracking/outputs_sam2/<clip>_sil.npz) into the same per-frame tables the colour tracker writes (<clip>.csv, <clip>_shape.csv),
so every model can switch tracker with the environment variable TRACKER=sam2. SAM 2 is the reference for the top edge: while the ball is pressed, the colour threshold
picks up a reflection of the ball on the shiny underside of the tin, which makes the top edge read too high (about 16-20 px, 4-5 % of the height)."""
import sys, csv
import numpy as np
from shape_curve import fit_frame

def main(name):
    z = np.load(f'tracking/outputs_sam2/{name}_sil.npz'); w = z['right'] - z['left']
    width = np.nanmax(w, 1); cx = np.nanmean((z['left'][:, 10:38] + z['right'][:, 10:38]) / 2, 1)
    with open(f'tracking/outputs_sam2/{name}.csv', 'w', newline='') as fh:
        wr = csv.writer(fh); wr.writerow(['frame', 't_s', 'pts_s', 'top_px', 'bottom_px', 'width_px', 'cx_px'])
        for i in range(len(z['top'])): wr.writerow([i, i / 240, z['pts_s'][i], z['top'][i], z['bottom'][i], width[i], cx[i]])
    with open(f'tracking/outputs_sam2/{name}_shape.csv', 'w', newline='') as fh:
        wr = csv.writer(fh); wr.writerow(['frame', 'pts_s', 'top_px', 'bottom_px', 'W_px', 'n', 'fit_rms_px'])
        for i in range(len(z['top'])):
            W, n, rms = fit_frame(w[i], None); wr.writerow([i, z['pts_s'][i], z['top'][i], z['bottom'][i], W, n, rms])
    print(name, 'tables written', int(np.isnan(z['top']).sum()), 'frames without a mask')

if __name__ == '__main__': main(sys.argv[1])
