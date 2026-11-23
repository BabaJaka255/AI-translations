"""'Legend of' in the 海の style: chunky rounded letters, white-to-cyan fill, black 3D side to the lower right.
Local frame: cap top y=0, x-height top y=7, baseline y=22, descender to 28."""
import numpy as np
from scipy import ndimage as ndi
from eng import *

G = {}
G['L'] = dict(w=13.5, strokes=[[(3.6, 2.6, 2.8), (3.4, 12, 2.8), (3.6, 19.0, 2.8)], [(3.6, 19.3, 2.6), (8, 19.5, 2.5), (11.2, 19.2, 2.6)]])
G['e'] = dict(w=12.6, strokes=[[(3.8, 15.0, 1.5), (9.2, 14.8, 1.5), (10.2, 11.6, 2.1), (7.0, 9.2, 2.1), (3.8, 11.8, 2.6), (3.5, 16.6, 2.7), (6.4, 19.8, 2.2), (10.6, 18.6, 1.8)]])
G['g'] = dict(w=13.2, strokes=[[(9.6, 11, 2.0), (6.6, 9.2, 2.1), (3.7, 11.8, 2.6), (3.7, 16.2, 2.6), (6.6, 18.8, 2.1), (9.4, 17, 2.0)],
                             [(10.4, 9.0, 2.5), (10.4, 18, 2.6), (10.2, 23.6, 2.5), (7.4, 26.2, 2.1), (3.8, 25.2, 1.9)]])
G['n'] = dict(w=13.2, strokes=[[(3.6, 9.4, 2.6), (3.6, 19.4, 2.6)], [(3.8, 12.6, 1.8), (6.8, 9.5, 2.1), (10, 11.6, 2.6), (10.2, 19.4, 2.6)]])
G['d'] = dict(w=13.6, strokes=[[(9.6, 11, 2.0), (6.6, 9.2, 2.1), (3.7, 11.8, 2.6), (3.7, 17, 2.6), (6.6, 19.8, 2.1), (9.4, 18, 2.0)],
                             [(10.4, 2.4, 2.6), (10.4, 19.4, 2.6)]])
G['o'] = dict(w=13.2, strokes=[[(7, 9.2, 2.1), (3.8, 12, 2.6), (3.8, 17, 2.6), (7, 19.8, 2.1), (10.2, 17, 2.6), (10.2, 12, 2.6), (7, 9.2, 2.1)]])
G['f'] = dict(w=10, strokes=[[(9.8, 3.6, 1.9), (7.2, 2.0, 2.1), (4.8, 4.8, 2.5), (4.6, 19.4, 2.6)], [(1.8, 9.6, 1.6), (8.6, 9.4, 1.6)]])
G[' '] = dict(w=5, strokes=[])

CY = [(0.0, (248, 248, 248)), (0.22, (224, 248, 248)), (0.42, (176, 232, 248)), (0.62, (128, 208, 248)), (0.82, (88, 200, 248)), (1.0, (32, 176, 240))]


def text_masks(text, x, base, rot=-5.0, shear=-0.16, sc=1.0, track=0.0, bounce=()):
    """returns list of per-letter coverage maps (1x)"""
    out = []; pen = 0.0
    piv = Xf(x, base - 22, rot, sc, sc, 0, 22, shear)
    for i, ch in enumerate(text):
        g = G[ch]
        if g['strokes']:
            dy = bounce[i] if i < len(bounce) else 0
            m = hi()
            for pts in g['strokes']:
                p = np.array(pts, float); p[:, 0] += pen; p[:, 1] += dy
                stamp(m, stroke_path(piv, [tuple(q) for q in p]))
            out.append(down(m))
        pen += g['w'] + track
    return out


def cyan3d(cv, covs, depth=3, rng=None, outline=(0, 24, 56)):
    rng = rng or np.random.default_rng(3)
    fills = [c >= 0.5 for c in covs]
    allf = np.any(fills, 0)
    side = np.zeros_like(allf)
    for k in range(1, depth + 1):
        side |= shift(allf, k, k) | shift(allf, k, k - 1) | shift(allf, k - 1, k)
    solid = allf | side
    ring = ndi.binary_dilation(solid, np.ones((3, 3), bool)) & ~solid
    cv.put(ring, outline)
    near = side & ~allf
    dcol = np.where(rng.random(allf.shape + (1,)) < 0.3, np.array([24, 16, 16.0]), np.array([4, 0, 0.0]))
    cv.put(near, dcol)
    for f in fills:
        ys, xs = np.nonzero(f)
        if not len(ys): continue
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        yy, xx = np.mgrid[0:H, 0:W]
        # light from the upper left; the rim toward the lower right goes deeper blue
        din = ndi.distance_transform_edt(f)
        dlr = ndi.distance_transform_edt(~(shift(~f & True, -1, -1) & f)) if False else None
        v = 0.16 + 0.30 * (xx - x0) / max(1, x1 - x0) + 0.55 * (yy - y0) / max(1, y1 - y0)
        edge_lr = f & ~(shift(f, -1, 0) & shift(f, 0, -1))      # pixels whose right or lower neighbour is outside
        edge_ul = f & ~(shift(f, 1, 0) & shift(f, 0, 1))
        v = v + 0.28 * edge_lr - 0.10 * edge_ul + rng.normal(0, 0.02, f.shape)
        cv.put(f, ramp(v, CY))


if __name__ == '__main__':
    cv = Canvas()
    covs = text_masks('Legend of', 12, 34)
    cyan3d(cv, covs)
    show(cv, 'v_legend.png', 6, box=(0, 0, 140, 46))
