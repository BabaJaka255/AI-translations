"""A whole blue marlin, drawn from scratch in the game's colours (the original logo only ever showed its tail, sail
and bill round the 海の). Local frame: fish points right, x = 0 at the tail tips .. 131 at the bill tip, y down,
0 on the body axis. Painted at 8x, then rotated into the band and averaged down."""
import numpy as np, cv2
from PIL import Image
from scipy.interpolate import PchipInterpolator
from eng import W, H, SS, spline, Canvas, show

LW, LH, X0, Y0 = 140, 48, 4, 26        # local canvas in px, and where local (0, 0) sits in it

TOP = [(16, -1.8), (24, -2.8), (34, -4.6), (46, -6.6), (58, -8.0), (70, -8.8), (80, -8.9), (88, -8.2), (94, -6.6), (99, -4.6), (102, -3.2)]
BOT = [(16, 1.8), (24, 3.0), (34, 4.8), (46, 6.6), (58, 7.8), (70, 8.4), (80, 8.0), (88, 6.8), (94, 5.4), (99, 4.0), (102, 3.2)]
DORSAL = [(90, -7), (87, -13.5), (83.5, -19.5), (80.5, -21.5), (78.5, -20), (76.5, -16.5), (73, -13.6), (66, -12.0), (56, -10.6),
          (46, -8.8), (38, -6.8), (33, -4.6), (36, -3), (88, -5)]
TAIL = [(19, -1.8), (16, -4), (12.5, -7.6), (8.4, -11.6), (4.6, -14.6), (1, -16.6), (2.8, -13.6), (5, -10), (7.2, -6.4), (8.6, -3.2),
        (9.2, 0), (8.6, 3.2), (7.2, 6.4), (5.2, 10), (3.2, 13.6), (1.6, 16.6), (5, 14.6), (8.8, 11.6), (12.8, 7.6), (16.2, 4), (19, 1.8)]
BILL = [(100, -3.4), (108, -2.5), (118, -1.3), (126, -0.3), (131.5, 0.5), (126, 0.9), (116, 1.0), (100, 1.2)]
JAW = [(99, 1.0), (106, 1.9), (112.5, 2.7), (107, 3.2), (98, 3.8)]
PECT = [(87.5, 3.0), (80, 5.2), (70, 8.8), (61, 12.2), (70, 6.4), (80, 3.0), (86.5, 1.4)]
PELV = [(85, 7.2), (76, 12.8), (72, 14.6), (75, 12.2), (83.5, 7.4)]
ANAL = [(48, 6.2), (42.5, 11.8), (40.5, 11.4), (41, 6.6)]
DORS2 = [(28, -3.2), (23, -6.6), (21.5, -2.4)]
ANAL2 = [(28, 3.4), (23.5, 6.6), (21.5, 2.6)]

NAVY, DEEP, COBALT, SKY = (16, 24, 96), (24, 16, 72), (40, 88, 184), (120, 168, 224)
SILVER, WHITE, SHADE = (208, 220, 240), (246, 248, 250), (112, 128, 176)


def P(pts):
    return np.round((np.array(pts, float) + (X0, Y0)) * SS * 16).astype(np.int32)


def fill(shape, pts, smooth=True):
    m = np.zeros(shape, np.uint8)
    q = np.array(pts, float)
    if smooth and len(q) > 3:
        q = spline(np.vstack([q, q[:1]]), 8)
    cv2.fillPoly(m, [P(q)], 255, cv2.LINE_AA, 4)
    return m.astype(np.float32) / 255


def lines(shape, segs, width):
    m = np.zeros(shape, np.uint8)
    for s in segs:
        cv2.polylines(m, [P(s)], False, 255, max(1, int(round(width * SS))), cv2.LINE_AA, 4)
    return m.astype(np.float32) / 255


def paint():
    """RGBA float image of the fish at local hi-res"""
    hh, ww = LH * SS, LW * SS
    shape = (hh, ww)
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    lx = xx / SS - X0; ly = yy / SS - Y0
    rgb = np.zeros((hh, ww, 3), np.float32); al = np.zeros(shape, np.float32)

    def over(m, col):
        nonlocal rgb, al
        col = np.asarray(col, np.float32)
        c = col if col.ndim == 3 else col[None, None, :]
        rgb = rgb * (1 - m[..., None]) + c * m[..., None]
        al = np.maximum(al, m)

    def grad(stops, t):
        xs = [a for a, _ in stops]; out = np.zeros(t.shape + (3,), np.float32)
        for c in range(3): out[..., c] = np.interp(t, xs, [v[c] for _, v in stops])
        return out

    # fins that sit behind the body
    d = fill(shape, DORSAL)
    dh = np.clip((-ly - 8) / 13, 0, 1)                                    # height up the sail
    over(d, grad([(0, (56, 48, 120)), (0.5, (40, 32, 104)), (1, DEEP)], dh))
    rays = lines(shape, [[(86.5, -9), (82, -19.5)], [(83, -9), (79.5, -19)], [(79.5, -9.2), (77.2, -15.5)], [(75.5, -9.4), (74, -13)],
                         [(70, -9.5), (69, -12)], [(63, -9), (62, -11)], [(55, -8.4), (54, -10.2)], [(47, -7.2), (46, -8.6)]], 0.7)
    over(rays * d * 0.8, (128, 112, 184))
    rim = lines(shape, [[(89.5, -8), (87, -13.5), (83.5, -19.5), (80.8, -21.2)]], 0.8)
    over(rim * d, (150, 150, 216))
    for poly in (ANAL, DORS2, ANAL2, PELV):
        over(fill(shape, poly, smooth=False), NAVY)
    t = fill(shape, TAIL, smooth=False)
    over(t, grad([(0, DEEP), (0.5, NAVY), (1, (24, 48, 136))], np.clip(lx / 18, 0, 1)))
    over(lines(shape, [[(16.5, -2.4), (12.5, -6), (8.5, -10), (4.5, -13.6)], [(16.5, 2.4), (12.8, 6), (9, 10), (5, 13.6)]], 0.9) * t, (56, 136, 224))
    over(lines(shape, [[(14.5, -3.6), (10.5, -7.6)], [(14.5, 3.8), (11, 7.6)]], 0.6) * t, (144, 224, 248))

    # body
    tx = [p[0] for p in TOP]; top = PchipInterpolator(tx, [p[1] for p in TOP]); bot = PchipInterpolator(tx, [p[1] for p in BOT])
    xc = np.clip(lx, 16, 102)
    T, B = top(xc).astype(np.float32), bot(xc).astype(np.float32)
    outline = [(x, float(top(x))) for x in np.linspace(16, 102, 60)] + [(x, float(bot(x))) for x in np.linspace(102, 16, 60)]
    body = fill(shape, outline, smooth=False)
    u = np.clip((ly - T) / np.maximum(B - T, 0.5), 0, 1)
    col = grad([(0.0, DEEP), (0.10, (20, 24, 88)), (0.26, NAVY), (0.38, COBALT), (0.47, SKY), (0.52, WHITE), (0.60, SILVER),
                (0.78, WHITE), (0.90, (190, 202, 228)), (1.0, SHADE)], u)
    bars = (np.abs(((lx - 22) % 9.5) - 1.0) < 0.55) & (u > 0.10) & (u < 0.46) & (lx > 26) & (lx < 88)      # the pale bars a lit-up marlin shows
    col[bars] = col[bars] * 0.45 + np.array((88, 168, 240), np.float32) * 0.55
    cheek = np.clip((lx - 88) / 8, 0, 1)[..., None] * (u[..., None] > 0.42)
    col = col * (1 - cheek * 0.35) + np.array((216, 208, 236), np.float32) * cheek * 0.35
    over(body, col)
    over(lines(shape, [[(90.5, -6.5), (89.2, -2), (89.6, 2.5), (91.5, 5.6)]], 0.6) * body, (72, 80, 144))      # gill cover
    over(lines(shape, [[(30, 0.2), (50, 0.4), (70, 0.2), (86, -0.4)]], 0.5) * body * 0.7, WHITE)             # lateral line

    # bill and lower jaw
    bl = fill(shape, BILL, smooth=False)
    over(bl, grad([(0, DEEP), (0.55, (40, 48, 120)), (1, (136, 152, 200))], np.clip((ly + 3) / 4.2, 0, 1)))
    over(fill(shape, JAW, smooth=False), (176, 188, 220))
    # pectoral fin lies over the flank
    pf = fill(shape, PECT)
    over(pf, NAVY)
    over(lines(shape, [[(86, 2.2), (79, 4), (70, 7.4), (63.5, 10.6)]], 0.6) * pf, (64, 120, 208))
    # eye
    ex, ey = 96.3, -1.9
    r = np.hypot(lx - ex, ly - ey)
    over(np.clip((1.9 - r) * SS / 2, 0, 1), (232, 216, 168))
    over(np.clip((1.25 - r) * SS / 2, 0, 1), (8, 8, 24))
    over(np.clip((0.5 - np.hypot(lx - ex + 0.5, ly - ey + 0.5)) * SS / 2, 0, 1), (255, 255, 255))
    return rgb, al


def marlin(x, y, rot=-14.0, scale=0.92, flipy=False):
    """RGBA layer (H, W, 4 float): the tail notch (local 12.6, 0) lands on band (x, y)"""
    rgb, al = paint()
    a = np.deg2rad(rot); c, s = np.cos(a) * scale, np.sin(a) * scale
    px, py = (12.6 + X0) * SS, (0 + Y0) * SS
    M = np.float32([[c, -s, x * SS - (c * px - s * py)], [s, c, y * SS - (s * px + c * py)]])
    size = (W * SS, H * SS)
    pre = np.dstack([rgb * al[..., None], al])
    out = cv2.warpAffine(pre, M, size, flags=cv2.INTER_LINEAR)
    small = out.reshape(H, SS, W, SS, 4).mean((1, 3))
    alpha = small[..., 3]
    col = small[..., :3] / np.maximum(alpha[..., None], 1e-4)
    lay = np.zeros((H, W, 4)); lay[..., :3] = col; lay[..., 3] = np.where(alpha >= 0.42, 255, 0)
    return lay


if __name__ == '__main__':
    from marlin import paste_layer
    cv = Canvas(); paste_layer(cv, marlin(124, 38))
    show(cv, 'v_marlin2.png', 8, box=(96, 0, 256, 66))
