# Game 3 Uocchi screens.
import tlabels
from lzscan import lz77
from namekbd import put_lz
from tilestr import render

# tank setup (set 0x1F6A7C at tile 0, map 0x1F6E98); option cells sit right of the cursor columns 11 and 15
TANK = dict(block=0x1f6a7c, maps=[0x1f6e98], blank=0x01, keep={0x19, 0x1a, 0x1b, 0x6d, 0x70, 0x78},
            # the title row is written by code with tiles 02-0C
            fixed=[(list(range(0x02, 0x0d)), 'Tank Settings', 'center')],
            labels=[(3, 3, 8, '. Depth', 'left'), (3, 12, 3, 'Deep', 'left'), (3, 16, 3, 'Low', 'left'),
                    (5, 3, 8, '. Current', 'left'), (5, 12, 3, 'On', 'left'), (5, 16, 3, 'Off', 'left'),
                    (7, 3, 8, '. Bottom', 'left'), (7, 12, 3, 'Sand', 'left'), (7, 16, 3, 'Rocks', 'left'),
                    (9, 2, 6, 'Done', 'left'),
                    (11, 2, 14, 'Water Purity', 'left'),
                    (12, 2, 8, ': OK', 'left'), (12, 12, 7, ': Back', 'left')])

# command menu (set 0x1F6FF4, map 0x1F7424); the digits 1-6 stay, the ・ after them becomes '.'
MENU = dict(block=0x1f6ff4, maps=[0x1f7424], blank=0x01, keep={0x18, 0x19, 0x1a, 0x1b, 0x1e, 0x1f, 0x6e, 0x70, 0x78},
            labels=[(1, 5, 10, 'Commands', 'center'),
                    (3, 5, 11, '. Fish Status', 'left'), (5, 5, 11, '. Feed', 'left'),
                    (7, 5, 11, '. Clean Tank', 'left'), (9, 5, 11, '. Tank Settings', 'left'),
                    (11, 5, 11, '. Ornaments', 'left'), (13, 5, 13, '. Quit Uocchi', 'left'),
                    (15, 2, 8, ': OK', 'left'), (16, 2, 9, ': Back', 'left')])

# fish status (set 0x1F7584, map 0x1F7A28); the name, length and hours are printed by code after the labels
FISH = dict(block=0x1f7584, maps=[0x1f7a28], blank=0x01, keep={0x02, 0x24, 0x2a, 0x2b, 0x32, 0x33, 0xda},
            labels=[(1, 4, 11, 'Fish Status', 'center'),
                    (3, 3, 6, 'Species', 'left'), (5, 3, 6, 'Length', 'left'),
                    (7, 3, 6, 'Age', 'left'), (7, 12, 6, ' hours', 'left'),
                    (11, 2, 5, 'Fullness', 'left'), (11, 11, 4, 'Stress', 'left'),
                    (15, 2, 8, ': Back', 'left')])

# tank view (set 0x1F5A9C): the bottom panel is written by code, 'N じかんけいか' uses tiles B0-B5
VIEW = dict(block=0x1f5a9c, fixed=[(list(range(0xb0, 0xb6)), ' hours', 'left')])

def apply(rom, allrefs):
    blk, ln = lz77(rom.d, VIEW['block'], limit=0x10000)
    blk = bytearray(blk)
    for ids, text, al in VIEW['fixed']:
        for t, tile in zip(ids, render(text, len(ids), align=al)):
            blk[t * 32:t * 32 + 32] = tile
    put_lz(rom, allrefs, VIEW['block'], ln, bytes(blk))
    apply_memo(rom, allrefs)
    out = {}
    for name, S in (('tank', TANK), ('menu', MENU), ('fish', FISH)):
        out[name] = tlabels.apply(rom, allrefs, S['block'], S['maps'], S['labels'], keep=S['keep'],
                                  blank=S['blank'], fixed=S.get('fixed', ()))
    return out

# Fishing Memo book (set 0x1BAEE8): 最高 / 平均 / 総数 are 3x2-tile labels in green on colour 14, 尾 is 1B-1E
MEMO = dict(block=0x1baee8, labels=[('Best', [0x50, 0x51, 0x52, 0x60, 0x61, 0x62]),
                                    ('Avg.', [0x53, 0x54, 0x55, 0x63, 0x64, 0x65]),
                                    ('Total', [0x56, 0x57, 0x58, 0x66, 0x67, 0x68])],
            erase=[0x1b, 0x1c, 0x1d, 0x1e], blank=0x08,
            # red 32x16 stamps on the memo page (OBJ, 8 tiles each, 1D order): 大物 and 育成 (Uocchi-raised fish)
            stamps=[(0x40, 'Big One'), (0x48, 'Raised')])

STAMP_INK = 4   # solid red in the stamp palette; 0 is transparent

def stamp_tiles(text):
    import font_en
    px = [[0] * 32 for _ in range(16)]
    for x in range(1, 31): px[0][x] = px[15][x] = STAMP_INK
    for y in range(1, 15): px[y][0] = px[y][31] = STAMP_INK
    sp = 2   # narrow space: 'Big One' has to fit the 30 px inside the frame
    w = sum(font_en.width(c) if c != ' ' else sp for c in text) - 1
    x0 = (32 - w + 1) // 2
    for c in text:
        if c != ' ':
            for y, row in enumerate(font_en.G[c]):
                for i, ch in enumerate(row):
                    if ch == '#': px[5 + y][x0 + i] = STAMP_INK
        x0 += font_en.width(c) if c != ' ' else sp
    out = []
    for ty in range(2):
        for tx in range(4):
            out.append(bytes(px[ty * 8 + y][tx * 8 + x] | (px[ty * 8 + y][tx * 8 + x + 1] << 4)
                             for y in range(8) for x in range(0, 8, 2)))
    return out

def recolour(tile, m):
    out = bytearray()
    for b in tile:
        lo, hi = b & 15, b >> 4
        out.append(m.get(lo, lo) | (m.get(hi, hi) << 4))
    return bytes(out)

def apply_memo(rom, allrefs):
    M = MEMO
    blk, ln = lz77(rom.d, M['block'], limit=0x10000)
    blk = bytearray(blk)
    for text, ids in M['labels']:
        # the numbers and 'cm' sit on the lower tile row, so the word goes there too
        for t, tile in zip(ids, [b'\x11' * 32] * 3 + render(text, 3)):
            blk[t * 32:t * 32 + 32] = recolour(bytes(tile), {1: 14, 3: 10})
    for base, text in M['stamps']:
        for k, tile in enumerate(stamp_tiles(text)):
            blk[(base + k) * 32:(base + k + 1) * 32] = tile
    b = M['blank']
    for t in M['erase']:
        blk[t * 32:t * 32 + 32] = blk[b * 32:b * 32 + 32]
    put_lz(rom, allrefs, M['block'], ln, bytes(blk))
