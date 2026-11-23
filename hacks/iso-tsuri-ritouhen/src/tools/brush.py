"""Tiny brush-stroke renderer for hand-drawn title lettering (no fonts).

A stroke is a list of (x, y, r) points in 1x screen pixels: the brush follows a Catmull-Rom curve through the
points and its radius follows r, so a stroke can press in heavy, thin out and flick off like a calligraphy brush.
The nib is a slightly flattened ellipse tilted like a brush held at an angle.
render() returns a coverage map at SS x resolution; shade() turns it into BG pixels the way the original
磯釣り logo is shaded: red body, dark red on the lit (upper-left) anti-aliased rim, black drop shadow lower-right.
"""
import math
from PIL import Image, ImageDraw

SS = 4                      # supersampling
NIB = (1.0, 0.62, -0.75)    # x scale, y scale, tilt (radians)

def _cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3)
                 for a, b, c, d in zip(p0, p1, p2, p3))

def samples(pts, step=0.25):
    pts = [tuple(p) + (0,) * (4 - len(p)) for p in pts]   # (x, y, r, dry)
    pts = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1:i + 3]
        n = max(2, int(math.dist(p1[:2], p2[:2]) / step))
        out += [_cr(p0, p1, p2, p3, k / n) for k in range(n)]
    out.append(tuple(pts[-2]))
    return out

def _nib(d, x, y, r):
    sx, sy, a = NIB
    if r <= 0: return
    pts = []
    for k in range(20):
        t = 2 * math.pi * k / 20
        ex, ey = math.cos(t) * r * sx, math.sin(t) * r * sy
        pts.append(((x + ex * math.cos(a) - ey * math.sin(a)) * SS, (y + ex * math.sin(a) + ey * math.cos(a)) * SS))
    d.polygon(pts, fill=255)

def render(strokes, size=(256, 224)):
    """A point's 4th value > 0.5 makes that stretch 'dry': the brush splits into bristle streaks (kasure)."""
    im = Image.new('L', (size[0] * SS, size[1] * SS), 0); d = ImageDraw.Draw(im)
    for s in strokes:
        sm = samples(s)
        for i, (x, y, r, dry) in enumerate(sm):
            if dry <= 0.5:
                _nib(d, x, y, r); continue
            j = min(i + 1, len(sm) - 1); k = max(i - 1, 0)
            dx, dy = sm[j][0] - sm[k][0], sm[j][1] - sm[k][1]; n = math.hypot(dx, dy) or 1
            nx, ny = -dy / n, dx / n
            for off in (-0.62, 0.62):
                _nib(d, x + nx * r * off, y + ny * r * off, r * 0.36)
    return im

def coverage(im):
    """Per-pixel coverage 0..1 at 1x."""
    w, h = im.width // SS, im.height // SS
    small = im.resize((w, h), Image.BOX)
    return [[small.getpixel((x, y)) / 255 for x in range(w)] for y in range(h)]

def shade(cov, full=0.62, rim=0.3, shadow=((1, 1), (2, 1), (2, 2), (1, 2))):
    """Return dict (x, y) -> 1 black / 2 body / 3 rim, like the original logo's palette use."""
    h, w = len(cov), len(cov[0])
    out = {}
    body = {(x, y) for y in range(h) for x in range(w) if cov[y][x] >= rim}
    for (x, y) in body:
        c = cov[y][x]
        lit = (x - 1, y) not in body or (x, y - 1) not in body
        out[(x, y)] = 3 if (c < full and lit) else 2
    for (x, y) in body:
        for dx, dy in shadow:
            q = (x + dx, y + dy)
            if q not in body and 0 <= q[0] < w and 0 <= q[1] < h: out[q] = 1
    return out
