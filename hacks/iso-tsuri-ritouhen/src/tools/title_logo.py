"""English title logo on BG3 of the title screen (2bpp, palettes: 1 = black/red/dark red, 2 = black/yellow/dark yellow).

The original BG3 tiles ($C5:ABE6, pointer $81:8636) and map ($C5:B40C, pointer $81:8648 + 6) are LZ streams
(tools/islz.py). The Japanese logo occupies map rows 2-14; the copyright line (rows 24-25) is kept.
python3 tools/title_logo.py  -> gfx/edit/title_logo_bg3.png (preview of the new layer)
"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); GAME = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import islz

TILES_PTR, MAP_PTR = 0x18636, 0x18648       # ROM offsets of the 24-bit pointers in bank $81
LOGO_ROWS = range(0, 17)          # drawn logo; an imported PNG may use rows 0-22 (copyright line is rows 24-25)

CUSTOM = os.path.join(GAME, 'gfx', 'edit', 'title_logo.png')
# BG3 colours: palette 0 white text, 1 red logo, 2 yellow subtitle (black = colour 1 of each)
PALS = {0: [None, (0, 0, 0), (0, 0, 0), (248, 248, 248)],
        1: [None, (0, 0, 0), (248, 64, 8), (184, 48, 16)],
        2: [None, (0, 0, 0), (240, 240, 0), (160, 160, 0)]}

def custom_layer(path):
    """Read a 256x224 PNG drawn in the BG3 colours (anything else / transparent / magenta = empty)."""
    src = Image.open(path).convert('RGBA'); out = Image.new('P', (256, 224), 0)
    def near(rgb, cands):
        return min(cands, key=lambda c: sum((a - b) ** 2 for a, b in zip(rgb, c[1])))
    for ty in range(28):
        for tx in range(32):
            px = [src.getpixel((tx * 8 + x, ty * 8 + y)) for y in range(8) for x in range(8)]
            solid = [p[:3] for p in px if p[3] >= 128 and p[:3] != (255, 0, 255)]
            if not solid: continue
            # palette = the one whose non-black colours fit this tile best
            def cost(pal):
                return sum(min(sum((a - b) ** 2 for a, b in zip(rgb, c)) for c in PALS[pal][1:]) for rgb in solid)
            pal = min(PALS, key=cost)
            cands = [(i, c) for i, c in enumerate(PALS[pal]) if c]
            for k, p in enumerate(px):
                if p[3] >= 128 and p[:3] != (255, 0, 255):
                    out.putpixel((tx * 8 + k % 8, ty * 8 + k // 8), pal << 2 | near(p[:3], cands)[0])
    return out

def layer():
    if os.path.exists(CUSTOM): return custom_layer(CUSTOM)
    return drawn_layer()

def drawn_layer():
    """Return a 256x224 'P' image: pixel value = color index | palette << 2 (0 = transparent).
    Hand-drawn lettering, no fonts: brush strokes shaded like 磯釣り, block letters outlined like 離島篇."""
    import brush, title_letters as TL
    out = Image.new('P', (256, 224), 0); px = out.load()
    s1, _ = TL.word('Rock', 28, 8, kern=[-1, -1, 0, 0], scale=1.0)
    s2, _ = TL.word('Fishing', 78, 56, kern=[-3, -2, -2, -4, -2, -3, 0], scale=0.95)
    red = brush.shade(brush.coverage(brush.render(s1 + s2)))
    for (x, y), c in red.items(): px[x, y] = 1 << 2 | c
    yel = {}
    TL.place(yel, 'REMOTE', 224 - 51, 105); TL.place(yel, 'ISLANDS', 224 - 57, 118)  # own tile rows (13-16): one palette per tile
    for (x, y), c in yel.items():
        if not px[x, y]: px[x, y] = 2 << 2 | c
    return out

def tile2bpp(px):
    b = bytearray(16)
    for y in range(8):
        for x in range(8):
            c = px[y * 8 + x]
            if c & 1: b[y * 2] |= 0x80 >> x
            if c & 2: b[y * 2 + 1] |= 0x80 >> x
    return bytes(b)

def build(rom):
    """rom: bytearray of the expanded ROM. Returns (tiles_bytes, map_bytes) for BG3."""
    def ptr(o): return rom[o] | rom[o + 1] << 8 | rom[o + 2] << 16
    hi = lambda a: a - 0xC00000
    tiles, _ = islz.decompress(rom, hi(ptr(TILES_PTR)))
    mp, _ = islz.decompress(rom, hi(ptr(MAP_PTR)) + 6)
    mp = bytearray(mp); tiles = bytearray(tiles)
    rows = range(0, 23) if os.path.exists(CUSTOM) else LOGO_ROWS
    keep = set()
    for i in range(0, 0x800, 2):
        row = i // 64
        e = mp[i] | mp[i + 1] << 8
        if row in rows: mp[i] = mp[i + 1] = 0
        else: keep.add(e & 0x3ff)
    free = [t for t in range(1, 256) if t not in keep]
    im = layer(); px = im.load()
    cache = {}
    for ty in rows:
        for tx in range(32):
            cells = [px[tx * 8 + x, ty * 8 + y] for y in range(8) for x in range(8)]
            if not any(cells): continue
            pal = max(c >> 2 for c in cells)
            t = tile2bpp([c & 3 for c in cells])
            if t not in cache:
                if not free: raise SystemExit('title logo: out of BG3 tiles')
                n = free.pop(0); cache[t] = n; tiles[n * 16:n * 16 + 16] = t
            e = cache[t] | pal << 10
            i = (ty * 32 + tx) * 2; mp[i] = e & 0xff; mp[i + 1] = e >> 8
    print('title logo: %d tiles, %d free left' % (len(cache), len(free)))
    return bytes(tiles), bytes(mp)

def preview(path):
    im = layer()
    pal = [0, 0, 0, 0, 0, 0, 248, 64, 8, 184, 48, 16, 0, 0, 0, 240, 240, 0, 160, 160, 0]
    full = [30, 60, 110] + [0, 0, 0] + [0, 0, 0] + [248, 248, 248] + [30, 60, 110] + pal[3:]
    im.putpalette(full + [0] * (768 - len(full)))
    im.convert('RGB').resize((512, 448), Image.NEAREST).save(path)

def insert(rom, tiles_at=0xE14000, map_at=0xE16000):
    """Build, compress and insert the new BG3 tiles/map; repoint $81:8636 / $81:8648."""
    tiles, mp = build(rom)
    ct = islz.compress(tiles); cm = islz.compress(mp)
    assert islz.decompress(ct)[0] == tiles and islz.decompress(cm)[0] == mp
    hi = lambda a: a - 0xC00000
    rom[hi(tiles_at):hi(tiles_at) + len(ct)] = ct
    old_map = (rom[MAP_PTR] | rom[MAP_PTR + 1] << 8 | rom[MAP_PTR + 2] << 16) - 0xC00000
    hdr = bytes(rom[old_map:old_map + 6])
    rom[hi(map_at):hi(map_at) + 6 + len(cm)] = hdr + cm
    assert len(ct) < 0x2000 and len(cm) < 0x2000
    rom[TILES_PTR:TILES_PTR + 3] = tiles_at.to_bytes(3, 'little')
    rom[MAP_PTR:MAP_PTR + 3] = map_at.to_bytes(3, 'little')

if __name__ == '__main__':
    os.makedirs(os.path.join(GAME, 'gfx', 'edit'), exist_ok=True)
    preview(os.path.join(GAME, 'gfx', 'edit', 'title_logo_bg3.png'))
