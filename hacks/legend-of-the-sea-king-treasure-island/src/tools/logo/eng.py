"""Hand-lettering engine for the Sea King title logo: brush strokes -> pixel shading in the original's style."""
import numpy as np, cv2
from PIL import Image

W, H, SS = 256, 144, 8
BG = np.array([40, 60, 110], float)


def spline(pts, n=20):
    P = np.array(pts, float)
    if len(P) == 2:
        t = np.linspace(0, 1, n + 1)[:, None]
        return P[0] * (1 - t) + P[1] * t
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return np.array(out)


class Xf:
    """local letter coords -> band coords"""
    def __init__(s, ox, oy, rot=0.0, sx=1.0, sy=1.0, cx=0.0, cy=0.0, shear=0.0):
        s.o = np.array([ox, oy], float); s.c = np.array([cx, cy], float)
        a = np.deg2rad(rot)
        R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        S = np.array([[sx, shear * sx], [0, sy]])
        s.M = R @ S; s.k = (abs(sx) * abs(sy)) ** 0.5
    def __call__(s, p):
        p = np.asarray(p, float)
        return (p - s.c) @ s.M.T + s.c + s.o


def hi(shape=None):
    return np.zeros((H * SS, W * SS), np.uint8)


def stamp(mask, path, val=255):
    """path: Nx3 (x, y, r) in band coords"""
    for x, y, r in path:
        cv2.circle(mask, (int(round(x * SS * 16)), int(round(y * SS * 16))), int(round(max(r, 0.05) * SS * 16)), val, -1, cv2.LINE_8, 4)


def poly(mask, pts, val=255):
    cv2.fillPoly(mask, [np.round(np.array(pts) * SS * 16).astype(np.int32)], val, cv2.LINE_8, 4)


def down(mask):
    return mask.reshape(H, SS, W, SS).mean((1, 3)) / 255.0


def stroke_path(xf, pts, n=20):
    """pts: list of (x, y, r) local; returns Nx3 band path"""
    sp = spline(pts, n)
    xy = xf(sp[:, :2])
    return np.column_stack([xy, sp[:, 2] * xf.k])


def offset_line(path, t0, t1, side, inset):
    """points along a stroke path, pushed to one side to (r - inset) from the centre"""
    n = len(path); i0, i1 = int(t0 * (n - 1)), int(t1 * (n - 1))
    seg = path[i0:i1 + 1]
    d = np.gradient(seg[:, :2], axis=0); d /= np.linalg.norm(d, axis=1)[:, None] + 1e-9
    nrm = np.column_stack([-d[:, 1], d[:, 0]]) * side
    return seg[:, :2] + nrm * (seg[:, 2] - inset)[:, None]


def line_mask(lines, width):
    m = hi()
    for ln in lines:
        pts = np.round(np.array(ln) * SS * 16).astype(np.int32)
        cv2.polylines(m, [pts], False, 255, max(1, int(round(width * SS))), cv2.LINE_AA, 4)
    return m


def kasure(mask, p, d, r, teeth, slit=5.0, gap=0.55):
    """split-brush end past point p along dir d: teeth = [(offset across -1..1, length, radius)] are small tapered
    prongs; between neighbours a thin slit is cut back into the stroke (the dry-brush streaks of the reference logos)"""
    p = np.array(p, float); d = np.array(d, float); d /= np.linalg.norm(d); q = np.array([-d[1], d[0]])
    teeth = sorted(teeth)
    for off, ln, w in teeth:
        b = p + q * off * r - d * r * 0.5
        n = int((ln + r * 1.5) * 4) + 2
        ts = np.linspace(0, 1, n)[:, None]
        pts = b + d * ts * (ln + r * 1.5) + q * (off * 0.10 * ln) * ts ** 2
        rad = w * (1 - 0.45 * ts[:, 0] ** 2)
        stamp(mask, np.column_stack([pts, rad]))
    far = max(t[1] for t in teeth) + r * 1.2 + 2
    for (a, la, wa), (b, lb, wb) in zip(teeth, teeth[1:]):
        m = p + q * (a + b) / 2 * r
        poly(mask, [m - q * gap + d * far, m + q * gap + d * far, m - d * slit], 0)


RAMP = [(0.00, (248, 24, 0)), (0.15, (248, 24, 0)), (0.21, (248, 48, 0)), (0.27, (248, 72, 12)), (0.34, (248, 100, 8)),
        (0.41, (248, 136, 16)), (0.48, (248, 152, 8)), (0.55, (248, 176, 12)), (0.60, (248, 188, 0)), (0.65, (248, 208, 0)),
        (0.72, (248, 232, 0)), (0.78, (248, 248, 0)), (1.0, (248, 248, 0))]


def ramp(t, table=RAMP):
    t = np.clip(t, 0, 1)
    xs = [a for a, _ in table]; out = np.zeros(t.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(t, xs, [v[c] for _, v in table])
    return out


def shift(m, dx, dy):
    out = np.zeros_like(m)
    h, w = m.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = m[ys, xs]
    return out


class Canvas:
    def __init__(s):
        s.rgb = np.zeros((H, W, 3)); s.a = np.zeros((H, W), bool)
    def put(s, mask, col):
        """mask bool; col (3,) or HxWx3"""
        col = np.asarray(col, float)
        s.rgb[mask] = col[mask] if col.ndim == 3 else col
        s.a |= mask
    def blend(s, cov, col):
        col = np.asarray(col, float)
        c = cov[..., None]
        s.rgb = s.rgb * (1 - c) + (col if col.ndim == 3 else col[None, None, :]) * c
    def over(s, other):
        s.rgb[other.a] = other.rgb[other.a]; s.a |= other.a
    def image(s):
        out = np.zeros((H, W, 4), np.uint8)
        out[..., :3] = np.clip(np.round(s.rgb), 0, 255); out[..., 3] = np.where(s.a, 255, 0)
        return Image.fromarray(out, 'RGBA')


def bubble(cv, cov, top, bot, hl=None, rng=None, shadow=((1, 1), (2, 2), (2, 1), (1, 2)), halo=(8, 40, 72), table=RAMP, aa=True):
    """the big red-to-yellow letters: shadow lower right, dark halo, banded gradient, white streaks"""
    rng = rng or np.random.default_rng(1)
    fill = cov >= 0.5
    sh = np.zeros_like(fill)
    for dx, dy in shadow: sh |= shift(fill, dx, dy)
    solid = fill | sh
    ring = (shift(solid, 1, 0) | shift(solid, 0, 1)) & ~solid
    cv.put(ring, halo)
    cv.put(sh & ~fill, (0, 0, 0))
    yy = np.repeat(np.arange(H)[:, None], W, 1).astype(float)
    t = (yy - top) / (bot - top) + rng.normal(0, 0.012, fill.shape)
    col = ramp(t, table)
    cv.put(fill, col)
    if aa:
        edge = (cov > 0.22) & ~fill & ~solid
        e = np.clip(cov * 1.5, 0, 1)[..., None]
        cv.put(edge, col * e + BG * 0.6 * (1 - e))
    if hl is not None:
        h = np.where(fill, hl, 0)
        cv.blend(np.clip(h * 1.25, 0, 1), np.array([255, 255, 236.0]))
    return fill


def show(img, path, scale=4, bg=(40, 60, 110), box=None):
    im = img if isinstance(img, Image.Image) else img.image()
    b = Image.new('RGBA', im.size, tuple(bg) + (255,)); b.alpha_composite(im)
    if box: b = b.crop(box)
    b.resize((b.size[0] * scale, b.size[1] * scale), Image.NEAREST).save(path)
