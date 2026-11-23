"""Make the English versions of the Japanese graphics into gfx_out/<path>; build.py writes them to the disc."""
import sys, os; sys.path.insert(0, 'tools')
from gfx import *
OUT = 'gfx_out'
def save(T, rel):
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True); T.save(p)

def namebg():
    T = Tim('files/TIM/NAMEBG.TIM'); a = T.rgb()
    for x0 in (0, 48):
        m = np.zeros(a.shape[:2], bool); m[233:247, x0 + 4:x0 + 43] = True
        a = inpaint(a, m, 4)
        from letters import render, style, paste
        m, _ = render('OK', 10, weight=0.27, swell=0.1, tilt=4, seed=4, spacing=1.2)
        art = style(m, (255, 255, 255), (206, 236, 240), (16, 40, 56), outline_w=1.0, shine_a=0.3, dark=0.2, shadow=(8, 20, 30), shadow_off=(1, 1))[0]
        rgba = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
        paste(rgba, art, x0 + 23, 240); a = rgba[..., :3]
    T.put(a, (0, 232, 96, 249))
    save(T, 'TIM/NAMEBG.TIM'); return T

def note():
    T = Tim('files/TIM/NOTE.TIM'); a = T.rgb().astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = ((R > G + 40) & (B > G + 20)) | ((R > 190) & (B > 190) & (G < 235) & (R > G + 15))
    m[:6] = False; m[50:] = False; m[:, :50] = False; m[:, 215:] = False
    m = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    a = inpaint(T.rgb(), m, 5)
    from letters import render, style_letters, paste
    m, _ = render('Fishing Note', 19, weight=0.3, swell=0.12, tilt=5, seed=2, spacing=0.3, per_letter=True, scale_var=0.06, space=4)
    art = style_letters(m, (255, 214, 255), (200, 70, 236), (50, 8, 72), shadow=(20, 0, 30), outline_w=1.2, shadow_off=(2, 2))[0]
    rgba = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
    paste(rgba, art, 128, 28); a = rgba[..., :3]
    T.put(a, (40, 4, 220, 52))
    save(T, 'TIM/NOTE.TIM'); return T

def dengon():
    T = Tim('files/TIM/DENGON.TIM'); a = T.rgb().astype(int)
    br = a.sum(2) / 3; g = a[..., 1] - (a[..., 0] + a[..., 2]) / 2
    m = np.zeros(br.shape, bool); m[8:30, 66:192] = True
    a = inpaint(T.rgb(), m, 5)
    from letters import render, paste
    m, _ = render('Family Message Board', 12, weight=0.17, swell=0.25, tilt=3, seed=11, spacing=1.1, space=4.5, bounce=0.05)
    rng = np.random.default_rng(5)
    grain = np.clip(0.55 + 0.45 * rng.random(m.shape), 0, 1)
    al = np.clip(m * grain * 1.15, 0, 1)
    sh = np.roll(np.roll(m, 1, 0), 1, 1) * 0.45
    art = np.zeros(m.shape + (4,))
    art[..., :3] = np.where(al[..., None] > 0, np.array([238, 246, 236]), np.array([16, 48, 30]))
    art[..., 3] = np.maximum(al, sh)
    art[..., :3] = np.where((al < sh)[..., None], np.array([16, 48, 30]), art[..., :3])
    rgba = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
    paste(rgba, art, 128, 18); a = rgba[..., :3]
    T.put(a, (8, 4, 248, 32))
    save(T, 'TIM/DENGON.TIM'); return T

def put_rgba(T, rgba, region):
    x0, y0, x1, y1 = region
    T.put(rgba[..., :3], region)
    tr = int(np.nonzero(T.raw == 0)[0][0])
    sub = rgba[y0:y1, x0:x1, 3] < 128
    T.idx[y0:y1, x0:x1][sub] = tr

def logo():
    copyright(); T = Tim('gfx_out/TIM/TITLE.TIM', 1)
    # the hand-drawn logo sheet (gfx/title_logo.png, or $LOGO) wins if present
    edits = [p for p in (os.environ.get('LOGO', ''), 'gfx/title_logo.png', 'art/title_logo.png') if p and os.path.exists(p)]
    if edits:
        # logo-only sheet: 256x144 = rows 64..207 of the page (the water strip and START button are not in it)
        e = np.array(Image.open(edits[0]).convert('RGBA'))
        page = np.dstack([T.rgb(), np.where(T.raw[T.idx] != 0, 255, 0).astype(np.uint8)])
        page[64:64 + e.shape[0], :e.shape[1]] = e[:144]
        put_rgba(T, page, (0, 64, 256, 208))
        save(T, 'TIM/TITLE.TIM'); return T
    rgba = np.dstack([T.rgb(), np.where(T.raw[T.idx] != 0, 255, 0).astype(np.uint8)])
    c = rgba[..., :3].astype(int); R, G, B = c[..., 0], c[..., 1], c[..., 2]
    def boxmask(m, x0, y0, x1, y1):
        b = np.zeros(m.shape, bool); b[y0:y1, x0:x1] = True; return m & b
    k = lambda n: np.ones((n, n), np.uint8)
    cyan = boxmask((B > 150) & (G > 110) & (R < B - 40), 0, 70, 90, 120)
    rgba[..., 3][boxmask(cv2.dilate(cyan.astype(np.uint8), k(7)) > 0, 0, 70, 90, 120)] = 0
    rgba[104:166, 38:222, 3] = 0
    tile = boxmask(((R > 190) & (G > 170) & (B < 200)) | ((R > 200) & (G > 120) & (B < 80)), 44, 170, 104, 202)
    tile = cv2.morphologyEx(tile.astype(np.uint8), cv2.MORPH_CLOSE, k(5))
    rgba[..., 3][boxmask(cv2.dilate(tile, k(5)) > 0, 44, 166, 104, 197)] = 0
    rgba[170:197, 100:208, 3] = 0
    rgba[160:204, 52:100, 3] = 0
    rgba[62:77, 55:83, 3] = 0
    im = Image.fromarray(rgba, 'RGBA')
    def layer(text, size, pos, grad, outline, stroke, shadow_off=(2, 2)):
        f = ImageFont.truetype(BOLD, size)
        return text_layer((256, 256), text, f, pos, None, shadow=(8, 8, 16), shadow_off=shadow_off, outline=outline,
                          grad=grad, anchor='mm', stroke=stroke)
    body = Image.new('RGBA', (256, 256), (0, 0, 0, 0)); bd = ImageDraw.Draw(body)
    bd.polygon([(16, 126), (28, 110), (78, 84), (88, 92), (84, 102), (36, 122)], fill=(36, 46, 120, 255))
    bd.line([(30, 118), (82, 92)], fill=(150, 164, 222, 255), width=3)
    under = Image.fromarray(rgba, 'RGBA'); body.alpha_composite(under); im = body
    from letters import render, style, style_letters, paste
    arr = np.array(im)
    m, _ = render('LEGEND', 13, weight=0.26, swell=0.1, tilt=3, seed=5, slant=0.28, spacing=1.0)
    paste(arr, style(m, (230, 255, 255), (30, 140, 230), (8, 20, 70), shadow=(0, 0, 20), outline_w=1.3, shadow_off=(1.5, 1.5))[0], 42, 88)
    m, _ = render('OF THE', 9, weight=0.28, swell=0.1, tilt=3, seed=6, slant=0.28, spacing=1.0, space=4)
    paste(arr, style(m, (230, 255, 255), (30, 140, 230), (8, 20, 70), shadow=(0, 0, 20), outline_w=1.2, shadow_off=(1, 1))[0], 46, 104)
    m, _ = render('SEA KING', 28, weight=0.36, tilt=7, seed=3, spacing=-0.2, per_letter=True, scale_var=0.08, bounce=0.08, space=4.5)
    paste(arr, style_letters(m, (250, 60, 10), (255, 235, 0), (60, 16, 0), shadow=(0, 0, 0), outline_w=2, shadow_off=(3, 3))[0], 131, 136)
    m, _ = render('to', 9, weight=0.28, swell=0.1, tilt=2, seed=8, slant=0.2)
    paste(arr, style(m, (255, 255, 255), (214, 226, 236), (26, 40, 60), outline_w=1.0, extrude=1, extrude_col=(110, 130, 150), shadow=(0, 0, 0), shadow_off=(2, 2))[0], 59, 186)
    m, _ = render('TREASURE ISLAND', 11, weight=0.26, swell=0.1, tilt=3, seed=9, spacing=0.9, space=4.5)
    paste(arr, style(m, (255, 255, 255), (214, 226, 236), (26, 40, 60), outline_w=1.0, extrude=2, extrude_col=(110, 130, 150), shadow=(0, 0, 0), shadow_off=(3, 3))[0], 145, 184)
    im = Image.fromarray(arr)
    put_rgba(T, np.array(im), (0, 64, 256, 210))
    save(T, 'TIM/TITLE.TIM'); return T

def copyright():
    T = Tim('files/TIM/TITLE.TIM', 0); a = T.rgb().astype(int)
    m = np.zeros(a.shape[:2], bool); m[212:229, 10:246] = a[212:229, 10:246].min(2) > 150
    m = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    a = inpaint(T.rgb(), m, 4)
    f = ImageFont.truetype(BOLD, 10)
    lay = text_layer((256, 240), '\u00a9 Victor Interactive Software 1999', f, (128, 221), (240, 244, 240), shadow=(10, 20, 30), anchor='mm')
    a = compose(a, lay)
    T.put(a, (0, 208, 256, 232))
    save(T, 'TIM/TITLE.TIM'); return T

# Shop sign plaques in the field tilesets (釣 tackle shop, 魚 fish dealer, 宿 inn): hand-pixelled 7 px capitals in the
# plaque's own cream on its dark board. Each plaque is widened to the full 16 px tile it sits in, so no other tile changes.
SIGN_GLYPHS = {
 'B': ['##.', '#.#', '#.#', '##.', '#.#', '#.#', '##.'],
 'A': ['.#.', '#.#', '#.#', '###', '#.#', '#.#', '#.#'],
 'I': ['#'] * 7,
 'T': ['###'] + ['.#.'] * 6,
 'F': ['###', '#..', '#..', '##.', '#..', '#..', '#..'],
 'S': ['.##', '#..', '#..', '.#.', '..#', '..#', '##.'],
 'H': ['#.#'] * 3 + ['###'] + ['#.#'] * 3,
 'N': ['#..#', '##.#', '##.#', '#.##', '#.##', '#..#', '#..#'],
}
SIGNS = [  # file, image, plaque box x0, y0, x1, y1 (inclusive, as drawn in the Japanese tiles), text
 ('MAP/BOHATE.TIM', 0, 145, 64, 158, 79, 'hook'),   # 釣 tackle/bait shop
 ('MAP/BOHATE.TIM', 0, 145, 96, 158, 111, 'fish'),   # 魚 fish shop
 ('MAP/BOHATE.TIM', 0, 209, 129, 222, 142, 'inn'),   # 宿
 ('MAP/ISO.TIM', 0, 97, 80, 110, 95, 'hook'),
 ('MAP/KAIGAN.TIM', 0, 17, 96, 30, 111, 'hook'),
 ('MAP/TAKARA.TIM', 0, 209, 128, 222, 143, 'hook'),
 ('MAP/TAKARA.TIM', 0, 193, 177, 206, 191, 'inn'),
]

# Series plaque art (Umi no Nushi / River King hacks: Hidden Lands tools/signs.py, Sea King field_signs.py):
# 魚 -> a fish, 釣 -> a hook, 宿 -> INN. 11x11, '#' = ink.
SIGN_ART = {
    'inn':  ["...........", "...........", "...........", "#.#..#.#..#", "#.##.#.##.#", "#.##.#.##.#",
             "#.#.##.#.##", "#.#.##.#.##", "#.#..#.#..#", "...........", "..........."],
    'hook': ["....###....", "....#.#....", "....###....", ".....#.....", ".....#.....", ".....#.....",
             "#....#.....", "##...#.....", "#....#.....", "#...#......", ".###......."],
    'fish': ["...........", "...........", "...........", "....###....", "#..######..", "##########.",
             "#######.###", "##########.", "#..######..", "....###....", "..........."],
}

def sign_plaque(a, x0, y0, x1, y1, text):
    from collections import Counter
    P = a[y0:y1 + 1, x0:x1 + 1].astype(int)
    inner = P[2:-2, 2:-2].reshape(-1, 3); lum = inner.sum(1)
    dark = np.array(Counter(map(tuple, inner[lum < np.percentile(lum, 50)])).most_common(1)[0][0])
    cream = inner[lum.argmax()]
    mids = inner[(lum > lum.min() + (lum.max() - lum.min()) * 0.45) & (lum < lum.max() - 60)]
    tan = mids.mean(0).astype(int) if len(mids) else (cream * 0.7).astype(int)
    tx0 = x0 & ~15; tx1 = tx0 + 15                     # widen to the whole tile
    h = y1 - y0 + 1; w = 16
    N = np.zeros((h, w, 3), int)
    N[:] = dark
    N[:, 0] = P[:, 0]; N[:, -1] = P[:, -1]
    mid_top = P[0, 1:-1]; mid_bot = P[-1, 1:-1]
    N[0, 1:-1] = np.resize(mid_top, (w - 2, 3)); N[-1, 1:-1] = np.resize(mid_bot, (w - 2, 3))
    N[1, 1:-1] = dark; N[-2, 1:-1] = dark
    if text in SIGN_ART:
        art = SIGN_ART[text]; ox = (w - 11) // 2 + 1; oy = (h - 11) // 2
        for r, row in enumerate(art):
            for k, ch in enumerate(row):
                if ch == '#': N[oy + r, ox + k] = cream
        a[y0:y1 + 1, tx0:tx1 + 1] = N
        return a
    gl = [SIGN_GLYPHS[c] for c in text]
    tw = sum(len(g[0]) for g in gl) + len(gl) - 1
    x = 1 + (w - 2 - tw) // 2; y = (h - 7) // 2
    for g in gl:
        for r, row in enumerate(g):
            for k, ch in enumerate(row):
                if ch != '#': continue
                below = r + 1 < 7 and g[r + 1][k] == '#'
                N[y + r, x + k] = cream if (below or r == 0) else tan   # stroke ends soften to tan, like the brushed kanji
        x += len(g[0]) + 1
    a[y0:y1 + 1, tx0:tx1 + 1] = N
    return a

def signs():
    from itertools import groupby
    T = None
    for (f, k), grp in groupby(SIGNS, key=lambda s: (s[0], s[1])):
        T = Tim('files/' + f, k); a = T.rgb().copy()
        regs = []
        for _, _, x0, y0, x1, y1, text in grp:
            a = sign_plaque(a, x0, y0, x1, y1, text); regs.append((x0 & ~15, y0, (x0 & ~15) + 16, y1 + 1))
        for r in regs: T.put(a, r)
        save(T, f)
        Image.fromarray(T.rgb()).save('view/gfx_sign_%s.png' % os.path.basename(f).split('.')[0])
    return T

def keikoku():
    """Development-disc warning screen (probably never shown in retail): white letters with a dark drop shadow."""
    T = Tim('files/TIM/KEIKOKU.TIM'); a = T.rgb()
    br = a.astype(int).min(2)
    m = np.zeros(br.shape, bool); m[81:128, 17:241] = True
    txt = (br > 150) & m
    txt = cv2.dilate(txt.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    a = inpaint(a, txt, 4)
    from letters import render
    rgba = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
    lines = ['This software (and the titles on it)', 'is still in development, so it will not', 'be exchanged even if problems occur.']
    for k, s in enumerate(lines):
        for cap in (7.5, 7, 6.5, 6):
            mk, base = render(s, cap, weight=0.26, spacing=1.0, tilt=0, bounce=0, seed=1, slant=0, swell=0, space=3.4, scale_var=0)
            xs = np.nonzero(mk.max(0) > 0.05)[0]
            if xs.max() - xs.min() <= 218: break
        top = int(round(88 + 16 * k - base + cap / 2)); left = 19 - xs.min()
        h, w = mk.shape
        for dy, dx, col in ((1, 1, (8, 16, 40)), (0, 0, (248, 248, 248))):
            for yy in range(h):
                Y = top + yy + dy
                if not 0 <= Y < rgba.shape[0]: continue
                X0 = max(0, left + dx); X1 = min(rgba.shape[1], left + dx + w)
                al = mk[yy, X0 - left - dx:X1 - left - dx, None]
                rgba[Y, X0:X1, :3] = np.clip(rgba[Y, X0:X1, :3] * (1 - al) + np.array(col) * al, 0, 255)
    T.put(rgba[..., :3], (0, 76, 256, 134))
    save(T, 'TIM/KEIKOKU.TIM'); return T

def credits():
    import credits as c; return c.all_pages()

ALL = ['namebg', 'note', 'dengon', 'logo', 'gover', 'credits', 'signs', 'keikoku']

# Faint banner "...復活中!..." in G_OVER.TIM: hand-pixelled block capitals in the original's
# yellow-to-orange fill and two-step blue outline. The second row is the first turned 180 degrees.
GOVER_GLYPHS = {
 'R': ['######.', '#######', '##...##', '##...##', '##...##', '##..###', '######.', '#####..', '##.##..', '##.###.', '##..##.', '##..###', '##...##', '##...##'],
 'E': ['######', '######', '##....', '##....', '##....', '##....', '#####.', '#####.', '##....', '##....', '##....', '##....', '######', '######'],
 'V': ['##...##'] * 7 + ['.##.##.'] * 3 + ['..###..'] * 3 + ['...#...'],
 'I': ['##'] * 14,
 'N': ['##...##', '###..##', '###..##', '###..##', '####.##', '####.##', '####.##', '##.####', '##.####', '##.####', '##..###', '##..###', '##..###', '##...##'],
 'G': ['.#####.', '#######', '##...##', '##...##', '##.....', '##.....', '##.....', '##..###', '##..###', '##...##', '##...##', '##...##', '#######', '.#####.'],
 '!': ['.##'] * 5 + ['##.'] * 5 + ['...', '...', '##.', '##.'],   # slanted, like the original's
}

def gover(text='REVIVING!'):
    T = Tim('files/TIM/G_OVER.TIM'); a = T.rgb(); al = T.raw[T.idx] != 0
    rgba = np.dstack([a, np.where(al, 255, 0)]).astype(np.uint8)
    old = rgba[211:229, :160].copy(); row = np.zeros_like(old)
    for src, dst in ((2, 2), (18, 16), (34, 30), (116, 120), (132, 134), (148, 148)):   # pull the dots out 2-4 px
        row[:, dst:dst + 9] = np.where(old[:, src:src + 9, 3:] > 0, old[:, src:src + 9], row[:, dst:dst + 9])
    from collections import Counter
    grad = [a[y, 44:110][(a[y, 44:110, 0] > 200) & (a[y, 44:110, 2] < 40)] for y in range(214, 227)]
    grad = [Counter(map(tuple, g)).most_common(1)[0][0] for g in grad]
    grad = grad[:1] + grad                          # 14 fill rows, 213-226 like the kanji
    x0, x1 = 40, 119
    w = sum(len(GOVER_GLYPHS[c][0]) for c in text) + 3 * (len(text) - 1)
    fill = np.zeros((18, x1 - x0), bool); x = (x1 - x0 - w + 1) // 2
    for c in text:
        g = GOVER_GLYPHS[c]
        for r, ln in enumerate(g):
            for k, ch in enumerate(ln):
                if ch == '#': fill[2 + r, x + k] = True
        x += len(g[0]) + 3
    d8 = lambda m: cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    d4 = lambda m: cv2.dilate(m.astype(np.uint8), np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], np.uint8)) > 0
    rim = d8(fill) & ~fill; edge = d8(fill | rim) & ~(fill | rim); corner = edge & ~d4(fill | rim)
    band = np.zeros((18, x1 - x0, 4), int)
    for r in range(2, 16): band[r][fill[r]] = list(grad[r - 2]) + [255]
    left = fill & ~np.roll(fill, 1, 1)             # soft bevel on the left edge of each stroke, as in the kanji
    band[left, :3] = (band[left, :3] * 0.6 + np.array([40, 88, 248]) * 0.4).astype(int)
    band[rim] = [40, 88, 248, 255]; band[edge] = [0, 0, 216, 255]; band[corner] = [0, 0, 160, 255]
    sub = row[:, x0:x1]; row[:, x0:x1] = np.where(band[..., 3:] > 0, band, sub)
    rgba[211:229, :160] = row
    rgba[235:253, 4:158] = rgba[211:229, 2:156][::-1, ::-1]
    put_rgba(T, rgba, (0, 208, 160, 256))
    save(T, 'TIM/G_OVER.TIM'); return T

if __name__ == '__main__':
    for fn in sys.argv[1:] or ALL:
        T = globals()[fn]()
        Image.fromarray(T.rgb()).save('view/gfx_%s.png' % fn)
