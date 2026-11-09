"""2D demo helpers: crop rows for the real-clip panel and a numpy-shaded ellipse (the ellipsoid proxy)."""
import numpy as np

CROP = (250, 800)     # rows of the 1080p frame shown around the ball

def shade(canvas, cx, cy, rx, ry):
    yy, xx = np.mgrid[0:canvas.shape[0], 0:canvas.shape[1]].astype(np.float32)
    u, v = (xx - cx) / rx, (yy - cy) / ry; r2 = u * u + v * v
    inside = r2 <= 1
    nz = np.sqrt(np.clip(1 - r2, 0, 1)); light = np.clip(0.55 * nz - 0.35 * u - 0.35 * v + 0.35, 0.15, 1.0)
    for ch, base in enumerate((40, 220, 250)):                 # BGR yellow
        canvas[..., ch] = np.where(inside, (base * light).astype(np.uint8), canvas[..., ch])

