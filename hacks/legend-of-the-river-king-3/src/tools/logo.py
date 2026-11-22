"""English title logo for Kawa no Nushi Tsuri 5, from the tester's art (art/river_king_3_*.png).

The title logo is made of 8bpp sprites. Three sprite frames in the bank at 0x08368D18 draw it:
  A  "川のぬし釣り" (slides/fades in)      -> "Legend of / The River King"
  B  the "5", one 64x64 sprite at tile 768 that spins in on its own  -> "3"
  C  the finished logo: A + 5 + the subtitle "~不思議の森から~"  -> A + 3 + "~ From the Mysterious Forest ~"
All logo pixels use OBJ palette entries 32-127 (palette at 0x08369098); the character uses 128-207.

make(rom_bytes, obj_block) returns (new_obj_block, new_bank_prefix, palette96) where new_bank_prefix replaces
frames A, B, C (the bank's later frames are copied after it unchanged by the caller).
"""
import os, struct
import numpy as np
from PIL import Image
from k5lib import ROM_PATH

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(os.path.dirname(HERE), 'art')
BANK = 0x368D18                     # ROM offset of frame A; B and C follow
BANK_REST = 0x368F24                # first frame after C
ANCHOR = (79, 5)                    # screen position of the frames' origin on the title screen
NUM_CENTER = (193, 51)              # where the original 5 sits on screen (B lands there)
SCALE = 0.38
PAL_LO, PAL_N = 32, 96

SIZES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8),
         (1, 2): (32, 16), (1, 3): (64, 32), (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}
SHAPE = {v: k for k, v in SIZES.items()}

def frames(d, a, n):
    out = []
    for _ in range(n):
        cnt = struct.unpack_from('<H', d, a)[0]
        recs = [struct.unpack_from('<4H', d, a + 4 + 8 * k) for k in range(cnt)]
        out.append((a, recs)); a += 4 + 8 * cnt
    return out, a

def units_of(rec):
    a0, a1, a2, _ = rec
    w, h = SIZES[(a0 >> 14, a1 >> 14)]; t = a2 & 1023; u = set()
    for ty in range(h // 8):
        for tx in range(w // 8):
            if (a0 >> 13) & 1: u |= {t + ty * 32 + tx * 2, t + ty * 32 + tx * 2 + 1}
            else: u.add(t + ty * 32 + tx)
    return u

FONT = 0x32F538                     # dialogue font, see build_patch.FONT
# 5-px replacements for the squat 4-px m and M (also written into the ROM font by build_patch)
WIDE = {'m': ['.....', '.....', '####.', '#.#.#', '#.#.#', '#.#.#', '#.#.#', '#.#.#', '#.#.#', '.....'],
        'M': ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#', '#...#', '#...#', '.....']}

def text_mask(d, text):
    """Draws text with the game's dialogue font (6 px per character), using the widened m."""
    m = np.zeros((10, 6 * len(text)), bool)
    for i, ch in enumerate(text):
        c = ord(ch); a = FONT + 20 * (c - 1 if c > 0x4F else c)
        for y in range(10):
            if ch == ' ': row = [False] * 6
            elif ch in WIDE: row = [c == '#' for c in WIDE[ch][y]] + [False]
            else:
                v = struct.unpack_from('<H', d, a + 2 * y)[0]; row = [bool(v >> (8 + x) & 1) for x in range(6)]
            m[y, 6 * i:6 * i + 6] = row
    cols = np.nonzero(m.any(0))[0]; rows = np.nonzero(m.any(1))[0]
    return m[rows.min():rows.max() + 1, cols.min():cols.max() + 1]

def subtitle_image(d):
    """'~ From the Mysterious Forest ~' in the game's own font, brown with a white outline."""
    txt = text_mask(d, 'From the Mysterious Forest')
    tilde = np.array([[0, 1, 1, 0, 0, 0], [1, 0, 0, 1, 0, 1], [0, 0, 0, 0, 1, 0]], bool)
    h = txt.shape[0]; w = txt.shape[1] + 2 * (tilde.shape[1] + 4)
    m = np.zeros((h, w), bool)
    m[4:7, 0:6] = tilde; m[4:7, w - 6:w] = tilde
    m[:, 10:10 + txt.shape[1]] = txt
    H, W = h + 2, w + 2
    fill = np.zeros((H, W), bool); fill[1:-1, 1:-1] = m
    out = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            out |= np.roll(np.roll(fill, dy, 0), dx, 1)
    img = np.zeros((H, W, 4), np.uint8)
    img[out] = (255, 255, 255, 255)
    img[fill] = (88, 40, 16, 255)
    return Image.fromarray(img, 'RGBA')

def art(d):
    """Returns (A, B, C) as RGBA images: A and C are 240x160 screens, B is the 64x64 spinning sprite."""
    big = Image.open(os.path.join(ART, 'river_king_3_complete.png')).convert('RGBA')
    words = Image.new('RGBA', big.size)
    words.alpha_composite(Image.open(os.path.join(ART, 'river_king_3_the_river_king.png')).convert('RGBA'), (0, 43))
    words.alpha_composite(Image.open(os.path.join(ART, 'river_king_3_legend_of.png')).convert('RGBA'), (102, 0))
    num = Image.open(os.path.join(ART, 'river_king_3_number.png')).convert('RGBA')
    sw, sh = round(big.width * SCALE), round(big.height * SCALE)
    words = words.resize((sw, sh), Image.LANCZOS)
    nw, nh = round(num.width * SCALE), round(num.height * SCALE)
    num = num.resize((nw, nh), Image.LANCZOS)
    # The spin starts with an all-zero affine matrix, which paints the whole sprite with its centre texel, so
    # the 3 is shifted inside its 64x64 sprite until the centre texel is transparent (the logo moves with it).
    na = np.array(num)[:, :, 3] >= 128
    shift = None
    for dx, dy in sorted(((x, y) for x in range(-13, 14) for y in range(-8, 9)), key=lambda v: abs(v[0]) + abs(v[1])):
        px, py = 32 - nw // 2 + dx, 32 - nh // 2 + dy
        if px < 0 or px + nw > 64 or py < 0 or py + nh > 64: continue
        if not na[32 - py, 32 - px]: shift = (dx, dy); break
    assert shift is not None
    ncx, ncy = (398 + 48) * SCALE + shift[0], (33 + 60) * SCALE + shift[1]   # number centre inside the scaled logo
    ox, oy = round(NUM_CENTER[0] - ncx), round(NUM_CENTER[1] - ncy)
    A = Image.new('RGBA', (240, 160)); A.alpha_composite(words, (ox, oy))
    B = Image.new('RGBA', (64, 64)); B.alpha_composite(num, (32 - nw // 2 + shift[0], 32 - nh // 2 + shift[1]))
    sub = subtitle_image(d)
    C = A.copy()
    C.alpha_composite(sub, ((240 - sub.width) // 2, max(0, oy - sub.height - 2)))
    return A, B, C, (ox, oy)

def quantize(images):
    """One 96-colour palette for all logo pixels; alpha is cut at 50%."""
    strips = [np.array(im) for im in images]
    px = np.concatenate([s.reshape(-1, 4) for s in strips])
    px = px[px[:, 3] >= 128][:, :3]
    sample = Image.fromarray(px.reshape(1, -1, 3).astype(np.uint8), 'RGB')
    q = sample.quantize(PAL_N, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:PAL_N * 3]).reshape(-1, 3)
    out = []
    for s in strips:
        rgb = s[:, :, :3].astype(int)
        dist = ((rgb[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(-1)
        idx = dist.argmin(-1) + PAL_LO
        idx[s[:, :, 3] < 128] = 0
        out.append(idx.astype(np.uint8))
    gba = b''.join(struct.pack('<H', (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)) for r, g, b in pal)
    return out, gba

def pieces(idx):
    """Cover the non-zero pixels of a 240x160 index image with 32x16 sprites (smaller at the edges)."""
    ys, xs = np.nonzero(idx)
    x0, y0 = xs.min() & ~7, ys.min() & ~7
    out = []
    for y in range(y0, ys.max() + 1, 16):
        for x in range(x0, xs.max() + 1, 32):
            blk = idx[y:y + 16, x:x + 32]
            if not blk.any(): continue
            cy = np.nonzero(blk.any(1))[0]; cx = np.nonzero(blk.any(0))[0]
            w = 32 if cx.max() >= 16 else (16 if cx.max() >= 8 else 8)
            h = 16 if cy.max() >= 8 else 8
            if (w, h) == (8, 16) or (w, h) == (16, 8) or (w, h) in SIZES.values():
                out.append((x, y, w, h))
            else:
                out.append((x, y, 32, 16))
    return out

class Alloc:
    def __init__(self, free):
        self.free = np.array([[(r * 32 + c) in free for c in range(32)] for r in range(32)])
    def take(self, uw, uh):
        for r in range(32 - uh + 1):
            for c in range(0, 32 - uw + 1, 2):
                if self.free[r:r + uh, c:c + uw].all():
                    self.free[r:r + uh, c:c + uw] = False
                    return r * 32 + c
        raise RuntimeError('no room for a %dx%d unit sprite' % (uw, uh))

def put(block, tile, idx, x, y, w, h):
    for ty in range(h // 8):
        for tx in range(w // 8):
            u = tile + ty * 32 + tx * 2
            cell = idx[y + ty * 8:y + ty * 8 + 8, x + tx * 8:x + tx * 8 + 8]
            c = np.zeros((8, 8), np.uint8); c[:cell.shape[0], :cell.shape[1]] = cell
            block[u * 32:u * 32 + 64] = c.tobytes()

def rec(x, y, w, h, tile):
    sh, sz = SHAPE[(w, h)]
    return struct.pack('<4H', (y & 255) | 0x2000 | (sh << 14), (x & 511) | (sz << 14), tile, 0)

MENU_FONT = '/usr/share/fonts/truetype/noto/NotoSans-CondensedBold.ttf'
MENU_ITEMS = (('New Game', 79, 72), ('Continue', 88, 64))   # (text, first 4bpp tile, width); 16 px tall

MENU_ART = os.path.join(ART, 'menu_%s.png')   # masks as first rendered with Noto Sans Condensed Bold

def menu_mask(text, width):
    """The 16 px letter mask for a title menu item. The release build reads the saved masks in art/
    (rendered once from MENU_FONT); delete them to render again from the font."""
    saved = MENU_ART % text.lower().replace(' ', '_')
    if os.path.exists(saved):
        return np.array(Image.open(saved).convert('L')) >= 128
    from PIL import ImageDraw, ImageFont
    for size in range(13, 8, -1):
        f = ImageFont.truetype(MENU_FONT, size * 4)
        im = Image.new('L', (width * 4 + 200, 64)); ImageDraw.Draw(im).text((0, 0), text, 255, font=f)
        bb = im.getbbox(); im = im.crop(bb)
        w, h = round(im.width / 4), round(im.height / 4)
        if w <= width - 4 and h <= 12: break
    m = np.array(im.resize((w, h), Image.BOX)) >= 110
    out = np.zeros((16, width), bool)
    x0, y0 = (width - w) // 2, (16 - h) // 2
    out[y0:y0 + h, x0:x0 + w] = m
    return out

def grow(m):
    o = m.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            o |= np.roll(np.roll(m, dy, 0), dx, 1)
    return o

def menu_items(block):
    """はじめから / つづきから sprites -> New Game / Continue in the same style: grey (or red when highlighted)
    letters shaded 9-c from top to bottom, a white outline (f) and a dark rim (2)."""
    for text, tile, width in MENU_ITEMS:
        fill = menu_mask(text, width)
        white = grow(fill); rim = grow(white)
        idx = np.zeros((16, width), np.uint8)
        idx[rim] = 2; idx[white] = 0xF
        ys = np.nonzero(fill.any(1))[0]; top, bot = ys.min(), ys.max()
        for y in range(16):
            shade = 9 + min(3, max(0, (y - top) * 4 // max(1, bot - top + 1)))
            idx[y][fill[y]] = shade
        for ty in range(2):
            for tx in range(width // 8):
                u = tile + ty * 32 + tx
                cell = idx[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
                block[u * 32:u * 32 + 32] = bytes((int(cell[y, 2 * i]) | (int(cell[y, 2 * i + 1]) << 4))
                                                  for y in range(8) for i in range(4))

def make(d, obj_block):
    (fa, fb, fc), end = frames(d, BANK, 3)
    assert end == BANK_REST
    block = bytearray(obj_block)
    menu_items(block)
    old = set()
    for _, recs in (fa, fc):
        for r in recs: old |= units_of(r)
    b_units = units_of(fb[1][0])
    nonzero = {u for u in range(1024) if any(block[u * 32:u * 32 + 32])}
    free = (old - b_units) | (set(range(1024)) - nonzero - b_units)
    for u in old - b_units: block[u * 32:u * 32 + 32] = bytes(32)
    A, B, C, _ = art(d)
    (ia, ib, ic), pal = quantize([A, B, C])
    al = Alloc(free)
    ax, ay = ANCHOR
    ra = b''; rc = b''; na = nc = 0
    placed = {}
    for (x, y, w, h) in pieces(ia):
        t = al.take(w // 4, h // 8); put(block, t, ia, x, y, w, h); placed[(x, y, w, h)] = t
        ra += rec(x - ax, y - ay, w, h, t); na += 1
    # C: subtitle pieces (only where C differs from A), the 3, then A's pieces
    sub_only = ic.copy(); sub_only[ia != 0] = 0
    for (x, y, w, h) in pieces(sub_only):
        t = al.take(w // 4, h // 8); put(block, t, ic, x, y, w, h)
        rc += rec(x - ax, y - ay, w, h, t); nc += 1
    # B: the 3, drawn into the existing 64x64 sprite at tile 768; C shows the same tiles unrotated
    bt = fb[1][0][2] & 1023
    put(block, bt, ib, 0, 0, 64, 64)
    rc += rec(NUM_CENTER[0] - 32 - ax, NUM_CENTER[1] - 32 - ay, 64, 64, bt); nc += 1
    for (x, y, w, h), t in placed.items():
        rc += rec(x - ax, y - ay, w, h, t); nc += 1
    bank = struct.pack('<HH', na, 0) + ra
    bank += d[fb[0]:fb[0] + 4 + 8 * len(fb[1])]
    bank += struct.pack('<HH', nc, 0) + rc
    return bytes(block), bank, pal

if __name__ == '__main__':
    A, B, C, o = art(open(ROM_PATH, 'rb').read())
    (ia, ib, ic), pal = quantize([A, B, C])
    print('logo origin', o, 'pieces A', len(pieces(ia)))
    prev = Image.new('RGBA', (240, 160), (40, 120, 140, 255)); prev.alpha_composite(C)
    n = Image.new('RGBA', (240, 160)); n.alpha_composite(B, (NUM_CENTER[0] - 32, NUM_CENTER[1] - 32))
    prev.alpha_composite(n); prev.resize((480, 320), Image.NEAREST).save('logo_preview.png')
