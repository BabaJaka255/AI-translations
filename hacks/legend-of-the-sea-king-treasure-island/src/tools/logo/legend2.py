"""'Legend of' traced from the Legend of the River King GB box logo (the fat rounded letters with the two-storey g),
shaded in the 海の style by legend.cyan3d."""
import numpy as np, cv2
from PIL import Image
from eng import *
from legend import cyan3d

CUTS = [0, 50, 88, 124, 160, 196, 240, 291, 320]       # letter boundaries in the crop, for per-letter shading


def traced(x, y, scale=0.34, rot=0.0):
    """list of per-letter coverage maps; the crop's (20, 22) corner lands on band (x, y)"""
    a = np.array(Image.open('ref_river.png').convert('RGB')).astype(int)[40:125, 190:510]
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    teal = (R < 110) & (G > 80) & (G < 170) & (B > 80) & (B < 170) & (G - R > 35)
    out = []
    k = scale * SS
    r = np.deg2rad(rot); c, s = np.cos(r) * k, np.sin(r) * k
    M = np.float32([[c, -s, x * SS - (c * 20 - s * 22)], [s, c, y * SS - (s * 20 + c * 22)]])
    for x0, x1 in zip(CUTS, CUTS[1:]):
        m = np.zeros(teal.shape, np.float32); m[:, x0:x1] = teal[:, x0:x1]
        if m.sum() < 20: continue
        m = cv2.GaussianBlur(m, (0, 0), 0.9)
        hi_ = cv2.warpAffine(m, M, (W * SS, H * SS), flags=cv2.INTER_CUBIC)
        out.append(down(((hi_ >= 0.5) * 255).astype(np.uint8)))
    return out


if __name__ == '__main__':
    cv = Canvas(); cyan3d(cv, traced(8, 10))
    show(cv, 'v_legend2.png', 7, box=(0, 0, 130, 44))
