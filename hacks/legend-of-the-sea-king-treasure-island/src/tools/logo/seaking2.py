"""'The Sea King', version 3: the lettering of the localized logos.
'Sea' is traced from the unreleased Sea King GB title screen (ref_sea.png), 'King' from the Legend of the River King GB
box logo (ref_river.png), and the small 'The' is brush strokes followed over the box logo's 'The'.
Layout coords = pixels of the box-logo crop; band = ORG + S * layout."""
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
from eng import *

S_ = 0.4075                    # layout -> band scale
ORG = (35.3, 34.2)             # band position of layout (0, 0)
FATTEN = {'King': 2}           # traced letters lose their black edge line in the trace; give that weight back
LXF = Xf(ORG[0], ORG[1], 0, S_, S_)


def box_warm():
    a = np.array(Image.open('ref_river.png').convert('RGB')).astype(int)[110:300, 40:650]
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    return (R > 185) & (B < 130) & (R - B > 90) & (G < 250)


def warp(src, x0, y0, x1, y1, dx, dy, into, sc=1.0):
    """paste a float mask (box-crop piece x0..x1, y0..y1, moved by dx, dy in layout px) into the hi-res band mask;
    sc enlarges the piece about the middle of its right edge"""
    k = S_ * SS * sc
    ax, ay = x1 + dx, (y0 + y1) / 2 + dy                       # anchor in layout
    tx = (ORG[0] + S_ * ax) * SS - k * (x1 - x0); ty = (ORG[1] + S_ * ay) * SS - k * (y1 - y0) / 2
    M = np.float32([[k, 0, tx], [0, k, ty]])
    out = cv2.warpAffine(src.astype(np.float32), M, (W * SS, H * SS), flags=cv2.INTER_CUBIC)
    np.maximum(into, out, out=into)


# traced pieces from the box logo: name -> (source box x0, y0, x1, y1), layout shift dx, dy
PIECES = {'King': ((356, 8, 598, 164), -72, 0)}
SCALE = {'King': 1.0}

# 'The' is too small at this size for a pixel trace to stay legible (18 px tall), so its brush strokes are followed
# by hand over the box logo's 'The': (x, y, radius) in box-crop pixels.
THE = [
    [(11, 80, 2.6), (22, 76, 3.0), (33, 72, 3.0)],                                   # T bar
    [(25, 81, 3.4), (24, 92, 4.0), (25, 104, 4.2), (27, 111, 3.2)],                  # T stem
    [(27, 111, 3.0), (33, 105, 2.2), (38, 100, 1.6)],                                # its flick
    [(40, 70, 3.0), (41, 84, 3.6), (42, 98, 3.8), (43, 107, 3.0)],                   # h stem
    [(44, 96, 2.4), (50, 89, 3.0), (55, 88, 3.4), (57, 97, 3.6), (57, 106, 3.0)],    # h hump
    [(65, 94, 2.2), (72, 89, 2.4), (77, 83, 2.6), (73, 78, 2.8), (66, 83, 3.4), (63, 93, 3.8), (67, 102, 3.6), (75, 102, 2.8), (81, 96, 2.0)],
]
THE_AT = dict(anchor=(86, 89), sc=1.15, dx=-11, dy=8, weight=0.74)


def the_layout(pts):
    p = np.array(pts, float); ax, ay = THE_AT['anchor']; k = THE_AT['sc']
    q = p.copy()
    q[:, 0] = ax + k * (p[:, 0] - ax) + THE_AT['dx']; q[:, 1] = ay + k * (p[:, 1] - ay) + THE_AT['dy']
    if p.shape[1] > 2: q[:, 2] = p[:, 2] * k * THE_AT['weight']
    return q

# 'Sea' comes from the unreleased Sea King GB title screen (ref_sea.png, a blurry capture, so its outline is traced
# and smoothed). GB capture pixel (gx, gy) of the 660x205 crop -> layout: K's left edge and top are the anchors.
GBF = 0.955
def gb_to_layout(gx, gy):
    return 292 + (gx - 355) * GBF, 14 + (gy - 10) * GBF


def gb_sea():
    """'Sea' at capture resolution: the silhouette (float-able bool) and the gaps inside it. A gap is anything the
    Game Boy art leaves dark or white inside the letters: the eye and mouth of the e, the slit of the a, the shadow
    lines where S meets e and e meets a."""
    from trace import gb_mask
    m = gb_mask()
    yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    sea = (xx >= 100) & ~((xx < 114) & (yy < 126)) & ~((xx > 312) & (xx < 372) & (yy > 132))
    if not GB_KING:
        sea &= (xx < 347) & ~((xx > 338) & (yy > 60))
    m = m & sea
    closed = ndi.binary_closing(m, iterations=6)
    holes = closed & ~m
    lab, n = ndi.label(holes)
    area = ndi.sum(holes, lab, range(1, n + 1)) if n else []
    gaps = np.isin(lab, [i + 1 for i, t in enumerate(area) if t >= 14])
    for x0, y0, x1, y1 in GB_NOT_GAPS:
        gaps &= ~((xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1))
    return closed, gaps


GB_NOT_GAPS = [(318, 94, 336, 110), (148, 76, 162, 90)]     # a glint pixel on the a; a corner of the S


def warp_gb(src, sigma):
    k = S_ * SS * GBF
    lx, ly = gb_to_layout(0, 0)
    M = np.float32([[k, 0, (ORG[0] + S_ * lx) * SS], [0, k, (ORG[1] + S_ * ly) * SS]])
    f = cv2.GaussianBlur(src.astype(np.float32), (0, 0), sigma)
    return cv2.warpAffine(f, M, (W * SS, H * SS), flags=cv2.INTER_CUBIC)


SEA_SMOOTH, SEA_GAP, SEA_SLIM = 3.0, 0.45, 2
GB_KING = False                # take 'King' from the Game Boy logo too (False: from the box logo)
STROKES = {}


def masks():
    """hi-res fill mask (uint8) and ink (thin dark streaks) mask for the whole of 'The Sea King'"""
    warm = box_warm()
    closed = ndi.binary_closing(warm, iterations=3)
    holes = closed & ~warm
    # a hole wider than a brush streak is a real counter (the eye of the e, the bowl of the g): leave it open
    lab, n = ndi.label(holes)
    thick = ndi.maximum(ndi.distance_transform_edt(holes), lab, range(1, n + 1)) if n else []
    real = np.isin(lab, [i + 1 for i, t in enumerate(thick) if t > 2.3])
    slit = holes & ~real
    closed = closed & ~real
    fill = np.zeros((H * SS, W * SS), np.float32); ink = np.zeros_like(fill)
    for name, ((x0, y0, x1, y1), dx, dy) in PIECES.items():
        if GB_KING and name == 'King': continue
        f = cv2.GaussianBlur(ndi.binary_dilation(closed, iterations=FATTEN[name])[y0:y1, x0:x1].astype(np.float32), (0, 0), 0.8)
        i = cv2.GaussianBlur(slit[y0:y1, x0:x1].astype(np.float32), (0, 0), 0.6)
        warp(f, x0, y0, x1, y1, dx, dy, fill, SCALE[name]); warp(i, x0, y0, x1, y1, dx, dy, ink, SCALE[name])
    sea, gaps = gb_sea()
    if SEA_SLIM: sea = ndi.binary_erosion(sea, iterations=SEA_SLIM)
    sf = (warp_gb(sea, SEA_SMOOTH) >= 0.5) & ~(warp_gb(gaps, 1.3) >= SEA_GAP)
    np.maximum(fill, sf.astype(np.float32), out=fill)
    fill = (fill >= 0.5).astype(np.uint8) * 255
    ink = np.clip(ink * 255 * 1.6, 0, 255).astype(np.uint8)
    ink = np.maximum(ink, (line_mask([gb_band(l) for l in SEA_INK], 0.7) * 0.8).astype(np.uint8))
    for name, g in STROKES.items():
        paths = []
        for pts in g['strokes']:
            p = stroke_path(LXF, pts); paths.append(p); stamp(fill, p)
        for si, end, teeth, slit_len in g.get('kas', []):
            p = paths[si]
            a, b = (p[0], p[4]) if end == 0 else (p[-1], p[-5])
            teeth = [(o, l * S_, w * S_) for o, l, w in teeth]
            kasure(fill, a[:2], a[:2] - b[:2], a[2], teeth, slit_len * S_, gap=0.5)
        lines = [offset_line(paths[si], t0, t1, side, inset * S_) for si, t0, t1, side, inset in g.get('ink', [])]
        ink = np.maximum(ink, line_mask(lines, 0.75))
    the = hi()
    for pts in THE:
        stamp(the, stroke_path(LXF, [tuple(q) for q in the_layout(pts)]))
    # 'The' tucks in behind the S, with a hairline between them
    r = int(round(1.4 * SS)); near = cv2.dilate((sf * 255).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    the[near > 0] = 0
    fill = np.maximum(fill, the)
    return fill, ink, the


# glints, layout coords: hand-placed short strokes on the upper-left shoulders, like ぬし釣り
GLINTS = [
    ([(319.1, 29.4), (314.7, 46.9), (310.3, 66.6), (307.1, 82.0)], True),
    ([(366.3, 22.8), (359.7, 35.9), (352.0, 49.1)], True),
    ([(337.8, 95.1), (346.5, 108.3), (355.3, 119.3)], False),
    ([(387.1, 16.2), (389.3, 25.0)], True),
    ([(389.3, 57.9), (386.0, 73.2), (383.8, 88.6)], False),
    ([(415.6, 64.4), (412.3, 79.8), (410.1, 95.1)], False),
    ([(436.4, 66.6), (441.9, 75.4), (441.9, 88.6)], True),
    ([(463.9, 79.8), (460.6, 92.9), (462.8, 106.1)], False),
    ([(493.5, 72.1), (504.4, 68.8), (513.2, 65.5)], False),
    ([(484.7, 143.4), (491.3, 132.4), (495.6, 119.3)], True),
]


# 'Sea' highlights and dry-brush streaks, in Game Boy capture coords (same frame as gb_sea)
SEA_GLINTS = [
    ([(173, 26), (162, 37), (151, 50), (141, 63)], True),       # S top slab
    ([(127, 82), (126, 92), (130, 101)], False),                # S belly
    ([(166, 124), (152, 136), (138, 148), (127, 158)], True),   # S tail
    ([(223, 61), (213, 71), (208, 84)], True),                  # e
    ([(206, 110), (212, 118)], False),
    ([(306, 50), (293, 60), (283, 72), (275, 86)], True),       # a bowl
    ([(329, 82), (327, 95), (329, 107)], False),                # a stem
]
SEA_INK = [
    [(188, 22), (180, 35)], [(194, 29), (187, 41)],             # S: split start of the stroke
    [(172, 52), (160, 68), (152, 80)],
    [(178, 120), (164, 136), (154, 147)],
    [(119, 168), (129, 157)], [(127, 174), (139, 161)],         # S: split end of the tail
    [(246, 57), (256, 67)], [(222, 122), (240, 125), (254, 119)],   # e
    [(319, 49), (331, 56)], [(280, 112), (292, 121)], [(339, 104), (337, 120)],   # a
]


def gb_band(pts):
    p = np.array(pts, float)
    lx, ly = gb_to_layout(p[:, 0], p[:, 1])
    return np.column_stack([ORG[0] + S_ * lx, ORG[1] + S_ * ly])


def draw(cv=None, table=RAMP, top=40, bot=99, glints=None):
    cv = cv or Canvas(); rng = np.random.default_rng(7)
    fill, ink, the_hi = masks()
    cov = down(fill); inkc = down(ink)
    gl = GLINTS if glints is None else glints
    hl = None
    if gl:
        gl = [(np.array(g[0], float) * S_ + ORG, g[1]) for g in gl] + [(gb_band(g[0]), g[1]) for g in SEA_GLINTS]
        thin = line_mask([g[0] for g in gl], 0.9)
        fat = line_mask([g[0][1:-1] if len(g[0]) > 3 else g[0] for g in gl if g[1]], 1.6) if any(g[1] for g in gl) else thin
        hl = down(np.maximum(thin, fat))
    f = bubble(cv, cov, top, bot, None, rng, table=table)
    # 'The' sits mid-height: give it its own full gradient like the reference does
    the = (down(the_hi) >= 0.5) & f
    ys = np.nonzero(the.any(1))[0]
    yy = np.repeat(np.arange(H)[:, None], W, 1).astype(float)
    ty0, ty1 = ys.min() - 1, ys.max() + 2
    cv.put(the, ramp((yy - ty0) / (ty1 - ty0) + rng.normal(0, 0.012, f.shape), table))
    cv.blend(np.where(f, np.clip(inkc * 1.1, 0, 1), 0), np.array([24, 0, 0.0]))
    if hl is not None:
        cv.blend(np.where(f, np.clip(hl * 1.25, 0, 1), 0) * (1 - np.clip(inkc * 2, 0, 1)), np.array([255, 255, 236.0]))
    return cv


if __name__ == '__main__':
    from PIL import ImageDraw
    cv = draw()
    show(cv, 'v_sk2.png', 6, box=(0, 26, 256, 112)); show(cv, 'v_sk2_small.png', 2, box=(0, 26, 256, 112))
    im = Image.open('v_sk2.png'); d = ImageDraw.Draw(im)
    for x in range(0, 256, 10): d.line([(x * 6, 0), (x * 6, im.size[1])], fill=(255, 255, 255, 60)); d.text((x * 6 + 2, 2), str(x), fill=(0, 255, 255))
    for y in range(30, 112, 10): d.line([(0, (y - 26) * 6), (im.size[0], (y - 26) * 6)], fill=(255, 255, 255, 60)); d.text((2, (y - 26) * 6 + 2), str(y), fill=(0, 255, 255))
    im.save('v_sk2_grid.png')
