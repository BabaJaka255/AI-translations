"""English title logo for Kawa no Nushi Tsuri (FC): "Legend of the / RIVER KING".

The Japanese logo is background tiles in CHR page 0 placed by PPU-write packets in
bank 11 (file 0x177A1: count, address hi, address lo, tiles), rows 2-11.  This
draws the English logo in the same colours (3 pink fill, 2 light pink outline,
1 dark blue shadow, 0 sky), cuts it into tiles, reuses only the tile numbers the
Japanese logo used, and rewrites the tile numbers in the same packets (same
lengths, so nothing else moves).  Cells outside the packets, under clouds or in
the clouds' palette areas are left alone.
"""
import os
from PIL import Image, ImageDraw, ImageFont

PACKETS = 0x177A1           # file offset in the original ROM (bank 11, unchanged in the expanded ROM)
N_PACKETS = 10              # rows 2-11
FONT_BIG = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_SMALL = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
# Hand-edited logo: if this file exists the build uses it instead of drawing the text.
# 256x96 PNG, any mode; each pixel is matched to the nearest of the 4 logo colours (PAL).
LOGO_PNG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gfx", "title_logo.png")
PAL = [(76, 154, 236), (8, 76, 196), (236, 174, 212), (236, 88, 180)]   # sky, shadow, outline, fill

# cells (row -> allowed columns) that are in palette 0 and free of clouds
ALLOWED = {2: range(6, 22), 3: range(6, 22), 4: range(6, 22), 5: range(6, 22),
           6: range(4, 28), 7: range(4, 28), 8: range(8, 26), 9: range(8, 26),
           10: range(8, 26), 11: range(8, 26)}
CLOUD = {0x4F, 0x6F, 0x8F, 0x5F, 0x7F, 0x9F, 0x2C, 0x2D, 0x2E, 0x2F, 0x0E, 0x3C, 0x3D, 0x3E, 0x3F, 0x0F}
SKY = 0xFE


def read_packets(rom):
    o = PACKETS; out = []
    for _ in range(N_PACKETS):
        n = rom[o]; a = (rom[o + 1] << 8) | rom[o + 2]
        row, col = (a - 0x2000) // 32, (a - 0x2000) % 32
        out.append((o + 3, row, col, n))
        o += 3 + n
    return out


def _text_mask(text, font_path, cap, max_w):
    """1-bit mask of text with cap height ~cap px, squeezed to max_w if needed."""
    size = cap * 2
    while True:
        f = ImageFont.truetype(font_path, size)
        if f.getbbox("H")[3] - f.getbbox("H")[1] <= cap:
            break
        size -= 1
    bb = f.getbbox(text)
    im = Image.new("L", (bb[2] - bb[0] + 4, bb[3] - bb[1] + 4), 0)
    ImageDraw.Draw(im).text((2 - bb[0], 2 - bb[1]), text, font=f, fill=255)
    if im.width > max_w:
        im = im.resize((max_w, im.height), Image.LANCZOS)
    return im.point(lambda v: 255 if v >= 128 else 0)


def load_png(path=LOGO_PNG):
    """Read an edited logo PNG back into a 256x96 grid of colour indices."""
    im = Image.open(path).convert("RGB")
    if im.size != (256, 96):
        raise ValueError(f"{path}: logo must be 256x96, got {im.size}")
    px = im.load()

    def idx(c):
        return min(range(4), key=lambda i: sum((a - b) ** 2 for a, b in zip(c, PAL[i])))
    return [[idx(px[x, y]) for x in range(256)] for y in range(96)]


def save_png(g, path):
    im = Image.new("P", (256, 96))
    im.putpalette([v for c in PAL for v in c] + [0] * (256 - 4) * 3)
    im.putdata([v for row in g for v in row])
    im.save(path)


def logo():
    """The logo grid: the edited PNG if there is one, else the drawn text."""
    return load_png() if os.path.exists(LOGO_PNG) else draw()


def draw():
    """Return a 256x96 list of rows of colour indices (title rows 0-11)."""
    W, H = 256, 96
    g = [[0] * W for _ in range(H)]

    def stamp(mask, x0, y0, shadow=2, outline=True):
        w, h = mask.size; px = mask.load()
        on = {(x, y) for y in range(h) for x in range(w) if px[x, y]}
        ring = set()
        if outline:
            for (x, y) in on:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if (x + dx, y + dy) not in on:
                            ring.add((x + dx, y + dy))
        body = on | ring
        for (x, y) in body:                       # drop shadow, down-right
            for s in range(1, shadow + 1):
                X, Y = x0 + x + s, y0 + y + s
                if 0 <= X < W and 0 <= Y < H and g[Y][X] == 0:
                    g[Y][X] = 1
        for (x, y) in ring:
            g[y0 + y][x0 + x] = 2
        for (x, y) in on:
            g[y0 + y][x0 + x] = 3

    def centre(mask, cols, y0, shadow, outline=True):
        x_lo, x_hi = cols.start * 8, cols.stop * 8
        x0 = x_lo + (x_hi - x_lo - mask.width - shadow) // 2
        stamp(mask, x0, y0, shadow, outline)

    small = _text_mask("Legend of the", FONT_SMALL, 9, 124)
    centre(small, range(6, 22), 18, 1)
    river = _text_mask("RIVER", FONT_BIG, 25, 120)
    centre(river, range(6, 22), 33, 2)
    king = _text_mask("KING", FONT_BIG, 25, 136)
    centre(king, range(8, 26), 63, 2)
    return g


def _tile_bytes(g, row, col):
    lo = bytearray(8); hi = bytearray(8)
    for y in range(8):
        for x in range(8):
            v = g[row * 8 + y][col * 8 + x]
            lo[y] |= (v & 1) << (7 - x); hi[y] |= ((v >> 1) & 1) << (7 - x)
    return bytes(lo + hi)


def apply(rom, chr_page0):
    """rom: expanded ROM (bytearray).  chr_page0: file offset of CHR page 0."""
    g = logo()
    # every pixel must sit in an allowed cell
    for y in range(96):
        for x in range(256):
            if g[y][x] and (y // 8 not in ALLOWED or x // 8 not in ALLOWED[y // 8]):
                raise ValueError(f"logo pixel outside the logo area at {x},{y} (see gfx/title_logo_guide.png)")
    pk = read_packets(rom)
    free = sorted({rom[o + i] for o, _, _, n in pk for i in range(n)} - CLOUD - {SKY})
    tiles = {}
    for o, row, col, n in pk:
        for i in range(n):
            c = col + i
            if rom[o + i] in CLOUD:
                continue
            tb = _tile_bytes(g, row, c)
            if not any(tb):
                rom[o + i] = SKY; continue
            if tb not in tiles:
                if not free:
                    raise ValueError("logo needs more tiles than the Japanese logo had")
                tiles[tb] = free.pop(0)
            rom[o + i] = tiles[tb]
    for tb, t in tiles.items():
        rom[chr_page0 + t * 16:chr_page0 + t * 16 + 16] = tb
    return len(tiles)


if __name__ == "__main__":
    # export the current logo for editing: python3 tools/knt_logo.py export <out.png>
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "export":
        save_png(draw(), sys.argv[2])
    else:
        g = logo()
        im = Image.new("RGB", (256, 96))
        for y in range(96):
            for x in range(256):
                im.putpixel((x, y), PAL[g[y][x]])
        im.resize((768, 288), Image.NEAREST).save(os.environ.get("OUT", "/tmp/logo_preview.png"))
