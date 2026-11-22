# Mask of the old Japanese logo in the game title pictures (colour rule inside hand-drawn boxes).
import numpy as np, colorsys
from PIL import Image
def hsv(rgb):
    a = rgb.astype(float) / 255
    mx, mn = a.max(2), a.min(2); d = mx - mn + 1e-9
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx
def dil(m, n=1):
    for _ in range(n):
        m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
    return m
def mask(nm):
    rgb = np.load(nm + '_pal.npy')[np.load(nm + '_idx.npy')]
    h, s, v = hsv(rgb)
    warm = ((h < 65) | (h > 330)) & (s > 0.45) & (v > 0.45)
    dark = v < 0.35
    box = np.zeros(rgb.shape[:2], bool)
    for x0, y0, x1, y1 in BOXES[nm]: box[y0:y1, x0:x1] = True
    m = warm & box
    for x0, y0, x1, y1 in KEEP.get(nm, []): m[y0:y1, x0:x1] = False
    m = m | (dark & dil(m, 2) & box)
    return rgb, m
KEEP = {'t3': [(134, 64, 182, 82)]}
BOXES = {'t3': [(28, 0, 222, 82)], 't4': [(22, 76, 89, 112), (22, 106, 224, 160)]}
if __name__ == '__main__':
    for nm in BOXES:
        rgb, m = mask(nm)
        v = rgb.copy(); v[m] = [255, 0, 255]
        Image.fromarray(v).resize((720, 480), Image.NEAREST).save(nm + '_mask.png')
