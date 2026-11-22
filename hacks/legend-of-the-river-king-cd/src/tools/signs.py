"""Village sign graphics, matching the Umi no Nushi patch: 宿 -> INN, 釣 -> a hook, 魚 -> a fish,
banner だんご -> a picture of a dango skewer.

The tiles are stored uncompressed (4bpp planar, 32 bytes each) in several map tilesets; the first
is at data.iso 0x6D000 (tile $600). Every disc copy of an original tile is replaced by content match.
"""
TILESET = 0x6D000
# Same art as the Umi no Nushi Tsuri patch (UmiToolkit/build/field_signs.py): INN, a hook, a fish.
# Umi's 12x12 pictures have a blank first column, dropped here for the 11-wide interior.
UMI_ART = {
    'inn': ["            ", "            ", "            ", " # #  # #  #", " # ## # ## #", " # ## # ## #",
            " # # ## # ##", " # # ## # ##", " # #  # #  #", "            ", "            ", "            "],
    'tackle': ["     ###    ", "     # #    ", "     ###    ", "      #     ", "      #     ", "      #     ",
               " #    #     ", " ##   #     ", " #    #     ", " #   #      ", "  ###       ", "            "],
    'fish': ["            ", "            ", "            ", "     ###    ", " #  ######  ", " ########## ",
             " ####### ###", " ########## ", " #  ######  ", "     ###    ", "            ", "            "],
}
SIGNS = {   # name: (2x2 tiles, inner rect x0,y0,x1,y1 inclusive, background colour, picture rows)
    'inn': ([[0x682, 0x683], [0x692, 0x693]], (2, 2, 12, 14), 0, [r[1:].replace(' ', '.') for r in UMI_ART['inn']]),
    'tackle': ([[0x686, 0x687], [0x696, 0x697]], (2, 2, 12, 14), 0, [r[1:].replace(' ', '.') for r in UMI_ART['tackle']]),
    'fish': ([[0x684, 0x685], [0x694, 0x695]], (2, 2, 12, 14), 0, [r[1:].replace(' ', '.') for r in UMI_ART['fish']]),
}
BANNER = ([[0x609, 0x60A], [0x619, 0x61A], [0x629, 0x62A], [0x639, 0x63A]], (5, 2, 11, 24), 1)
# Banner: a skewer of three dango (white, tan, green) on a brown stick instead of the word.
DANGO = ['.#####.', '#######', '#######', '#######', '#######', '.#####.']
DANGO_BALLS = ((2, 15), (9, 4), (16, 6))     # (top row, colour), the stick shows between them; banner interior is columns 5-11
STICK = 2
INK = 15

def dec(b):
    px = []
    for y in range(8):
        p = [b[y * 2], b[y * 2 + 1], b[16 + y * 2], b[17 + y * 2]]
        px.append([sum(((p[k] >> (7 - x)) & 1) << k for k in range(4)) for x in range(8)])
    return px

def enc(px):
    b = bytearray(32)
    for y in range(8):
        for x in range(8):
            c = px[y][x]
            for k, o in enumerate((y * 2, y * 2 + 1, 16 + y * 2, 17 + y * 2)):
                if (c >> k) & 1: b[o] |= 0x80 >> x
    return bytes(b)

def block(d, tiles):
    g = []
    for row in tiles:
        ts = [dec(d[TILESET + (n - 0x600) * 32:][:32]) for n in row]
        for y in range(8): g.append(sum((t[y] for t in ts), []))
    return g

def split(g, tiles):
    out = {}
    for r, row in enumerate(tiles):
        for c, n in enumerate(row):
            out[n] = enc([g[r * 8 + y][c * 8:c * 8 + 8] for y in range(8)])
    return out

def draw(g, rect, bg, rows, top):
    x0, y0, x1, y1 = rect
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if g[y][x] not in (bg,): g[y][x] = bg
    for dy, r in enumerate(rows):
        for dx, ch in enumerate(r):
            if ch == '#': g[top + dy][x0 + dx] = INK

def new_tiles(d):
    """{original 32 bytes: new 32 bytes}"""
    rep = {}
    for name, (tiles, rect, bg, rows) in SIGNS.items():
        g = block(d, tiles); orig = split(g, tiles)
        x0, y0, x1, y1 = rect
        draw(g, rect, bg, rows, y0 + (y1 - y0 + 1 - len(rows)) // 2)
        new = split(g, tiles)
        for n in orig: rep[d[TILESET + (n - 0x600) * 32:][:32]] = new[n]
    tiles, rect, bg = BANNER
    g = block(d, tiles); orig = split(g, tiles)
    for y in range(1, 26):                 # the old lettering reaches column 12
        for x in range(16):
            if g[y][x] == INK: g[y][x] = bg
    for y in range(1, 25): g[y][8] = STICK
    for top, col in DANGO_BALLS:
        for dy, r in enumerate(DANGO):
            for dx, ch in enumerate(r):
                if ch == '#': g[top + dy][5 + dx] = col
        if col == INK: g[top + 4][10] = 4      # shade on the white ball
        else: g[top + 1][6] = INK              # highlight
    new = split(g, tiles)
    for n in orig: rep[d[TILESET + (n - 0x600) * 32:][:32]] = new[n]
    return rep

def patch(t, data):
    """t: build_patch.Track, data: first-copy data (bytes). Returns number of tiles replaced."""
    import re
    n = 0
    for old, new in new_tiles(data).items():
        if old == new: continue
        for m in re.finditer(re.escape(old), data):
            if m.start() % 32: continue
            sec, o = divmod(m.start(), 2048); t.write(sec, o, new); n += 1
    return n
