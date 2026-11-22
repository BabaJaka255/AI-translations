"""Redraw the art with Japanese lettering in English.

Reads gfx/orig/art/<sheet>.png, draws the English lettering (tools/letter.py
for the hand lettering, tools/sheet.py for tile painting) and writes
gfx/edit/art/<sheet>.png, which `rhtk build` reinserts.

    python3 tools/make_art.py            # every item
    python3 tools/make_art.py labels     # just one
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import letter as L
from sheet import Sheet, styled, shift

ITEMS = {}
def item(fn):
    ITEMS[fn.__name__] = fn
    return fn

def grid(text):
    """Pixel grid from a string: '.' = 0, 1-3 = that value, other = ink(1)."""
    rows = [r for r in text.strip('\n').split('\n')]
    return rows

def paint_grid(sh, rows, x0, y0, cmap, clip=None):
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c in cmap:
                x, y = x0 + i, y0 + j
                if clip and not clip(x, y):
                    continue
                sh.put(x, y, cmap[c])

# ---------------------------------------------------------------- illness
@item
def illness():
    """Cough marks ケン -> KOFF. Each mark is a 2x4-tile block; cells (1,1) and
    (0,3) are the screen's shared blank tile, so ink avoids them."""
    sh = Sheet('illness_picture')
    A = ["........", ".RR..RR.", ".RR.RR..", ".RRRR...", "RRRR....", "RR.RR...", "RR..RR..", "RR...RR."]
    B = ["........", "..RRR...", ".RR..RR.", ".RR..RR.", "RR..RR..", "RR..RR..", ".RRRR...", "........"]
    C = ["........", "...RRRRR", "..RR....", "..RR....", "..RRRR..", ".RR.....", ".RR.....", "........"]
    E = ["....RRRR", "...RR...", "...RR...", "..RR....", "..RRRRR.", "..RR....", ".RR.....", ".RR....."]
    F = [".RR.....", "RR......", "RR......", "R.......", "........", "........", "........", "........"]
    W = sh.w // 8
    for cell, t in ((A, 3), (B, 4), (C, 6), (E, 11), (F, 18)):
        pass
    blocks = {3: A, 4: B, 6: C, 10: ["........"] * 8, 11: E, 18: F}
    for t, rows in blocks.items():
        tx, ty = (t % W) * 8, (t // W) * 8
        for j in range(8):
            for i in range(8):
                sh.put(tx + i, ty + j, 2 if rows[j][i] == 'R' else 0)
    sh.save()

# ---------------------------------------------------------------- event labels
# Block capitals for the labels: 11 rows, 2px stems.
BLOCK = {
 'A': [".###.","##.##","##.##","##.##","##.##","#####","##.##","##.##","##.##","##.##","##.##"],
 'B': ["####.","##.##","##.##","##.##","####.","##.##","##.##","##.##","##.##","##.##","####."],
 'C': [".###.","##.##","##...","##...","##...","##...","##...","##...","##...","##.##",".###."],
 'D': ["####.","##.##","##.##","##.##","##.##","##.##","##.##","##.##","##.##","##.##","####."],
 'E': ["#####","##...","##...","##...","####.","##...","##...","##...","##...","##...","#####"],
 'G': [".###.","##.##","##...","##...","##...","##.##","##.##","##.##","##.##","##.##",".####"],
 'H': ["##.##","##.##","##.##","##.##","#####","##.##","##.##","##.##","##.##","##.##","##.##"],
 'I': ["##"]*11,
 'K': ["##..#","##.##","##.#.","####.","###..","###..","####.","##.#.","##.##","##.##","##..#"],
 'N': ["##..##","###.##","###.##","######","##.###","##.###","##..##","##..##","##..##","##..##","##..##"],
 'O': [".###."]+["##.##"]*9+[".###."],
 'R': ["####.","##.##","##.##","##.##","####.","###..","##.#.","##.##","##.##","##.##","##.##"],
 'S': [".###.","##.##","##...","##...",".##..","..##.","...##","...##","...##","##.##",".###."],
 'T': ["######"]+["..##.."]*10,
 'U': ["##.##"]*9+["##.##",".###."],
 '!': ["##"]*8+["..","##","##"],
}
def block_word(word, gap=1):
    rows = [""] * 11
    for k, ch in enumerate(word):
        g = BLOCK[ch]
        for j in range(11):
            rows[j] += ("." * gap if k else "") + g[j]
    return [[1 if c == '#' else 0 for c in r] for r in rows]

@item
def labels():
    """Two-kanji labels -> one English word per 32x16 row. Needs the hacks.ips
    change that moves the two halves together (tools/make_hacks.py)."""
    sh = Sheet('event_labels')
    words = ['BIRTH', 'DEATH', 'OUCH!', 'SICK', 'GONE!']
    for k, wd in enumerate(words):
        y0 = 16 * k
        sh.fill(0, y0, 32, y0 + 16, 0)
        m = block_word(wd)
        w, h = len(m[0]), len(m)
        x = (32 - w) // 2
        y = y0 + 2
        def grad(px, py, top=y):
            r = py - top
            return 2 if r < 3 or r >= 9 else 1
        styled(sh, m, x, y, grad, outline=3)
    sh.save()

# ---------------------------------------------------------------- ACCIDENT banner
def extrude(sh, mask, x0, y0, fill, edge, depth_col, depth=3, clip=None):
    """Chunky title lettering: dark extrusion down-right, light edge, fill."""
    big = L.dilate(mask, 1)
    for k in range(depth, 0, -1):
        sh.paint(big, x0 - 1 + k, y0 - 1 + k, depth_col, clip)
    sh.paint(big, x0 - 1, y0 - 1, edge, clip)
    sh.paint(mask, x0, y0, fill, clip)

CHUNK = {
 'A': ["..###..",".#####.",".##.##.","###.###","###.###","#######","#######","###.###","###.###","###.###"],
 'C': [".######","#######","###....","###....","###....","###....","###....","###....","#######",".######"],
 'I': ["###"]*10,
 'D': ["######.","#######","###.###","###.###","###.###","###.###","###.###","###.###","#######","######."],
 'E': ["#######","#######","###....","###....","######.","######.","###....","###....","#######","#######"],
 'N': ["###..###","####.###","####.###","########","########","###.####","###.####","###..###","###..###","###..###"],
 'T': ["#######","#######"]+["..###.."]*8,
 '!': ["###"]*7+["...","###","###"],
 'H': ["###.###"]*4+["#######"]*2+["###.###"]*4,
 'M': ["###...###","####.####","#########","###.#.###"]+["###...###"]*6,
 'S': [".######","#######","###....","###....","######.",".######","....###","....###","#######","######."],
 'R': ["######.","#######","###.###","###.###","#######","######.","###.###","###.###","###.###","###.###"],
 'L': ["###...."]*8+["#######"]*2,
 'U': ["###.###"]*8+["#######",".#####."],
 'B': ["######.","#######","###.###","###.###","######.","#######","###.###","###.###","#######","######."],
 ' ': ["...."]*10,
}
def chunk_word(word, yscale=2, gap=2, bounce=None, slant=6, xscale=1.0):
    """Big block capitals: rows doubled, letters bounced up/down, rows sheared
    1px right for every `slant` rows above the baseline (italic)."""
    bounce = bounce or [0] * len(word)
    def scaled(g):
        rows = [g[min(9, int(j * 10 / (10 * yscale)))] for j in range(int(round(10 * yscale)))]
        wn = int(round(len(g[0]) * xscale))
        return [''.join(r[min(len(r) - 1, int(i * len(r) / wn))] for i in range(wn)) for r in rows]
    glyphs = [scaled(CHUNK[c]) for c in word]
    H = int(round(10 * yscale)) + max(bounce) - min(bounce)
    xs, x = [], 0
    for g in glyphs:
        xs.append(x); x += len(g[0]) + gap
    W = x - gap + H // slant + 1
    m = [[0] * W for _ in range(H)]
    for g, x0, b in zip(glyphs, xs, bounce):
        top = b - min(bounce)
        for j, r in enumerate(g):
            y = top + j
            sx = (H - 1 - y) // slant
            for i, c in enumerate(r):
                if c == '#':
                    m[y][x0 + i + sx] = 1
    return m

@item
def banner():
    """アクシデント -> ACCIDENT! (80x48 of 8x16 sprites: white edge, light
    blue fill, dark blue extrusion like the original)."""
    sh = Sheet('accident_banner')
    sh.fill(0, 0, 80, 48, 0)
    m = chunk_word("ACCIDENT", yscale=3, bounce=[0, 4, 1, 5, 0, 4, 1, 0], slant=999)
    w, h = len(m[0]), len(m)
    x = max(1, (80 - 4 - w) // 2)
    y = max(1, (48 - 4 - h) // 2)
    extrude(sh, m, x, y, 2, 1, 3, depth=3)
    sh.save()
    return w, h

# ---------------------------------------------------------------- title logo
SCRATCH = os.environ.get('HC_STATES', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gfx', 'states', 'boot'))

@item
def title():
    """ハムスター倶楽部 -> HAMSTER CLUB on the title band (BG rows 1-6).
    Blank band cells use one shared tile, so ink is kept out of them."""
    from screen import Screen
    t88, t90 = Sheet('title_logo_bg8800'), Sheet('title_logo_bg9000')
    scr = Screen(os.path.join(SCRATCH, 'boot_1080.state'), {'t88': (t88, 0x8800, 0), 't90': (t90, 0x9000, 0)})
    r0, c0, r1, c1 = 1, 0, 7, 20
    users = scr.users()
    region = {(r, c) for r in range(r0, r1) for c in range(c0, c1)}
    def free(x, y):  # canvas coords
        cell = (r0 + y // 8, c0 + x // 8)
        key = scr.cells.get(scr.visible(*cell))
        return key is not None and all(u in region for u in users[key[:2]]) and len(users[key[:2]]) == 1
    g = [[0] * ((c1 - c0) * 8) for _ in range((r1 - r0) * 8)]
    class Canvas:  # Sheet-like painter over the grid
        w, h = len(g[0]), len(g)
        def put(self, x, y, v):
            if 0 <= x < self.w and 0 <= y < self.h and free(x, y): g[y][x] = v
        def paint(self, mask, x0, y0, v, clip=None):
            for j, row in enumerate(mask):
                for i, m in enumerate(row):
                    if m: self.put(x0 + i, y0 + j, v(x0 + i, y0 + j) if callable(v) else v)
    cv = Canvas()
    m = chunk_word("HAMSTER CLUB", yscale=2.0, xscale=1.3, gap=2, bounce=[1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1], slant=999)
    w, h = len(m[0]), len(m)
    x = max(17, (cv.w - w - 4) // 2 + 1)
    y = 9
    # dark red outline, black drop shadow, red fill with a light shine on the top rows
    big = L.dilate(m, 1)
    for k in (2, 1):
        cv.paint(big, x - 1 + k, y - 1 + k, 3)
    cv.paint(big, x - 1, y - 1, 2)
    cv.paint(m, x, y, 1)
    # shine: the top row of each letter's fill in the band color
    H = len(m)
    for j in range(H):
        for i in range(1, len(m[0]) - 2):
            top = next(k for k in range(j, -1, -1) if k == 0 or not m[k - 1][i])
            if m[j][i] and not m[j][i - 1] and m[j][i + 1] and m[j][i + 2] and 1 <= j - top <= 7:
                cv.put(x + i + 1, y + j, 0)
    conf = scr.write(g, r0, c0, r1, c1)
    if conf: print('title conflicts:', conf[:5], len(conf))
    t88.save(); t90.save()
    scr.render().save(os.path.join(SCRATCH, 'title_preview.png'))
    return w, h

# ---------------------------------------------------------------- boot screens
class Canvas:
    """Paint on a screen region, only where the tile is free to change."""
    def __init__(self, scr, r0, c0, r1, c1):
        self.scr, self.r0, self.c0, self.r1, self.c1 = scr, r0, c0, r1, c1
        self.g, self.pals = scr.canvas(r0, c0, r1, c1)
        self.w, self.h = len(self.g[0]), len(self.g)
        users = scr.users()
        region = {scr.visible(r, c) for r in range(r0, r1) for c in range(c0, c1)}
        self.freecell = {}
        for r in range(r0, r1):
            for c in range(c0, c1):
                key = scr.cells.get(scr.visible(r, c))
                self.freecell[(r, c)] = key is not None and len(users[key[:2]]) == 1
                self.inregion = getattr(self, 'inregion', {})
                self.inregion[(r, c)] = key is not None and all(u in region for u in users[key[:2]])
    def free(self, x, y):
        return self.freecell.get((self.r0 + y // 8, self.c0 + x // 8), False)
    def put(self, x, y, v):
        if 0 <= x < self.w and 0 <= y < self.h and self.free(x, y):
            self.g[y][x] = v
    def get(self, x, y):
        return self.g[y][x]
    def paint(self, mask, x0, y0, v, clip=None):
        for j, row in enumerate(mask):
            for i, m in enumerate(row):
                if m: self.put(x0 + i, y0 + j, v(x0 + i, y0 + j) if callable(v) else v)
    def fill_cells(self, pattern):
        """Reset every free cell to pattern(r, c) -> 8x8 values."""
        for (r, c), ok in self.inregion.items():
            if ok:
                t = pattern(r, c)
                for j in range(8):
                    for i in range(8):
                        self.g[(r - self.r0) * 8 + j][(c - self.c0) * 8 + i] = t[j][i]
    def commit(self, label):
        conf = self.scr.write(self.g, self.r0, self.c0, self.r1, self.c1)
        if conf: print(label, 'conflicts:', conf[:4], len(conf))

SMALL = {  # 5x7 (+2 descender rows) letters for the copyright line
 '©': [".#####.","#.....#","#.###.#","#.#...#","#.###.#","#.....#",".#####."],
 'M': ["#...#","##.##","#.#.#","#.#.#","#...#","#...#","#...#"],
 'A': [".###.","#...#","#...#","#####","#...#","#...#","#...#"],
 'S': [".####","#....","#....",".###.","....#","....#","####."],
 'e': [".....",".....",".###.","#...#","#####","#....",".###."],
 'd': ["....#","....#",".####","#...#","#...#","#...#",".####"],
 't': [".#..",".#..","####",".#..",".#..",".#..","..##"],
 'a': [".....",".....",".###.","....#",".####","#...#",".####"],
 'i': ["#",".","#","#","#","#","#"],
 'o': [".....",".....",".###.","#...#","#...#","#...#",".###."],
 'b': ["#....","#....","####.","#...#","#...#","#...#","####."],
 'h': ["#....","#....","####.","#...#","#...#","#...#","#...#"],
 'u': [".....",".....","#...#","#...#","#...#","#..##",".##.#"],
 'p': [".....",".....","####.","#...#","#...#","#...#","####.","#....","#...."],
 'n': [".....",".....","####.","#...#","#...#","#...#","#...#"],
 '/': ["....#","...#.","...#.","..#..",".#...",".#...","#...."],
 ' ': ["..."]*7,
}
def small_text(text, gap=1):
    rows = [""] * 9
    for k, ch in enumerate(text):
        g = SMALL[ch] + ["." * len(SMALL[ch][0])] * (9 - len(SMALL[ch]))
        for j in range(9):
            rows[j] += ("." * gap if k else "") + g[j]
    return [[1 if c == '#' else 0 for c in r] for r in rows]

@item
def boot():
    """Copyright line, Jorudan logo and Nekogumi logo on the boot screens."""
    from screen import Screen
    b88, b90 = Sheet('boot_logos_bg8800'), Sheet('boot_logos_bg9000')
    sheets = {'b88': (b88, 0x8800, 0), 'b90': (b90, 0x9000, 0)}
    tile = lambda sh, t: [[sh.get((t % (sh.w // 8)) * 8 + i, (t // (sh.w // 8)) * 8 + j) for i in range(8)] for j in range(8)]
    checker = lambda r, c: tile(b90, 1 if (r + c) % 2 == 0 else 2)

    # 1. ©めで鯛 / あおば出版 -> © Medetai / Aoba Shuppan (rows 8-9, black = value 0)
    scr = Screen(os.path.join(SCRATCH, 'boot_240.state'), sheets)
    cv = Canvas(scr, 8, 0, 10, 20)
    cv.fill_cells(checker)
    m = small_text("© Medetai / Aoba Shuppan")
    cv.paint(m, (160 - len(m[0])) // 2, 1, 0)
    cv.commit('credit')

    # 2. ジョルダン -> JORUDAN (rows 2-5, gray = value 0, beside the blue mark)
    scr = Screen(os.path.join(SCRATCH, 'boot_540.state'), sheets)
    cv = Canvas(scr, 2, 4, 6, 20)
    cv.fill_cells(checker)
    m = L.render("JORUDAN", cap=14, weight=3.2, width=8, spacing=3, seed=3)
    cv.paint(m, 4 + (cv.w - 4 - len(m[0])) // 2, (32 - len(m)) // 2, 0)
    cv.commit('jorudan')

    # 3. ねこぐみ -> NEKOGUMI (under the cat, rows 14-16)
    scr = Screen(os.path.join(SCRATCH, 'boot_540.state'), sheets)
    cv = Canvas(scr, 14, 5, 17, 15)
    # keep the cat's chin (row 14 top) by only clearing gray text pixels below y=1
    for y in range(cv.h):
        for x in range(cv.w):
            if cv.free(x, y) and cv.get(x, y) == 0:
                r, c = 14 + y // 8, 5 + x // 8
                cv.g[y][x] = checker(r, c)[y % 8][x % 8]
    m = L.render("NEKOGUMI", cap=9, weight=2, width=3.8, spacing=1.3, wobble=0.25, bounce=0.6, seed=5)
    cv.paint(m, 8 + (56 - len(m[0])) // 2, 2, 0)
    cv.commit('nekogumi')

    b88.save(); b90.save()
    return len(m[0])

# ---------------------------------------------------------------- trick animations
import tricks
from frame import Frame, styled_ink

def stack(lines, gap=1, align='center', **kw):
    """Render several lines with the same settings and stack them (one mask)."""
    ms = [L.render(t, **kw) if t.strip() else [[0]] for t in lines]
    ms = [L.trim(m) if any(any(r) for r in m) else [[0] * 2] * 2 for m in ms]
    W = max(len(m[0]) for m in ms)
    out = []
    for k, m in enumerate(ms):
        if k: out += [[0] * W for _ in range(gap)]
        pad = (W - len(m[0])) // 2 if align == 'center' else (0 if align == 'left' else W - len(m[0]))
        out += [[0] * pad + r + [0] * (W - len(r) - pad) for r in m]
    return out

def fit_text(text, w, h, outline, shadow, weight=2.0, slant=0.15, wobble=0.2, bounce=0.5,
             seed=1, spacing=1.0, width=None, cap=None, sizes=None, angle=0.0, gap=1,
             align='center', vertical=False):
    """Largest lettering of `text` that fits w x h (with room for outline/shadow).
    '\n' splits lines; vertical=True stacks the letters top to bottom."""
    lines = list(text.replace('\n', '')) if vertical else text.split('\n')
    n = len(lines)
    pad_w = (2 if outline else 0) + (1 if shadow else 0)
    pad_h = pad_w
    cap = cap or max(5, (h - pad_h - (n - 1) * gap) // n - int(2 * bounce) - int(weight) + 1)
    width = width or cap * 0.62
    while True:
        kw = dict(cap=cap, weight=weight, width=width, slant=slant, wobble=wobble, bounce=bounce,
                  seed=seed, spacing=spacing, angle=angle)
        if n == 1 and not vertical: m = L.render(lines[0], sizes=sizes, **kw)
        else: m = stack(lines, gap=gap, align=align, **kw)
        if len(m[0]) + pad_w <= w and len(m) + pad_h <= h: return m
        if width > cap * 0.42 and len(m[0]) + pad_w > w: width -= 0.25
        else: cap -= 1
        if cap < 4: return m

def sfx(tid, frame, rect, text, fill, outline=None, shadow=None, erase=lambda v: True,
        erase_to=0, names=None, align='center', mask=None, offset=(0, 0), clear=None, keep=None, shared_ok=False, ring=None, tiles=None, **kw):
    """Redraw the lettering of trick `tid` inside screen rect (x0,y0,x1,y1) of saved
    frame `frame`: erase the sheet pixels there, draw `text` fitted to the rect."""
    sh = tricks.sheets(tid)
    if names: sh = {k: v for k, v in sh.items() if k in names}
    f = Frame(tricks.state(tid, frame), sh)
    x0, y0, x1, y1 = rect
    m = mask or fit_text(text, x1 - x0 - (2 if ring is not None else 0), y1 - y0 - (2 if ring is not None else 0),
                         outline is not None or ring is not None, shadow is not None, **kw)
    m = L.trim(m)
    pw = (1 if outline is not None else 0) + (1 if ring is not None else 0)
    mx = x0 + pw + ((x1 - x0) - len(m[0]) - 2 * pw - (1 if shadow is not None else 0)) // 2 if align == 'center' else x0 + pw
    my = y0 + pw + ((y1 - y0) - len(m) - 2 * pw - (1 if shadow is not None else 0)) // 2
    if align == 'tl': my = y0 + pw
    ink = styled_ink(m, mx + offset[0], my + offset[1], fill, outline, shadow, ring=ring)
    targets = {(n, t) for n in sh for t in tiles} if tiles is not None else set(sh)
    bad = f.edit(clear or rect, targets, erase, erase_to, ink, keep=keep, shared_ok=shared_ok)
    if bad: print('  trick', tid, text, ': %d ink pixels had no tile' % bad)
    return f


def compose(parts):
    """parts: [(mask, dx, dy)] -> one mask with each part placed at its offset."""
    W = max(dx + len(m[0]) for m, dx, dy in parts); H = max(dy + len(m) for m, dx, dy in parts)
    out = [[0] * W for _ in range(H)]
    for m, dx, dy in parts:
        for j, r in enumerate(m):
            for i, v in enumerate(r):
                if v: out[dy + j][dx + i] = 1
    return out

def diag(words, dx, dy, **kw):
    """Words placed in a staircase (each one dx, dy further on)."""
    return compose([(L.trim(L.render(w, **kw)), max(0, k * dx), k * dy) for k, w in enumerate(words)])

def save_trick(tid):
    for k, (sheet, *_r) in tricks.sheets(tid).items():
        sheet.save()

@item
def trick10():
    """カッチーン (frozen stiff) -> FROZEN!"""
    sfx(10, 4, (32, 88, 112, 104), "FROZEN!", fill=1, outline=3, weight=2, slant=0.2, bounce=0.8, seed=2)
    save_trick(10)

@item
def trick01():
    """オラ (punching cry) -> POW!"""
    sfx(1, 21, (80, 16, 112, 40), "POW!", fill=3, outline=1, weight=2.2, slant=0.2, bounce=0.6, seed=4)
    save_trick(1)

@item
def trick08():
    """ちょ… / ちょーだい -> GIM… / GIM ME!"""
    sfx(8, 1, (16, 24, 48, 40), "GIM", fill=2, outline=1, clear=(16, 24, 48, 56), weight=2.2, slant=0.1, seed=3)
    sfx(8, 8, (121, 24, 147, 72), "GIM\nME!", fill=2, outline=1, weight=2.2, slant=0.1, seed=5, cap=17, gap=3)
    save_trick(8)

@item
def trick09():
    """ちょ〜… だいっ (pencil) -> GIM~… ME!"""
    sfx(9, 1, (56, 48, 72, 63), "GIM", fill=3, weight=1.0, slant=0.15, wobble=0.25, bounce=0.5, seed=2)
    sfx(9, 2, (56, 64, 72, 80), "ME!", fill=3, weight=1.0, slant=0.15, wobble=0.25, bounce=0.5, seed=3,
        clear=(56, 64, 72, 96))
    save_trick(9)

@item
def trick11():
    """ばっ ばっ ばっ (kicking sand; one tile block used three times) -> SH SH SH!"""
    sfx(11, 3, (32, 8, 48, 24), "SH", fill=2, outline=3, weight=2.4, slant=0.15, bounce=0.3, seed=1)
    sfx(11, 3, (104, 16, 112, 24), "", fill=2, outline=3, mask=[[1, 1], [1, 1], [1, 1], [0, 0], [1, 1]],
        clear=(104, 16, 112, 32))
    save_trick(11)

@item
def trick15():
    """ぽて (plop) on a pink sticker -> PLOP"""
    sfx(15, 3, (8, 0, 33, 16), "PLOP", fill=3, outline=1, ring=2, clear=(8, 0, 33, 16),
        weight=1.2, slant=0.1, bounce=0.3, spacing=0.5, seed=2)
    save_trick(15)

@item
def trick16():
    """おろろろろ〜 (thin, running down a narrow column) -> UH UH UH UH"""
    uh = lambda k: L.trim(L.render("UH", cap=6, weight=1.0, width=3.0, wobble=0.2, slant=0.15, seed=k))
    m = compose([(uh(0), 0, 0), (uh(1), 2, 12), (uh(2), 5, 24), (uh(3), 8, 37)])
    sfx(16, 5, (8, 9, 8 + len(m[0]), 9 + len(m)), "", fill=3, mask=m, align='tl', clear=(8, 8, 25, 62))
    save_trick(16)

@item
def trick17():
    """むしゃ, written twice down the side -> MUN/CH (shaped to the tiles the words use)"""
    kw = dict(slant=0.08, wobble=0.2, seed=6)
    a = L.trim(L.render("MUN", cap=12, width=3.3, weight=1.6, spacing=0.4, **kw))
    b = L.trim(L.render("CH", cap=12, width=4.5, weight=1.8, spacing=0.6, **kw))
    sfx(17, 5, (32, 1, 56, 40), "", fill=3, mask=compose([(a, 0, 0), (b, 1, 16)]), align='tl',
        clear=(32, 0, 56, 34), erase_to=0)
    a = L.trim(L.render("MUN", cap=13, width=4.4, weight=2.0, spacing=0.6, **kw))
    b = L.trim(L.render("CH", cap=13, width=4.4, weight=2.0, spacing=0.6, **kw))
    sfx(17, 5, (8, 41, 32, 74), "", fill=3, mask=compose([(a, 0, 0), (b, 0, 16)]), align='tl',
        clear=(6, 36, 32, 74), erase_to=0)
    save_trick(17)

@item
def trick18():
    """よじ (clambering) -> HUP"""
    sfx(18, 1, (56, 24, 72, 40), "HUP", fill=3, weight=1.2, slant=0.2, wobble=0.25, bounce=0.6, seed=2)
    save_trick(18)

@item
def trick20():
    """ぐ〜っ with a long stroke (snoring, belly up) -> Z z z"""
    z = [L.trim(L.render("Z", cap=c, weight=2.0, width=c * 0.8, slant=0.1, seed=k)) for k, c in enumerate((11, 8, 6))]
    m = compose([(z[0], 0, 0), (z[1], 6, 15), (z[2], 15, 30)])
    keep = lambda x, y: x + y == 143 or (x >= 51 and y < 100)
    sfx(20, 1, (25, 58, 25 + len(m[0]) + 2, 58 + len(m) + 2), "", fill=3, mask=m, align='left',
        clear=(24, 58, 58, 112), erase=lambda v: v == 3, erase_to=1, keep=keep)
    save_trick(20)

@item
def trick21():
    """ぎゅっ in a pink speech bubble -> GRIP (top to bottom)"""
    sfx(21, 3, (39, 28, 58, 63), "GRIP", fill=3, erase=lambda v: v == 3, erase_to=2,
        clear=(37, 28, 59, 62), vertical=True, weight=2.0, width=6, slant=0.05, seed=2, gap=2)
    save_trick(21)

@item
def trick23():
    """くる (rubbing in circles), across and down -> RUB"""
    sfx(23, 2, (8, 32, 32, 48), "RUB", fill=2, outline=3, weight=1.6, slant=0.15, bounce=0.5, seed=2)
    sfx(23, 9, (16, 31, 24, 56), "RUB", fill=2, outline=3, vertical=True, weight=1.0, width=4, cap=5, gap=1, seed=3,
        slant=0, wobble=0, bounce=0)
    save_trick(23)

@item
def trick28():
    """びたっ (splat), big black letters -> SPLAT"""
    sfx(28, 1, (26, 30, 104, 56), "SPLAT", fill=3, outline=1, clear=(24, 24, 108, 58),
        weight=3.0, slant=0.15, bounce=1.0, seed=4, cap=19)
    save_trick(28)

@item
def trick29():
    """コロン (rolling over), chunky pink -> ROLL"""
    sfx(29, 2, (72, 82, 152, 110), "ROLL", fill=2, outline=3, ring=3, clear=(72, 80, 152, 112),
        weight=3.0, slant=-0.1, bounce=1.2, seed=2)
    save_trick(29)

@item
def trick30():
    """ぐぅ (sleeping), top to bottom -> Z Z"""
    sfx(30, 1, (108, 14, 136, 58), "ZZ", fill=3, outline=1, vertical=True, clear=(108, 14, 136, 58),
        weight=2.6, width=11, slant=0.1, seed=2, gap=4)
    save_trick(30)

@item
def trick36():
    """ぐぅ (sleeping) over the hamster -> Z Z"""
    sfx(36, 1, (72, 24, 100, 58), "ZZ", fill=3, outline=2, vertical=True, clear=(72, 24, 100, 58),
        weight=2.4, width=10, slant=0.1, seed=3, gap=3)
    save_trick(36)

@item
def trick37():
    """ばしっ (whack), red brush letters -> WHA/CK!"""
    a = L.trim(L.render("WHA", cap=14, width=8, weight=2.2, slant=0.2, wobble=0.3, bounce=0.8, seed=2))
    b = L.trim(L.render("CK!", cap=12, width=6.5, weight=2.2, slant=0.2, wobble=0.3, bounce=0.8, seed=3))
    sfx(37, 2, (88, 25, 128, 72), "", fill=3, mask=compose([(a, 0, 0), (b, 16, 22)]), align='tl',
        clear=(86, 22, 130, 72))
    save_trick(37)

@item
def trick42():
    """びょ〜ん (stretching), top of a long line -> BOI + the line"""
    sfx(42, 2, (8, 24, 40, 48), "BOI", fill=3, clear=(0, 0, 40, 48), weight=3.0, width=8, slant=0.1, seed=2)
    save_trick(42)

@item
def trick43():
    """ぼて ぼて (waddling), light and dark pink, alternating -> WAD DLE"""
    sfx(43, 1, (2, 17, 31, 34), "WAD", fill=2, clear=(0, 16, 32, 40), weight=2.0, slant=0.15, bounce=0.6, seed=1,
        shared_ok=True)
    sfx(43, 1, (34, 32, 63, 47), "DLE", fill=3, clear=(32, 24, 64, 48), weight=2.0, slant=0.15, bounce=0.6, seed=2,
        shared_ok=True)
    save_trick(43)

@item
def trick44():
    """すぽっ in a speech bubble (popping into the cup) -> POP!"""
    sfx(44, 2, (115, 20, 141, 36), "POP!", fill=2, outline=3, erase=lambda v: v in (2, 3), erase_to=1,
        clear=(115, 20, 141, 35), weight=1.6, slant=0.1, bounce=0.4, seed=2)
    save_trick(44)

@item
def trick45():
    """びょ〜ん (springing up): びょ at the top, ん at the end of the line -> BOI ... NG"""
    sfx(45, 2, (80, 9, 106, 32), "BOI", fill=3, outline=1, clear=(80, 8, 112, 32), weight=2.0, width=6, slant=0.1, seed=1)
    sfx(45, 2, (112, 72, 136, 88), "NG", fill=3, outline=1, clear=(112, 72, 136, 88), weight=2.0, slant=0.1, seed=2)
    save_trick(45)

@item
def trick46():
    """もぐ もぐ (chewing) -> NOM NOM"""
    sfx(46, 1, (72, 8, 104, 27), "NOM", fill=3, clear=(72, 8, 104, 26), weight=2.2, slant=0.2, bounce=0.8, seed=1)
    sfx(46, 1, (104, 16, 136, 38), "NOM", fill=3, clear=(96, 16, 136, 40), erase=lambda v: v == 3,
        weight=2.2, slant=0.2, bounce=0.8, seed=2)
    save_trick(46)

@item
def trick47():
    """よじ (clambering), small and thin, twice -> HUP"""
    sfx(47, 1, (56, 56, 72, 80), "HUP", fill=3, weight=1.0, slant=0.2, wobble=0.2, bounce=0.6, seed=1,
        tiles=range(184, 192))
    sfx(47, 2, (57, 101, 72, 116), "HUP", fill=3, weight=1.0, width=3.2, cap=6, slant=0.2, wobble=0.2, bounce=0.6,
        seed=2, tiles=range(192, 196), clear=(56, 96, 80, 120))
    save_trick(47)

@item
def trick48():
    """ぐり (rubbing), big outlined letters on a slant -> R U B"""
    r = [L.trim(L.render(c, cap=15, width=10, weight=4.0, slant=0.1, seed=k)) for k, c in enumerate("RUB")]
    m = compose([(r[0], 0, 0), (r[1], 13, 9), (r[2], 25, 24)])
    sfx(48, 1, (38, 6, 90, 60), "", fill=2, outline=3, mask=m, align='tl', clear=(32, 0, 88, 56))
    save_trick(48)

@item
def trick49():
    """ばしっ (smack), brown outlined letters -> SMA/CK"""
    a = L.trim(L.render("SMA", cap=13, width=6, weight=2.4, spacing=0.5, slant=0.15, seed=1))
    b = L.trim(L.render("CK", cap=13, width=6, weight=2.4, spacing=0.5, slant=0.15, seed=2))
    sfx(49, 1, (24, 7, 72, 58), "", fill=2, outline=3, ring=1, mask=compose([(a, 0, 0), (b, 8, 19)]), align='tl',
        clear=(16, 4, 72, 56))
    save_trick(49)

@item
def trick51():
    """じわ〜 (pain welling up), white letters down the left, then a long squiggle -> OW + squiggle"""
    bars = {3, 9, 15, 22, 28, 36}
    # the top of じ sits on the white cage wall: take out its strokes but not the bars
    sfx(51, 3, (0, 24, 1, 25), "", fill=3, mask=[[0]], clear=(0, 24, 40, 41), erase=lambda v: v == 3, erase_to=0,
        keep=lambda x, y: x in bars or (y >= 34 and x < 4), tiles=set(range(256)) - {4, 46})
    sfx(51, 3, (8, 50, 40, 71), "OW", fill=0, outline=3, clear=(0, 34, 40, 73), erase=lambda v: v in (0, 3),
        erase_to=1, keep=lambda x, y: y < 41 and (x in bars or y < 34 + x // 5), tiles=set(range(256)) - {4, 46},
        weight=2.6, slant=0.1, bounce=0.8, seed=2)
    # put back the bars and the wall/floor edge the old letters covered
    edge = lambda x: 34 + (x * 8) // 43
    ink = [(x, y, 3) for x in bars for y in range(24, edge(x))] + [(x, edge(x), 3) for x in range(0, 40)]
    sh = {k: v for k, v in tricks.sheets(51).items()}
    Frame(tricks.state(51, 3), sh).edit((0, 24, 40, 44), {(n, t) for n in sh for t in range(256) if t not in (4, 46)},
                                        lambda v: False, 0, ink)
    save_trick(51)

@item
def trick54():
    """ぬぼっ (blank, dazed look), slanting up -> DUH"""
    sfx(54, 1, (10, 4, 64, 38), "DUH", fill=3, outline=2, clear=(8, 0, 66, 40), weight=3.0, slant=0.15,
        angle=12, bounce=0.8, seed=3)
    save_trick(54)

@item
def trick55():
    """ぱっ in a bubble (grabbing a seed), then もぐもぐ -> ! / NOM NOM"""
    sfx(55, 1, (114, 62, 134, 80), "!", fill=2, erase=lambda v: v in (2, 3), erase_to=1, clear=(114, 63, 134, 79),
        weight=3.0, cap=13, seed=1)
    sfx(55, 2, (72, 24, 128, 40), "NOM NOM", fill=3, weight=1.2, slant=0.2, wobble=0.25, bounce=0.6, seed=2,
        clear=(72, 24, 128, 40))
    save_trick(55)

@item
def trick61():
    """ちま ちま ちま, then もぐ (nibbling), thin -> NIB NIB NIB / NOM"""
    for fr, x, t, sd in ((1, 56, "NIB", 1), (3, 72, "NIB", 2), (5, 80, "NIB", 3), (7, 56, "NOM", 4)):
        sfx(61, fr, (x, 8, x + 16, 24), t, fill=3, weight=1.0, cap=6, width=3.4, slant=0.2, wobble=0.2,
            bounce=0.6, seed=sd)
    save_trick(61)

@item
def trick64():
    """ぽり (scratching), small blue -> ITCH"""
    sfx(64, 1, (40, 48, 64, 58), "ITCH", fill=3, clear=(38, 46, 66, 60), weight=1.0, cap=7, slant=0.2,
        wobble=0.2, bounce=0.5, seed=2)
    save_trick(64)

@item
def trick67():
    """ぬぼ〜 (dazed) -> DUH + the existing ~"""
    sfx(67, 1, (41, 40, 86, 56), "DUH", fill=3, outline=2, clear=(40, 38, 87, 56), weight=2.0, slant=0.1,
        bounce=0.6, seed=4)
    save_trick(67)

@item
def trick68():
    """ぴこ (ear twitch), green -> FLICK"""
    sfx(68, 2, (56, 32, 88, 48), "FLICK", fill=3, outline=1, clear=(56, 32, 88, 48), weight=1.6, slant=0.15,
        bounce=0.6, seed=2)
    save_trick(68)

def chi(tid, big, small, medium=None, names=None):
    """ぢ (angry chitter) in three sizes -> CHI / CHI / !"""
    fr, x, y = big
    sfx(tid, fr, (x, y, x + 24, y + 16), "CHI", fill=3, outline=1, clear=(x, y, x + 24, y + 32), names=names,
        weight=2.2, slant=0.1, bounce=0.6, seed=tid)
    if medium:
        fr, x, y = medium
        sfx(tid, fr, (x, y, x + 16, y + 16), "CHI", fill=3, outline=1, clear=(x, y, x + 16, y + 16), names=names,
            weight=1.0, cap=7, width=3.6, spacing=0.6, slant=0.1, seed=tid + 1)
    fr, x, y = small
    sfx(tid, fr, (x + 1, y + 1, x + 8, y + 15), "", fill=3, outline=1, mask=[[1, 1]] * 7 + [[0, 0]] * 2 + [[1, 1]] * 2,
        clear=(x, y, x + 8, y + 16), names=names)

@item
def trick69():
    """ぢ / ぢぢ (chittering) -> CHI / !"""
    chi(69, (9, 96, 24), (7, 96, 48))
    save_trick(69)

@item
def trick70():
    """ゆら〜っ (swaying) -> SWAY + the existing ~"""
    sfx(70, 1, (36, 20, 76, 44), "SWAY", fill=3, outline=2, clear=(34, 18, 76, 46), weight=2.4, slant=0.15,
        bounce=1.0, wobble=0.3, seed=5)
    sfx(70, 1, (100, 30, 112, 46), "", fill=3, mask=[[0]], clear=(100, 33, 112, 46))
    save_trick(70)

@item
def trick73():
    """ぢ ぢ (chittering), three sizes -> CHI / CHI / !"""
    chi(73, (1, 10, 44), (1, 73, 40), medium=(1, 45, 20))
    save_trick(73)

@item
def trick77():
    """ふぁ〜ん (yawn) -> YAAAWN"""
    sfx(77, 2, (33, 18, 112, 48), "YAAAWN", fill=3, outline=1, clear=(32, 16, 114, 48), weight=2.2, slant=0.1,
        bounce=1.2, wobble=0.3, seed=3, sizes=[1.25, 1, 0.9, 0.8, 1, 1])
    save_trick(77)

@item
def trick86():
    """ぽか (bonk), tiny red on a sticker, top to bottom -> BOP"""
    B = [[1, 1, 0], [1, 1, 1], [1, 0, 1], [1, 1, 1]]
    O = [[1, 1, 1], [1, 0, 1], [1, 0, 1], [1, 1, 1]]
    P = [[1, 1, 1], [1, 0, 1], [1, 1, 1], [1, 0, 0]]
    gap = [[0, 0, 0]]
    sfx(86, 1, (34, 64, 39, 80), "", fill=2, outline=1, mask=B + gap + O + gap + P, align='tl',
        clear=(32, 64, 40, 80), names={'trick86_187FD0'})
    save_trick(86)

@item
def trick87():
    """ぐわ〜ん (dizzy, gong-like), top to bottom with a long line -> WHO + line + A"""
    sfx(87, 2, (24, 1, 41, 40), "WHO", fill=3, outline=1, vertical=True, clear=(24, 0, 41, 40),
        weight=2.2, width=10, slant=0, wobble=0.2, seed=2, gap=2)
    sfx(87, 2, (23, 64, 42, 80), "A", fill=3, outline=1, clear=(22, 64, 42, 80), weight=2.4, cap=13, seed=3)
    save_trick(87)

import ribbon

def tiny(text, sx=1, sy=1, gap=1):
    """TINY pixel font word, each pixel scaled sx by sy."""
    lay = ribbon.unit_layout(text, gap)
    W = max(dx + len(g[0]) for dx, g in lay); H = max(len(g) for dx, g in lay)
    m = [[0] * (W * sx) for _ in range(H * sy)]
    for dx, g in lay:
        for j, row in enumerate(g):
            for i, on in enumerate(row):
                if on:
                    for a in range(sy):
                        for b in range(sx): m[j * sy + a][(dx + i) * sx + b] = 1
    return m

def rot_cw(m):
    return [list(r) for r in zip(*m[::-1])]

@item
def trick02():
    """Repeating 16px strip along the top and bottom (むし-like, hard to read) -> WAG WAG"""
    sfx(2, 1, (16, 16, 32, 32), "", fill=0, mask=tiny("WAG", 1, 2), clear=(16, 16, 32, 32), erase_to=2,
        shared_ok=True)
    save_trick(2)

@item
def trick03():
    """もしゃもしゃ in wavy ribbons across the screen -> NOMNOM (glyph-for-letter swap)"""
    MO = ".#...|####.|.#...|####.|.#...|.#..#|..##."
    SHI = "#...|#...|#...|#..#|.##."
    YA = ".#.#.|####.|.#..#|.#.#."
    ribbon.substitute(3, set(range(10, 29)), 3, 0, [(MO, "N", 1), (SHI, "O", 0), (YA, "m", 0)], strict=False)
    save_trick(3)

@item
def trick06():
    """ずるっ strip along the top and bottom (sliding) -> SLIP SLIP"""
    sfx(6, 11, (16, 16, 32, 32), "", fill=0, mask=tiny("SLIP", 1, 2), clear=(16, 16, 32, 32), erase_to=1,
        shared_ok=True)
    save_trick(6)

@item
def trick33():
    """じたばた down both sides (flailing), 32px repeat -> FLAIL, turned sideways"""
    m = rot_cw(L.trim(L.render("FLAIL", cap=9, width=5, weight=2.2, spacing=1, seed=3)))
    sfx(33, 1, (2, 0, 14, 32), "", fill=0, mask=m, clear=(1, 0, 15, 32), erase_to=2, shared_ok=True)
    save_trick(33)

@item
def trick39():
    """オラオラ strip along the top and bottom, 32px repeat -> POW!"""
    sfx(39, 2, (16, 0, 48, 15), "POW!", fill=3, shadow=2, clear=(16, 0, 48, 16), erase_to=1, shared_ok=True,
        weight=2.6, width=6, cap=11, slant=0.15, seed=2)
    save_trick(39)

@item
def trick75():
    """プリプリ strips (in a huff) in three colour sets, 24px repeat, plus ぢ sprites -> GRR / CHI / !"""
    for fr, bg, fg in ((1, 3, 1), (2, 2, 1), (4, 0, 3)):
        sfx(75, fr, (8, 17, 32, 31), "GRR", fill=fg, clear=(8, 16, 32, 32), erase_to=bg, shared_ok=True,
            names={'trick75_148EF0'}, weight=2.6, width=5.5, cap=11, slant=0.1, seed=2)
    chi(75, (1, 10, 44), (1, 73, 40), medium=(1, 45, 20), names={'trick75_163F00'})
    save_trick(75)

@item
def trick76():
    """ぬるっ in wavy ribbons across the screen (slimy eel) -> SLIP"""
    ribbon.anchored(76, set(range(11, 36)), 2, 3, "SLIP", lambda w, h, n: n >= 44 and w >= 12, blank={10})
    save_trick(76)

# ------------------------------------------------ tricks whose lettering only shows late in the animation
# (the frames were recaptured without pressing A; A skips to the end of a trick)

@item
def trick04():
    """ぎゅう〜♥ (squeeze), one 16x32 sprite column per kana -> H U G (+ the existing ~ and heart)"""
    for k, ch in enumerate("HUG"):
        x = 16 + 24 * k
        sfx(4, 19, (x, 94, x + 16, 124), ch, fill=2, outline=1, clear=(x, 92, x + 16, 126),
            weight=2.4, width=11, slant=0.1, wobble=0.15, seed=4 + k)
    save_trick(4)

@item
def trick05():
    """カッチン (going stiff), big red letters with a dotted shadow -> FREEZE!"""
    sfx(5, 8, (16, 24, 96, 71), "FREEZE!", fill=2, outline=1, shadow=3, clear=(16, 16, 104, 72),
        weight=2.6, slant=0.12, bounce=0.8, wobble=0.25, seed=5)
    save_trick(5)

@item
def trick24():
    """びょ〜ん (boing), pink, with a long stretch line -> BO + line + ING"""
    lt = range(80, 110)
    sfx(24, 5, (80, 1, 104, 31), "BO", fill=1, outline=3, clear=(72, 0, 104, 32), tiles=lt,
        weight=2.4, slant=0.15, bounce=0.5, seed=2)
    sfx(24, 5, (112, 72, 136, 88), "ING", fill=1, outline=3, clear=(108, 64, 136, 92), tiles=lt,
        weight=2.2, slant=0.15, bounce=0.6, seed=3)
    save_trick(24)

@item
def trick52():
    """すぴ… (soft snoring), top to bottom -> Z z z"""
    z = lambda c, k: L.trim(L.render("Z", cap=c, weight=1.6, width=c * 0.8, slant=0.15, seed=k))
    m = compose([(z(11, 1), 0, 0), (z(9, 2), 4, 14), (z(7, 3), 8, 26)])
    sfx(52, 5, (106, 6, 106 + len(m[0]), 6 + len(m)), "", fill=2, mask=m, align='tl', clear=(100, 0, 132, 60))
    save_trick(52)

@item
def trick53():
    """あ… (oh…) and コロッ… (roll…) -> OH / ROLL (the dots stay)"""
    sfx(53, 12, (24, 16, 40, 31), "OH", fill=3, clear=(24, 16, 40, 32), tiles=range(80, 84),
        weight=1.4, slant=0.1, seed=2)
    sfx(53, 13, (24, 16, 40, 31), "OH", fill=2, clear=(24, 16, 40, 32), tiles=range(96, 100),
        weight=1.4, slant=0.1, seed=2)
    kw = dict(cap=8, weight=1.3, width=5, slant=0.1, seed=3)
    m = compose([(L.trim(L.render("RO", **kw)), 0, 0), (L.trim(L.render("LL", **kw)), 16, 8)])
    sfx(53, 14, (1, 105, 1 + len(m[0]), 105 + len(m)), "", fill=3, mask=m, align='tl', clear=(0, 102, 32, 128),
        tiles=range(112, 119))
    save_trick(53)

@item
def trick58():
    """ぬるり (slippery) and くねっ (wriggle), black letters -> SLIP / SQUIRM"""
    sfx(58, 6, (72, 1, 104, 23), "SLIP", fill=3, clear=(70, 0, 106, 24), tiles=range(184, 200),
        weight=1.8, slant=0.15, bounce=0.5, wobble=0.3, seed=2)
    sfx(58, 7, (24, 104, 72, 120), "SQUIRM", fill=3, outline=1, clear=(12, 82, 74, 128), tiles=range(200, 236),
        weight=1.8, slant=0.15, bounce=0.5, wobble=0.3, seed=4)
    save_trick(58)

@item
def trick59():
    """ず (zip; a dash) in three sizes -> ZIP"""
    for fr, rect, clear, tl, k in ((7, (45, 20, 69, 36), (40, 16, 82, 66), range(72, 86), 1),
                                   (10, (61, 65, 101, 81), (50, 60, 104, 112), range(55, 72), 2),
                                   (13, (90, 19, 122, 35), (88, 16, 124, 52), range(86, 96), 3)):
        sfx(59, fr, rect, "ZIP", fill=3, outline=2, clear=clear, tiles=tl, weight=2.2, slant=0.2, bounce=0.3,
            seed=k)
    save_trick(59)

@item
def trick62():
    """ふぅっ (sigh), then ぱたっ / ぱた (flop) next to an arrow -> PHEW / FLOP"""
    sfx(62, 4, (22, 50, 42, 80), "PHEW", fill=3, vertical=True, clear=(20, 48, 44, 82),
        weight=1.0, width=5, cap=5, gap=2, slant=0.1, seed=2)
    sfx(62, 5, (69, 40, 104, 56), "FLOP", fill=3, clear=(69, 38, 106, 64), weight=1.6, slant=0.15,
        bounce=0.4, seed=3)
    sfx(62, 6, (74, 40, 100, 64), "FL\nOP", fill=3, clear=(73, 38, 100, 64), weight=1.6, slant=0.15,
        seed=4, gap=2)
    save_trick(62)

@item
def trick63():
    """ぽこっ (pop) in a bubble and big, ひく (sniff), すっ‥ (a sniff) -> POP / POP! / SNIF / SNIFF"""
    sfx(63, 4, (75, 52, 92, 68), "POP", fill=3, erase_to=0, clear=(74, 50, 93, 69),
        keep=lambda x, y: (x >= 88 and y <= 53) or x <= 74, weight=1.4, slant=0.1, seed=2,
        names={'trick63_181650'})
    sfx(63, 9, (96, 16, 120, 40), "PO", fill=3, outline=1, clear=(92, 14, 132, 58),
        names={'trick63_1427A0'}, tiles=range(56, 128), weight=2.2, slant=0.15, bounce=0.5, seed=3)
    sfx(63, 9, (112, 40, 128, 56), "P!", fill=3, outline=1, clear=(112, 40, 112, 40),
        names={'trick63_1427A0'}, tiles=range(56, 128), weight=1.8, slant=0.15, seed=5)
    for fr, pitch, tl in ((5, 6, (2, 3, 18, 34)), (6, 6, (4, 5, 20, 36)), (7, 7, (6, 7, 22, 38, 54))):
        m = compose([(tiny(c, 2, 1), 0, pitch * k) for k, c in enumerate("SNIF")])
        sfx(63, fr, (81, 41, 81 + len(m[0]), 41 + len(m)), "", fill=3, mask=m, align='tl',
            clear=(80, 40, 96, 72), names={'trick63_1427A0'}, tiles=tl)
    sfx(63, 8, (80, 38, 112, 56), "SNIFF", fill=3, clear=(80, 36, 112, 56), names={'trick63_1427A0'},
        tiles=range(0, 48), weight=1.8, slant=0.1, seed=4)
    save_trick(63)

@item
def trick65():
    """あ… (oh…) and ない (it's not there), tiny; ない wobbles between three tile sets -> OH / GO NE"""
    sfx(65, 7, (40, 32, 56, 44), "OH", fill=3, clear=(40, 30, 58, 46), tiles=(7, 8, 23, 24),
        weight=1.0, slant=0.1, seed=2)
    m = compose([(tiny("GO"), 0, 0), (tiny("NE"), 0, 16)])
    for fr, x, tl in ((3, 33, (2, 3, 18, 19, 34)), (4, 31, (1, 17, 33)), (5, 35, (0, 16, 32))):
        sfx(65, fr, (x, 33, x + len(m[0]), 33 + len(m)), "", fill=3, mask=m, align='tl',
            clear=(24, 30, 50, 58), tiles=tl)
    save_trick(65)

@item
def trick80():
    """ずざざっ (shuffling back) -> SHUFFLE"""
    sfx(80, 6, (40, 24, 96, 40), "SHUFFLE", fill=3, outline=1, clear=(36, 14, 110, 50), tiles=range(60, 84),
        weight=1.6, slant=0.15, bounce=0.3, wobble=0.3, seed=3)
    save_trick(80)

@item
def trick81():
    """ぐちゃーっ (squelch), bold dark green -> SQUISH"""
    sfx(81, 6, (40, 16, 88, 48), "SQU", fill=3, outline=1, clear=(38, 12, 122, 50), tiles=range(60, 96),
        weight=3.0, slant=0.15, bounce=0.4, wobble=0.3, seed=2)
    sfx(81, 6, (88, 32, 112, 48), "ISH", fill=3, outline=1, clear=(88, 32, 88, 32), tiles=range(60, 96),
        weight=2.0, slant=0.15, bounce=0.3, wobble=0.3, seed=3)
    save_trick(81)

@item
def trick82():
    """Scrawl next to the toothbrush (likely ゴシ, scrubbing; hard to read), one 14x16 and one 8x8 patch
    -> RUB !"""
    sfx(82, 6, (61, 63, 73, 73), "", fill=3, mask=tiny("RUB", 1, 2), clear=(58, 56, 98, 76), tiles=range(66, 72))
    sfx(82, 6, (84, 61, 88, 67), "", fill=3, mask=[[1, 1]] * 4 + [[0, 0], [1, 1]], clear=(84, 61, 84, 61),
        tiles=range(66, 72))
    save_trick(82)

@item
def trick84():
    """ぴ (ear twitch), purple in a thought bubble -> TWI/TCH"""
    sfx(84, 5, (38, 22, 66, 56), "TWI\nTCH", fill=2, outline=3, clear=(36, 20, 68, 58),
        weight=2.0, slant=0.12, seed=2, gap=2)
    save_trick(84)

@item
def trick85():
    """ぶら (dangle) down both side strips, 32px repeat -> SWING, turned sideways"""
    m = rot_cw(L.trim(L.render("SWING", cap=10, width=5, weight=2.2, spacing=1, seed=3)))
    sfx(85, 5, (10, 32, 22, 64), "", fill=2, mask=m, clear=(8, 32, 24, 64), erase_to=1, shared_ok=True)
    save_trick(85)

if __name__ == '__main__':
    names = sys.argv[1:] or list(ITEMS)
    for n in names:
        ITEMS[n]()
        print('drew', n)
