"""Hand-built lettering: each letter is a brush skeleton (polylines/arcs in units, cap height 10, x-height 6,
baseline 0). Rendered with a round brush that swells mid-stroke, per-letter tilt and bounce, then styled
(gradient fill, bevel shine, outline, drop shadow). No system font is used for display art."""
import math, random
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

def arc(cx, cy, rx, ry, a0, a1, n=None):
    n = n or max(6, int(abs(a1 - a0) / 12))
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
def L(*pts): return list(pts)
def bowl(cx, cy, rx, ry): return arc(cx, cy, rx, ry, 0, 360, 36)

# letter: (width, [strokes]); a stroke is a list of points; a 1-point stroke is a dot
G = {
 'A': (6.4, [L((0, 0), (3.2, 10), (6.4, 0)), L((1.4, 3.6), (5.0, 3.6))]),
 'B': (5.8, [L((0, 0), (0, 10), (2.8, 10)) + arc(2.8, 7.6, 2.5, 2.4, 90, -90) + L((0, 5.2), (3.0, 5.2)) + arc(3.0, 2.6, 2.8, 2.6, 90, -90) + L((0, 0))]),
 'D': (6.2, [L((0, 0), (0, 10), (2.2, 10)) + arc(2.2, 5, 4.0, 5, 90, -90) + L((0, 0))]),
 'E': (5.0, [L((5.0, 10), (0, 10), (0, 0), (5.2, 0)), L((0, 5.2), (4.2, 5.2))]),
 'F': (5.0, [L((5.0, 10), (0, 10), (0, 0)), L((0, 5.2), (4.2, 5.2))]),
 'G': (6.6, [arc(3.3, 5, 3.3, 5, 45, 335) + L((6.4, 4.4), (3.8, 4.4))]),
 'H': (5.8, [L((0, 0), (0, 10)), L((5.8, 0), (5.8, 10)), L((0, 5.2), (5.8, 5.2))]),
 'I': (0.0, [L((0, 0), (0, 10))]),
 'K': (5.6, [L((0, 0), (0, 10)), L((5.4, 10), (0, 3.6)), L((1.8, 5.6), (5.8, 0))]),
 'L': (4.8, [L((0, 10), (0, 0), (4.8, 0))]),
 'M': (7.6, [L((0, 0), (0.4, 10), (3.8, 2.6), (7.2, 10), (7.6, 0))]),
 'N': (6.0, [L((0, 0), (0, 10), (6.0, 0), (6.0, 10))]),
 'O': (7.0, [bowl(3.5, 5, 3.5, 5)]),
 'R': (5.8, [L((0, 0), (0, 10), (2.8, 10)) + arc(2.8, 7.4, 2.7, 2.6, 90, -90) + L((0, 4.8)), L((2.6, 4.8), (5.8, 0))]),
 'S': (5.8, [arc(3.0, 7.5, 2.8, 2.5, 25, 270) + arc(3.0, 2.5, 2.9, 2.5, 90, -155)]),
 'T': (6.2, [L((0, 10), (6.2, 10)), L((3.1, 10), (3.1, 0))]),
 'a': (4.8, [bowl(2.3, 2.9, 2.3, 2.9), L((4.8, 6), (4.8, 0))]),
 'd': (4.8, [bowl(2.3, 2.9, 2.3, 2.9), L((4.8, 10), (4.8, 0))]),
 'e': (5.0, [L((0.2, 3.3), (4.9, 3.3)) + arc(2.5, 3.0, 2.5, 3.0, 0, 285)]),
 'g': (4.8, [bowl(2.3, 3.2, 2.3, 2.8), L((4.8, 6), (4.8, -1.0)) + arc(2.5, -1.0, 2.3, 2.2, 0, -165)]),
 'h': (4.8, [L((0, 10), (0, 0)), L((0, 3.4)) + arc(2.4, 3.6, 2.4, 2.4, 180, 0) + L((4.8, 0))]),
 'i': (0.0, [L((0, 0), (0, 6)), L((0, 8.8))]),
 'l': (0.0, [L((0, 0), (0, 10))]),
 'm': (7.8, [L((0, 0), (0, 6)), L((0, 3.8)) + arc(1.95, 4.0, 1.95, 2.0, 180, 0) + L((3.9, 0)), L((3.9, 4.0)) + arc(5.85, 4.0, 1.95, 2.0, 180, 0) + L((7.8, 0))]),
 'n': (4.8, [L((0, 0), (0, 6)), L((0, 3.4)) + arc(2.4, 3.6, 2.4, 2.4, 180, 0) + L((4.8, 0))]),
 'o': (5.4, [bowl(2.7, 3.0, 2.7, 3.0)]),
 'r': (3.6, [L((0, 0), (0, 6)), L((0, 3.2)) + arc(2.6, 3.4, 2.6, 2.6, 180, 50)]),
 's': (4.4, [arc(2.3, 4.5, 2.1, 1.5, 25, 270) + arc(2.3, 1.5, 2.2, 1.5, 90, -160)]),
 't': (3.4, [L((1.0, 8.8), (1.0, 1.4)) + arc(2.6, 1.4, 1.6, 1.4, 180, 280), L((0, 6), (3.2, 6))]),
 'u': (4.8, [L((0, 6), (0, 2.6)) + arc(2.4, 2.6, 2.4, 2.6, 180, 360) + L((4.8, 6)), L((4.8, 6), (4.8, 0))]),
 'y': (5.0, [L((0, 6), (2.6, 0.6)), L((5.0, 6), (2.0, -2.4), (0.6, -3.0))]),
 'f': (3.6, [arc(2.6, 8.4, 1.6, 1.6, 30, 180) + L((1.0, 0)), L((0, 6), (3.4, 6))]),
 'U': (6.0, [L((0, 10), (0, 3.2)) + arc(3.0, 3.2, 3.0, 3.2, 180, 360) + L((6.0, 10))]),
 'C': (6.2, [arc(3.4, 5, 3.4, 5, 45, 315)]),
 'P': (5.6, [L((0, 0), (0, 10), (2.8, 10)) + arc(2.8, 7.3, 2.7, 2.7, 90, -90) + L((0, 4.6))]),
 'V': (6.2, [L((0, 10), (3.1, 0), (6.2, 10))]),
 'W': (8.4, [L((0, 10), (2.0, 0), (4.2, 7.2), (6.4, 0), (8.4, 10))]),
 'Y': (6.0, [L((0, 10), (3.0, 5.0), (6.0, 10)), L((3.0, 5.0), (3.0, 0))]),
 'J': (4.4, [L((4.4, 10), (4.4, 2.8)) + arc(2.2, 2.8, 2.2, 2.8, 0, -180)]),
 'Z': (5.6, [L((0, 10), (5.6, 10), (0, 0), (5.8, 0))]),
 'X': (6.0, [L((0, 10), (6.0, 0)), L((6.0, 10), (0, 0))]),
 'Q': (7.0, [bowl(3.5, 5, 3.5, 5), L((4.4, 2.0), (7.2, -0.6))]),
 'b': (4.8, [L((0, 10), (0, 0)), bowl(2.5, 2.9, 2.3, 2.9)]),
 'c': (4.6, [arc(2.6, 3.0, 2.6, 3.0, 40, 320)]),
 'k': (4.4, [L((0, 10), (0, 0)), L((4.2, 6), (0, 2.2)), L((1.4, 3.4), (4.6, 0))]),
 'p': (4.8, [L((0, 6), (0, -3.4)), bowl(2.5, 3.0, 2.3, 3.0)]),
 'v': (5.0, [L((0, 6), (2.5, 0), (5.0, 6))]),
 'w': (7.0, [L((0, 6), (1.7, 0), (3.5, 4.4), (5.3, 0), (7.0, 6))]),
 'x': (4.8, [L((0, 6), (4.8, 0)), L((4.8, 6), (0, 0))]),
 'z': (4.4, [L((0, 6), (4.4, 6), (0, 0), (4.6, 0))]),
 'j': (2.0, [L((2.0, 6), (2.0, -1.4)) + arc(0.6, -1.4, 1.4, 1.6, 0, -170), L((2.0, 8.8))]),
 'q': (4.8, [bowl(2.3, 3.0, 2.3, 3.0), L((4.8, 6), (4.8, -3.4))]),
 '.': (0.0, [L((0, 0.4))]),
 '!': (0.0, [L((0, 10), (0, 3.6)), L((0, 0.4))]),
 '?': (4.6, [arc(2.3, 7.6, 2.3, 2.4, 160, -60) + L((2.3, 3.6)), L((2.3, 0.4))]),
 "'": (0.0, [L((0, 10), (0, 7.4))]),
 'o2': (0, []),
 '0': (5.6, [bowl(2.8, 5, 2.8, 5)]),
 '1': (2.6, [L((0.2, 8.0), (2.4, 10), (2.4, 0))]),
 '%': (7.4, [bowl(1.5, 8.2, 1.5, 1.8), L((6.6, 10), (0.8, 0)), bowl(5.9, 1.8, 1.5, 1.8)]),
 '(': (1.2, [arc(4.0, 5, 4.0, 6.2, 135, 225)]),
 ')': (1.2, [arc(-2.8, 5, 4.0, 6.2, 45, -45)]),
 '-': (3.0, [L((0, 4.2), (3.0, 4.2))]),
 ',': (0.6, [L((0.6, 0.6), (-0.2, -1.8))]),
}

def render(text, cap, weight=0.34, spacing=1.3, tilt=5.0, bounce=0.06, seed=7, slant=0.0, space=3.2, swell=0.18, per_letter=False, scale_var=0.03):
    """-> (alpha mask float array, baseline y). cap = cap height in px; weight = stroke width / cap * 10"""
    rnd = random.Random(seed)
    u = cap / 10.0
    W = int(sum((G.get(c, (space, []))[0] + spacing) for c in text) * u + len(text) * weight * cap + 6 * cap)
    H = int(cap * 2.6)
    sc = 4
    layers = []
    im = Image.new('L', (W * sc, H * sc), 0); d = ImageDraw.Draw(im)
    base = cap * 1.7
    x = cap * 0.6
    bw = weight * u * 10 / 2  # brush radius in px
    for c in text:
        if c == ' ': x += space * u; continue
        w, strokes = G[c]
        ang = math.radians(rnd.uniform(-tilt, tilt)); dy = rnd.uniform(-bounce, bounce) * cap
        s = 1 + rnd.uniform(-scale_var, scale_var)
        cx = x + w * u / 2; cy = base - 5 * u
        def tf(p):
            px = x + p[0] * u * s + slant * p[1] * u; py = base - p[1] * u * s + dy
            rx, ry = px - cx, py - cy
            return cx + rx * math.cos(ang) - ry * math.sin(ang), cy + rx * math.sin(ang) + ry * math.cos(ang)
        for st in strokes:
            pts = [tf(p) for p in st]
            if len(pts) == 1: pts = pts * 2
            # resample and stamp a round brush that swells in the middle of each stroke
            seg = []
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                n = max(1, int(math.hypot(x1 - x0, y1 - y0) * 2))
                seg += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
            seg.append(pts[-1])
            for k, (px, py) in enumerate(seg):
                t = k / max(1, len(seg) - 1)
                r = bw * (1 + swell * math.sin(math.pi * t)) * sc
                d.ellipse((px * sc - r, py * sc - r, px * sc + r, py * sc + r), fill=255)
        x += (w + spacing) * u + 2 * bw
        if per_letter:
            layers.append(im); im = Image.new('L', (W * sc, H * sc), 0); d = ImageDraw.Draw(im)
    if per_letter:
        ms = [np.array(l.resize((W, H), Image.LANCZOS)).astype(float) / 255 for l in layers]
        right = max(np.nonzero(m.max(0) > 0.05)[0].max() for m in ms) + 2
        return [m[:, :right] for m in ms], base
    a = np.array(im.resize((W, H), Image.LANCZOS)).astype(float) / 255
    cols = np.nonzero(a.max(0) > 0.05)[0]; rows = np.nonzero(a.max(1) > 0.05)[0]
    return a[:, :cols.max() + 2], base

def style(mask, top, bottom, outline, shadow=None, shine=(255, 255, 255), shine_a=0.7, dark=0.35,
          outline_w=1.5, shadow_off=(2, 2), extrude=0, extrude_col=None):
    """mask: float alpha -> RGBA float image with gradient fill, bevel, outline and shadow"""
    h, w = mask.shape
    pad = int(outline_w + max(shadow_off) + extrude + 3)
    m = np.pad(mask, pad)
    H, Wd = m.shape
    ys = np.nonzero(m.max(1) > 0.5)[0]; y0, y1 = ys.min(), ys.max()
    t = np.clip((np.arange(H) - y0) / max(1, y1 - y0), 0, 1)[:, None, None]
    fill = np.array(top)[None, None] * (1 - t) + np.array(bottom)[None, None] * t
    fill = np.broadcast_to(fill, (H, Wd, 3)).copy()
    # bevel: light where the shape continues down-right but not up-left, dark the other way
    hi = np.clip(m - ndimage.shift(m, (1.6, 1.6), order=1), 0, 1)
    lo = np.clip(m - ndimage.shift(m, (-1.6, -1.6), order=1), 0, 1)
    fill = fill + (np.array(shine) - fill) * (hi * shine_a)[..., None]
    fill = fill * (1 - lo * dark)[..., None]
    out = np.zeros((H, Wd, 4))
    def over(col, alpha):
        a = np.clip(alpha, 0, 1)[..., None]
        out[..., :3] = out[..., :3] * (1 - a) + np.array(col, float) * a if np.ndim(col) == 1 else out[..., :3] * (1 - a) + col * a
        out[..., 3:] = out[..., 3:] + (1 - out[..., 3:]) * a
    ol = ndimage.grey_dilation(m, footprint=disk(outline_w))
    if shadow is not None:
        sh = ndimage.shift(ol, shadow_off, order=1)
        over(shadow, sh)
    if extrude:
        for k in range(extrude, 0, -1):
            over(extrude_col, ndimage.shift(ol, (k, k * 0.6), order=1))
    over(outline, ol)
    over(fill, m)
    return out, pad

def disk(r):
    R = int(math.ceil(r)); y, x = np.mgrid[-R:R + 1, -R:R + 1]
    return (x * x + y * y) <= r * r + 0.3

def paste(base_rgba, art, x, y, anchor='mm'):
    """composite art (float RGBA 0-255 colours, alpha 0-1) onto uint8 RGBA array; (x, y) = centre of the art"""
    h, w = art.shape[:2]
    x0 = int(round(x - w / 2)) if anchor[0] == 'm' else int(x); y0 = int(round(y - h / 2)) if anchor[1] == 'm' else int(y)
    for yy in range(h):
        Y = y0 + yy
        if not 0 <= Y < base_rgba.shape[0]: continue
        for xx0 in [0]:
            X0 = max(0, x0); X1 = min(base_rgba.shape[1], x0 + w)
            if X1 <= X0: continue
            a = art[yy, X0 - x0:X1 - x0, 3:4]
            b = base_rgba[Y, X0:X1].astype(float)
            ba = b[:, 3:4] / 255
            col = art[yy, X0 - x0:X1 - x0, :3] * a + b[:, :3] * (1 - a)
            na = a + ba * (1 - a)
            base_rgba[Y, X0:X1, :3] = np.clip(col, 0, 255)
            base_rgba[Y, X0:X1, 3:4] = np.clip(na * 255, 0, 255)
    return base_rgba

def style_letters(masks, *a, **k):
    """style each letter separately and stack them left to right so overlaps keep their outlines"""
    out = None
    for m in masks:
        art, pad = style(m, *a, **k)
        if out is None: out = np.zeros_like(art)
        al = art[..., 3:4]
        out[..., :3] = art[..., :3] * al + out[..., :3] * (1 - al)
        out[..., 3:] = al + out[..., 3:] * (1 - al)
    return out, pad
