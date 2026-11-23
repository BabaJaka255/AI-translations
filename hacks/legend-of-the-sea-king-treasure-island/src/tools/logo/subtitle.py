"""'to TREASURE ISLAND': white block 'to', the palm, the island, two gold plaques (one per word, like 宝 and 島),
the coin and the fishing rod. All drawn on the pixel grid."""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from eng import *
from marlin import ORIG

F = {}
F['T'] = """
########
########
...##...
...##...
...##...
...##...
...##...
...##...
...##...
...##...
...##...
...##...
...##..."""
F['R'] = """
######..
#######.
##...###
##....##
##....##
##...###
#######.
######..
##.##...
##.###..
##..###.
##...###
##....##"""
F['E'] = """
#######
#######
##.....
##.....
##.....
######.
######.
##.....
##.....
##.....
##.....
#######
#######"""
F['A'] = """
...##...
..####..
..####..
.##..##.
.##..##.
.##..##.
##....##
##....##
########
########
##....##
##....##
##....##"""
F['S'] = """
.######.
########
##....##
##......
###.....
.#####..
..#####.
.....###
......##
##....##
##....##
########
.######."""
F['U'] = """
##....##
##....##
##....##
##....##
##....##
##....##
##....##
##....##
##....##
##....##
###..###
.######.
..####.."""
F['I'] = """
####
####
.##.
.##.
.##.
.##.
.##.
.##.
.##.
.##.
.##.
####
####"""
F['L'] = """
##.....
##.....
##.....
##.....
##.....
##.....
##.....
##.....
##.....
##.....
##.....
#######
#######"""
F['N'] = """
##....##
###...##
###...##
####..##
####..##
##.##.##
##.##.##
##..####
##..####
##...###
##...###
##....##
##....##"""
F['D'] = """
######..
#######.
##...###
##....##
##....##
##....##
##....##
##....##
##....##
##....##
##...###
#######.
######.."""
TO = {}
TO['t'] = """
..###...
..###...
..###...
########
########
..###...
..###...
..###...
..###...
..###...
..###...
..###..#
..######
...#####"""
TO['o'] = """
..#####..
.#######.
###...###
###...###
###...###
###...###
###...###
.#######.
..#####.."""


def grid(s):
    rows = [r for r in s.strip('\n').split('\n')]
    return np.array([[c == '#' for c in r] for r in rows], bool)


def word_mask(text, font=F, gap=2):
    gs = [grid(font[c]) for c in text]
    h = max(g.shape[0] for g in gs); w = sum(g.shape[1] for g in gs) + gap * (len(gs) - 1)
    m = np.zeros((h, w), bool); x = 0
    for g in gs:
        m[h - g.shape[0]:, x:x + g.shape[1]] = g; x += g.shape[1] + gap
    return m


def put(cv, m, x, y, col):
    h, w = m.shape
    sub = np.zeros((H, W), bool); sub[y:y + h, x:x + w] = m
    cv.put(sub, col); return sub


def plaque(cv, text, x, y, h=24, pad=4, rng=None):
    """gold tile with engraved dark letters; returns its width"""
    rng = rng or np.random.default_rng(5)
    m = word_mask(text)
    w = m.shape[1] + pad * 2 + 4
    yy, xx = np.mgrid[0:h, 0:w]
    t = yy / (h - 1.0) + rng.normal(0, 0.05, (h, w))
    face = ramp(t, [(0, (240, 232, 168)), (0.45, (240, 232, 168)), (0.7, (248, 216, 144)), (1, (240, 208, 128))])
    til = np.zeros((h, w, 3)); til[:] = face
    til[0, :] = (248, 224, 192); til[:, 0] = (248, 216, 144)             # lit lip, top and left
    til[1, 1:w - 2] = (56, 48, 40); til[1:h - 2, 1] = (56, 48, 40)        # dark inner frame under the lip
    til[2, 2:w - 3] = (184, 168, 136)
    til[h - 3, 2:w - 2] = (176, 168, 104)                                 # shaded foot of the face
    til[:, w - 2:] = (0, 0, 0); til[h - 2:, :] = (0, 0, 0)                # thick shadow side, right and bottom
    til[0, w - 2:] = (56, 48, 40)
    box = np.zeros((H, W), bool); box[y:y + h, x:x + w] = True
    full = np.zeros((H, W, 3)); full[y:y + h, x:x + w] = til
    cv.put(box, full)
    ly = y + (h - 2 - m.shape[0]) // 2 + 1; lx = x + pad + 1
    lm = np.zeros((H, W), bool); lm[ly:ly + m.shape[0], lx:lx + m.shape[1]] = m
    lit = shift(lm, 1, 1) & ~lm & box                                    # engraved: light catches the lower right wall
    cv.put(lit, (248, 248, 232))
    cv.put(lm, (24, 16, 16))
    top = lm & ~shift(lm, 0, 1)                                          # upper edge of each stroke a touch browner
    cv.put(top, (56, 48, 40))
    return w


def white_word(cv, text, x, y):
    """に向かって style: white blocks, grey foot, black shadow lower right, blue-grey rim upper left"""
    m = word_mask(text, TO, gap=2)
    full = np.zeros((H, W), bool); full[y:y + m.shape[0], x:x + m.shape[1]] = m
    sh = shift(full, 1, 1) | shift(full, 2, 2) | shift(full, 2, 1) | shift(full, 1, 2)
    solid = full | sh
    ring = ndi.binary_dilation(solid, np.ones((3, 3), bool)) & ~solid
    lower = ring & (shift(solid, 1, 0) | shift(solid, 0, 1) | shift(solid, 1, 1))
    cv.put(ring, (72, 120, 152))
    cv.put(ring & shift(full, 0, -1), (192, 208, 216))
    cv.put(lower, (8, 40, 48))
    cv.put(sh, (0, 0, 0))
    cv.put(full, (248, 248, 248))
    foot = full & ~shift(full, 0, -1)                                    # bottom row of each stroke
    cv.put(foot, (192, 192, 192))
    side = full & ~shift(full, -1, 0) & ~foot
    cv.put(side, (216, 216, 216))
    return m.shape[1]


def palm(cv, x, y):
    """the original palm and rock (original x 32..49, rows 108..138), pasted with its left edge at x, top at y"""
    src = ORIG[108:139, 32:50].copy()
    h, w = src.shape[:2]
    m = np.zeros((H, W), bool); col = np.zeros((H, W, 3))
    m[y:y + h, x:x + w] = src[..., 3] > 0; col[y:y + h, x:x + w] = src[..., :3]
    cv.put(m, col)


def coin(cv, x, y):
    src = ORIG[124:134, 63:72].copy()
    c = src[..., :3].astype(int)
    gold = (c[..., 0] > 150) & (c[..., 1] > 90) & (c[..., 1] < 200) & (c[..., 2] < 80)
    gold = ndi.binary_closing(gold, np.ones((3, 3), bool))
    ring = ndi.binary_dilation(gold, np.ones((3, 3), bool)) & ~gold
    h, w = gold.shape
    m = np.zeros((H, W), bool); col = np.zeros((H, W, 3))
    m[y:y + h, x:x + w] = gold; col[y:y + h, x:x + w] = src[..., :3]
    r = np.zeros((H, W), bool); r[y:y + h, x:x + w] = ring
    cv.put(r, (48, 16, 0)); cv.put(m, col)


def island(cv, x0, x1, top, base, peak=None):
    """green hill behind the plaques: a low dome from x0 to x1 whose crown reaches row `top`"""
    yy, xx = np.mgrid[0:H, 0:W]
    cx = peak if peak is not None else (x0 + x1) / 2
    rx = np.where(xx < cx, cx - x0, x1 - cx)
    e = ((xx - cx) / rx) ** 2 + ((yy - base) / (base - top + 0.5)) ** 2
    m = (e <= 1) & (yy <= base)
    cv.put(m, (0, 120, 72))
    cv.put(m & (e < 0.80) & (yy >= top + 1) & (yy < top + 5) & (np.abs(xx - cx) < rx * 0.55), (24, 144, 72))
    cv.put(m & (yy >= top + 2) & (yy < top + 4) & (xx > cx - 14) & (xx < cx + 8), (16, 160, 88))
    return m


def rod(cv, x0, x1, y):
    """fishing rod lying flat: cork grip at the left, tip at the right; rows y-1..y+1"""
    grip = 10
    for x in range(x0, x1 + 1):
        if x < x0 + grip:
            cv.rgb[y - 1, x], cv.rgb[y, x], cv.rgb[y + 1, x] = (240, 216, 200), (176, 136, 144), (88, 56, 48)
            cv.a[y - 1:y + 2, x] = True
            continue
        k = (x - x0 - grip) / max(1, x1 - x0 - grip)
        seg = ((x - x0) // 14) % 2
        cv.rgb[y - 1, x] = (160, 184, 200) if seg == 0 else (72, 120, 152)
        cv.rgb[y, x] = (248, 248, 248) if seg == 0 else (192, 192, 192)
        cv.a[y - 1:y + 1, x] = True
        if k < 0.55:
            cv.rgb[y + 1, x] = (88, 80, 64); cv.a[y + 1, x] = True
    for x in (x0 + grip, x0 + grip + 1):                                  # reel seat
        cv.rgb[y - 2:y + 2, x] = (168, 104, 176); cv.a[y - 2:y + 2, x] = True
    gx = x0 + grip + 22
    while gx < x1 - 4:                                                    # line guides
        cv.rgb[y - 2, gx] = (192, 208, 216); cv.rgb[y - 1, gx] = (248, 248, 248); cv.a[y - 2, gx] = True
        gx += 26
    cv.rgb[y - 1, x1] = (192, 208, 216); cv.rgb[y, x1] = (192, 192, 192)


def draw(cv=None, x=34, y=109):
    cv = cv or Canvas()
    tx = x + white_word(cv, 'to', x, y + 6) + 4
    px = tx
    t1 = px + 19
    m1 = word_mask('TREASURE').shape[1] + 12; m2 = word_mask('ISLAND').shape[1] + 12
    end = t1 + m1 + 2 + m2
    island(cv, px + 10, t1 + m1 + 26, y - 6, y + 25, peak=t1 + 40)
    ys = slice(y + 24, y + 26)
    cv.rgb[ys, px + 4:t1 + 6] = (80, 40, 24); cv.a[ys, px + 4:t1 + 6] = True
    cv.rgb[ys, t1 + 6:end + 3] = (0, 120, 72); cv.a[ys, t1 + 6:end + 3] = True
    palm(cv, px, y - 1)
    w1 = plaque(cv, 'TREASURE', t1, y)
    w2 = plaque(cv, 'ISLAND', t1 + w1 + 2, y)
    coin(cv, t1 - 5, y + 14)                           # the coconut, fallen at the foot of the palm
    rod(cv, end + 6 - 112, end + 6, y + 28)            # about the length of the original rod, under the right half
    return cv


if __name__ == '__main__':
    cv = draw()
    show(cv, 'v_sub.png', 6, box=(20, 98, 250, 144))
