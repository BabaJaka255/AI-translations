"""Shop plaques in the village maps (MAP/*.TIM, 8bpp pages of 256x256).
Each 16x16 plaque is stored as two 8-row halves that sit in different places on the page (or on
the other page). Halves are found by matching against the KEIRYU / SANJYO originals, then the face
(x 3..13, y 3..13 of the plaque) is repainted with the series art: 魚 -> fish, 釣 -> hook, 宿 -> INN,
お (Sanjyo's eatery) -> EAT. Colours come from each half's own pixels, so every map keeps its tint."""
import sys, glob, os
import numpy as np
sys.path.insert(0, 'tools')
import tim

# 11x11 pictures (the Umi no Nushi art, first blank column dropped; see kawa-shizenha/tools/signs.py)
ART = {
    'inn':  ["...........", "...........", "...........", "#.#..#.#..#", "#.##.#.##.#", "#.##.#.##.#",
             "#.#.##.#.##", "#.#.##.#.##", "#.#..#.#..#", "...........", "..........."],
    'hook': ["....###....", "....#.#....", "....###....", ".....#.....", ".....#.....", ".....#.....",
             "#....#.....", "##...#.....", "#....#.....", "#...#......", ".###......."],
    'fish': ["...........", "...........", "...........", "....###....", "#..######..", "##########.",
             "#######.###", "##########.", "#..######..", "....###....", "..........."],
    'eat':  ["...........", "...........", "...........", "###.###.###", "#...#.#..#.", "##..###..#.",
             "#...#.#..#.", "###.#.#..#.", "...........", "...........", "..........."],
}
# original halves to match: name -> (file, page, x, y, which)
TEMPLATES = {
    'fish': (('KEIRYU.TIM', 0, 48, 200), ('KEIRYU.TIM', 0, 208, 160)),
    'hook': (('KEIRYU.TIM', 0, 64, 200), ('KEIRYU.TIM', 0, 224, 144)),
    'inn':  (('KEIRYU.TIM', 0, 80, 200), ('KEIRYU.TIM', 0, 240, 144)),
    'eat':  (('SANJYO.TIM', 1, 160, 216), ('SANJYO.TIM', 0, 32, 176)),
}
FACE = (3, 3, 13, 13)          # inclusive face rect inside the 16x16 plaque
THRESH = 0.7
FULL_THRESH = 0.8

def pages(d):
    o = 0; out = []
    while o < len(d) - 8:
        try: t = tim.parse(d, o)
        except Exception: break
        if t['bpp'] != 1: break
        out.append(t); o = t['end']
    return out

def lum_of(t):
    lut = np.array([tim.c15(v) for v in t['clut']['data'][0]], float)[:, :3]
    L = lut @ [.3, .59, .11]
    return L, L[tim.indices(t)]

_z = lambda a: (a - a.mean()) / (a.std() + 1e-6)

def templates(src):
    T = {}
    for name, halves in TEMPLATES.items():
        for half, (f, pi, x, y) in zip('tb', halves):
            T[name, half] = _z(lum_of(pages(src(f))[pi])[1][y:y + 8, x:x + 16])
    return T

def find(d, T):
    """[(page, x, y, name, half)] for every plaque half on this map's pages."""
    hits = []
    F = {n: _z(np.vstack([T[n, 't'], T[n, 'b']])) for n in ART}
    for pi, t in enumerate(pages(d)):
        L = lum_of(t)[1]; H, W = L.shape
        for y in range(0, H - 7, 8):
            for x in range(0, W - 15, 8):
                b = _z(L[y:y + 8, x:x + 16])
                c, key = max(((b * v).mean(), k) for k, v in T.items())
                if c > THRESH: hits.append((pi, x, y) + key)
        # whole plaques that don't sit on the 8-pixel grid (KAKOU's are at y=239)
        for y in range(H - 15):
            for x in range(W - 15):
                b = _z(L[y:y + 16, x:x + 16])
                c, name = max(((b * v).mean(), n) for n, v in F.items())
                if c > FULL_THRESH and (pi, x, y, name, 't') not in hits:
                    hits += [(pi, x, y, name, 't'), (pi, x, y + 8, name, 'b')]
    return hits

def rgb_of(t):
    return np.array([tim.c15(v) for v in t['clut']['data'][0]], float)

def face_mask(half):
    x0, y0, x1, y1 = FACE
    r0 = 0 if half == 't' else 8
    face = np.zeros((8, 16), bool)
    for yy in range(8):
        if y0 <= r0 + yy <= y1: face[yy, x0:x1 + 1] = True
    return face

def colours(idx, L, L_of, x, y, half):
    """(background, ink) indices of the original face: its dark ground and the brightest glyph colour."""
    face = face_mask(half)
    vals = idx[y:y + 8, x:x + 16][face]; lv = L[y:y + 8, x:x + 16][face]
    bg = np.bincount(vals[lv <= np.percentile(lv, 30)]).argmax()
    cnt = np.bincount(vals)
    ink = max((L_of[i], i) for i in np.nonzero(cnt >= 3)[0])[1]
    return bg, ink

def nearest(rgb, want):
    """CLUT index (not the transparent 0) closest to an RGB colour."""
    dist = ((rgb[1:, :3] - want[:3]) ** 2).sum(1)
    return 1 + int(dist.argmin())

def paint(idx, x, y, name, half, bg, ink):
    x0, y0, x1, y1 = FACE
    blk = idx[y:y + 8, x:x + 16]
    r0 = 0 if half == 't' else 8
    art = ART[name]
    for yy in range(8):
        py = r0 + yy
        if not (y0 <= py <= y1): continue
        for xx in range(x0, x1 + 1):
            blk[yy, xx] = ink if art[py - y0][xx - x0] == '#' else bg

def patch(d, T):
    d = bytearray(d)
    hits = find(bytes(d), T)
    pg = pages(bytes(d))
    idx = [tim.indices(t).copy() for t in pg]
    lum = [lum_of(t) for t in pg]
    rgb = [rgb_of(t) for t in pg]
    # both halves of a sign get the top half's colours (the halves' own glyph pixels differ in tone)
    ref = {}
    for pi, x, y, name, half in hits:
        if half == 't' and name not in ref:
            bg, ink = colours(idx[pi], lum[pi][1], lum[pi][0], x, y, half)
            ref[name] = (rgb[pi][bg], rgb[pi][ink])
    for pi, x, y, name, half in hits:
        bg, ink = colours(idx[pi], lum[pi][1], lum[pi][0], x, y, half)
        if name in ref:
            bg, ink = nearest(rgb[pi], ref[name][0]), nearest(rgb[pi], ref[name][1])
        paint(idx[pi], x, y, name, half, bg, ink)
    for pi, t in enumerate(pg):
        if not any(h[0] == pi for h in hits): continue
        words = (idx[pi][:, 0::2] | (idx[pi][:, 1::2] << 8)).astype('<u2')
        o = t['img']['off']
        d[o:o + words.nbytes] = words.tobytes()
    return bytes(d), hits

def build_all(src):
    """src(name) -> original bytes. Returns {name: (new bytes, hits)} for maps that changed."""
    T = templates(src)
    out = {}
    for f in sorted(os.path.basename(p) for p in glob.glob('files/MAP/*.TIM')):
        new, hits = patch(src(f), T)
        if hits: out[f] = (new, hits)
    return out

if __name__ == '__main__':
    from PIL import Image
    src = lambda f: open('files/MAP/' + f, 'rb').read()
    res = build_all(src)
    tiles = []
    for f, (new, hits) in res.items():
        print(f, [(p, x, y, n + h) for p, x, y, n, h in hits])
        po, pn = pages(src(f)), pages(new)
        for p, x, y, n, h in hits:
            a = np.array(tim.to_image(po[p]).convert('RGB'))[y:y + 8, x:x + 16]
            b = np.array(tim.to_image(pn[p]).convert('RGB'))[y:y + 8, x:x + 16]
            tiles.append(np.hstack([a, np.zeros((8, 2, 3), np.uint8), b]))
    sheet = np.vstack([np.vstack([t, np.full((2, 34, 3), 255, np.uint8)]) for t in tiles])
    Image.fromarray(sheet).resize((34 * 6, sheet.shape[0] * 6), Image.NEAREST).save('shots/signs.png')
