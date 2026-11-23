"""The marlin from the original logo, with the body that 海の used to hide painted back in."""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from eng import *

ORIG = np.array(Image.open('title_logo_only_original.png').convert('RGBA'))


def original_parts():
    """sail, head and bill pixels of the original (everything right of の), as an RGBA layer in original coords"""
    a = ORIG.copy()
    yy, xx = np.mgrid[0:H, 0:W]
    keep = (xx >= 60) & (yy <= 50) & (a[..., 3] > 0)
    keep &= ((xx - 59.5) ** 2 + (yy - 30.5) ** 2) > 19.0 ** 2          # the の and its 3D side
    keep &= ~((yy > 40) & (xx < 80))                                    # lower extrusion of の
    c = a[..., :3].astype(int)
    warm = (c[..., 0] > 180) & (c[..., 2] < 140) & (c[..., 0] > c[..., 2] + 60)   # ぬ / し tops
    keep &= ~warm
    keep &= ~((yy > 44))
    lab, n = ndi.label(keep)
    if n:
        sizes = ndi.sum(keep, lab, range(1, n + 1))
        keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= 6])
    a[~keep] = 0
    return a


BODY = [(88, 29, 9.5), (76, 32.5, 10.5), (62, 37.5, 10.0), (48, 43.5, 8.0), (36, 49.5, 5.4), (27, 54, 3.2)]


def body_layer(rng=None):
    """painted body in original coords: navy back, lavender flank, white belly, as an RGBA float layer"""
    rng = rng or np.random.default_rng(11)
    xf = Xf(0, 0)
    path = stroke_path(xf, BODY, 30)
    m = hi(); stamp(m, path)
    cov = down(m); f = cov >= 0.5
    yy, xx = np.mgrid[0:H, 0:W]
    P = path[:, :2]
    d2 = (xx[..., None] - P[:, 0]) ** 2 + (yy[..., None] - P[:, 1]) ** 2
    k = d2.argmin(-1)
    tang = np.gradient(P, axis=0); tang /= np.linalg.norm(tang, axis=1)[:, None]
    nrm = np.column_stack([-tang[:, 1], tang[:, 0]])                      # points to the belly side for a head->tail path? checked below
    off = (xx - P[k, 0]) * nrm[k, 0] + (yy - P[k, 1]) * nrm[k, 1]
    u = off / path[k, 2]
    if u[int(BODY[2][1]) + 8, int(BODY[2][0])] < 0: u = -u               # make +1 = belly (below the axis)
    s = k / (len(P) - 1.0)                                               # 0 head .. 1 tail
    stops = [(-1.0, (40, 32, 96)), (-0.62, (64, 56, 128)), (-0.30, (112, 96, 160)), (-0.05, (168, 152, 200)),
             (0.12, (232, 228, 244)), (0.50, (248, 248, 248)), (0.74, (184, 196, 224)), (1.0, (56, 72, 144))]
    xs = [a for a, _ in stops]
    col = np.zeros((H, W, 3))
    un = np.clip(u + rng.normal(0, 0.05, u.shape), -1, 1)
    for c in range(3): col[..., c] = np.interp(un, xs, [v[c] for _, v in stops])
    navy = np.array([16, 32, 112.0])
    w = np.clip((s - 0.45) / 0.5, 0, 1)[..., None] * 0.75                # toward the tail the body turns deep blue
    col = col * (1 - w * (un[..., None] < 0.1)) + navy * (w * (un[..., None] < 0.1))
    # thin white streaks along the flank, like the ones round the head
    for uu, s0, s1 in ((-0.42, 0.05, 0.50), (-0.16, 0.0, 0.62), (-0.70, 0.12, 0.34)):
        st = (np.abs(u - uu) < 0.07) & (s > s0) & (s < s1)
        col[st] = (236, 228, 244)
    out = np.zeros((H, W, 4)); out[..., :3] = col; out[..., 3] = f * 255
    edge = f & ~ndi.binary_erosion(f)
    out[edge & (u < 0), :3] = (24, 16, 72)
    return out


def tail_part():
    a = ORIG.copy(); c = a[..., :3].astype(int)
    yy, xx = np.mgrid[0:H, 0:W]
    keep = (xx < 36) & (yy >= 44) & (yy < 86) & (a[..., 3] > 0) & (c[..., 2] > c[..., 0] + 20)
    keep &= ~((yy < 60) & (xx > 22) & (c.sum(-1) > 500))           # the white belly streak under 海
    a[~keep] = 0
    return a


def marlin(dx=0, dy=0, tail=True):
    parts = original_parts().astype(float)
    body = body_layer()
    lay = body.copy()
    if tail:
        t = tail_part().astype(float); m = (t[..., 3] > 0) & ~(lay[..., 3] > 0)
        lay[m] = t[m]
    m = parts[..., 3] > 0
    lay[m] = parts[m]
    out = np.zeros_like(lay)
    h, w = lay.shape[:2]
    ys = slice(max(0, dy), min(h, h + dy)); xs = slice(max(0, dx), min(w, w + dx))
    out[ys, xs] = lay[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
    return out


def paste_layer(cv, lay):
    m = lay[..., 3] > 0
    cv.rgb[m] = lay[m][:, :3]; cv.a |= m


if __name__ == '__main__':
    cv = Canvas(); paste_layer(cv, marlin())
    show(cv, 'v_marlin.png', 6, box=(0, 0, 140, 70))
