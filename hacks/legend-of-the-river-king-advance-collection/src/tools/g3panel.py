# Game 3 status panels (field status/command, tackle, creel, battle). They are LZ77 maps over a shared
# 48-tile set at tile D0 (block 0x1B6A04) plus small per-panel sets loaded at C0, at DA (place name) and
# at E0 (bait/lure/fly word). The Japanese reuses kana tiles between words; English gets a tile run per word.
import struct
from lzscan import lz77
from namekbd import put_lz
from tilestr import render

FF = 0xff                       # blank panel tile
MAIN = 0x1b6a04                 # tiles D0-FF
MAIN_WORDS = ['HP', 'Yen', 'EXP']
MAIN_SLOTS = list(range(0xe3, 0xf6))            # E2 stays blank (the creel panel uses it); FE is the cursor
# The field status panel has no set of its own at C0, so it gets one: its loader is pointed at a copy of the
# shared set with 16 tiles in front, loaded at C0 (BG and the OBJ copy the cursor uses, so FE stays put).
STATUS_SITE = 0x84734                           # literal pool: set, BG dest, OBJ dest
STATUS_WORDS = ['Fish', 'Go', 'Eat', 'Items', 'Gear', 'Bag', 'Cmd']
# the first command is written by code: つり (Fish) or いどう (Go, when travelling); movs r3,#tile
CURSOR_CODE = [(0x84946, 'Fish', 0), (0x84962, 'Fish', 1), (0x8497e, 'Fish', 2),
               (0x849b2, 'Go', 0), (0x849ce, 'Go', 1), (0x849ea, 'Go', 2)]

# place names: one 6-tile set per place at DA-DF (table 0x1FE944), drawn by the strings at table 0x1FE9B0
PLACES = ['Stream', 'Upper Lake', 'Creek', 'Plains Lake', 'Mirage Lake']
PLACE_TAB, PLACE_STR = 0x1fe944, 0x1fe9b0
# bait word at E0-E2 by fishing style (table 0x1FE958: float, casting, lure, fly)
VARIANTS = {0x1b6d08: 'Bait', 0x1b6d34: 'Lure', 0x1b6d64: 'Fly'}
# per-panel sets at C0
CBLOCKS = {0x1b6e30: ['Rod', 'Bait', 'Lure', 'Fly', 'Hook', 'Items'], 0x1b6f74: ['Capacity', 'Total', 'Bag'],
           0x1eeaf4: ['Fight', 'Run', 'Cmd', 'Eat'], 'status': STATUS_WORDS}

def ntiles(word):
    import font_en
    w = sum(font_en.width(c) if c != ' ' else 3 for c in word)   # includes 1 px lead-in from render()
    return -(-w // 8)

def alloc(words, slots):
    out, i = {}, 0
    for w in words:
        n = ntiles(w)
        out[w] = slots[i:i + n]; i += n
    assert i <= len(slots), (words, i, len(slots))
    return out

M = alloc(MAIN_WORDS, MAIN_SLOTS)
C = {b: alloc(ws, list(range(0xc0, 0xd0))) for b, ws in CBLOCKS.items()}

def tiles_of(word, block=None):
    return (C[block] if block else M)[word]

# map edits: (row, col, cells, word, cblock or None); cells are filled with the word then blank
def title(word, cb):
    return [(0, 12, [0xfb, FF, (word, cb), FF, 0xfb])]
STATUS = [(1, 1, 5, 'HP', None), (2, 1, 5, 'Yen', None), (3, 1, 5, 'EXP', None)]
MAPS = {
    0x1b6d9c: title('Cmd', 'status') + STATUS +
              [(1, 12, 3, 'Fish', 'status'), (1, 16, 3, 'Eat', 'status'), (2, 16, 3, 'Items', 'status'),
               (3, 12, 3, 'Gear', 'status'), (3, 16, 3, 'Bag', 'status')],
    0x1b6ee8: STATUS + [(1, 12, 3, 'Rod', 0x1b6e30), (1, 16, 3, 'Bait', 0x1b6e30), (2, 12, 3, 'Lure', 0x1b6e30),
                        (2, 16, 3, 'Fly', 0x1b6e30), (3, 12, 3, 'Hook', 0x1b6e30), (3, 16, 3, 'Items', 0x1b6e30)],
    0x1b6fec: title('Bag', 0x1b6f74) + STATUS +
              [(1, 11, 5, 'Capacity', 0x1b6f74), (3, 11, 4, 'Total', 0x1b6f74)],
    0x1ee990: title('Bag', 0x1b6f74) + STATUS +
              [(1, 11, 5, 'Capacity', 0x1b6f74), (3, 11, 4, 'Total', 0x1b6f74)],
    0x1eeb48: title('Cmd', 0x1eeaf4) + STATUS + [(1, 13, 4, 'Fight', 0x1eeaf4), (2, 13, 3, 'Eat', 0x1eeaf4),
                                                (3, 13, 3, 'Run', 0x1eeaf4)],
}

def draw(blk, base, word, ids):
    for t, tile in zip(ids, render(word, len(ids), align='left')):
        i = t - base
        blk[i * 32:i * 32 + 32] = tile

def patch_map(m, edits):
    hw = list(struct.unpack('<%dH' % (len(m) // 2), m))
    def put(r, c, t):
        i = r * 32 + c
        hw[i] = (hw[i] & 0xfc00) | t
    for e in edits:
        if isinstance(e[2], list):
            r, c, seq = e
            col = c
            for x in seq:
                for t in (tiles_of(*x) if isinstance(x, tuple) else [x]):
                    put(r, col, t); col += 1
            continue
        r, c, cells, word, cb = e
        ids = tiles_of(word, cb)
        assert len(ids) <= cells, (word, ids, cells)
        for k in range(cells):
            put(r, c + k, ids[k] if k < len(ids) else FF)
    return struct.pack('<%dH' % len(hw), *hw)

def small_block(rom, allrefs, off, words_ids, base, n):
    blk = bytearray(32 * n)
    for t in range(n):                 # background colour 1
        blk[t * 32:t * 32 + 32] = b'\x11' * 32
    for w, ids in words_ids.items():
        draw(blk, base, w, ids)
    _, ln = lz77(rom.d, off, limit=0x10000)
    put_lz(rom, allrefs, off, ln, bytes(blk))

def apply(rom, allrefs):
    blk, ln = lz77(rom.d, MAIN, limit=0x10000)
    blk = bytearray(blk)
    for w, ids in M.items():
        draw(blk, 0xd0, w, ids)
    put_lz(rom, allrefs, MAIN, ln, bytes(blk))
    for off, w in VARIANTS.items():
        small_block(rom, allrefs, off, {w: [0xe0, 0xe1, 0xe2]}, 0xe0, 3)
    for off, ws in CBLOCKS.items():
        if off == 'status': continue
        n = max(t for ids in C[off].values() for t in ids) - 0xc0 + 1
        small_block(rom, allrefs, off, C[off], 0xc0, n)
    # status panel: 16 own tiles + the shared set, at C0
    pre = bytearray(b'\x11' * 32 * 16)
    for w, ids in C['status'].items():
        draw(pre, 0xc0, w, ids)
    from gfx import lz77_compress
    a = rom.put(lz77_compress(bytes(pre) + bytes(blk)), align=4)
    pool = STATUS_SITE
    assert struct.unpack_from('<3I', rom.d, pool) == (0x08000000 + MAIN, 0x06001a00, 0x06011a00)
    rom.w(pool, struct.pack('<3I', 0x08000000 + a, 0x06001800, 0x06011800))
    for addr, word, k in CURSOR_CODE:
        ids = C['status'][word]
        assert rom.d[addr + 1] == 0x23
        rom.w(addr, bytes([ids[k] if k < len(ids) else FF]))
    # place names: new 6-tile sets and strings
    for i, name in enumerate(PLACES):
        import font_en
        w = sum(font_en.width(c) if c != ' ' else 2 for c in name) - 1
        assert w <= 48, name
        ids = list(range(0xda, 0xda + -(-w // 8)))
        b = bytearray(b'\x11' * 32 * 6)
        for t, tile in zip(ids, render_tight(name, len(ids))):
            b[(t - 0xda) * 32:(t - 0xda + 1) * 32] = tile
        from gfx import lz77_compress
        a = rom.put(lz77_compress(bytes(b)), align=4)
        rom.w(PLACE_TAB + 4 * i, struct.pack('<I', 0x08000000 + a))
        s = ([0xfd] if len(ids) <= 5 else []) + ids + [0xff]
        sa = rom.put(b''.join(struct.pack('<H', v) for v in s), align=2)
        rom.w(PLACE_STR + 4 * i, struct.pack('<I', 0x08000000 + sa))
    for off, edits in MAPS.items():
        m, mln = lz77(rom.d, off, limit=0x10000)
        put_lz(rom, allrefs, off, mln, patch_map(m, edits))

def render_tight(text, n):
    """render() with 2 px word spaces, for names that are a pixel too wide."""
    import font_en
    from gfx import to_tiles
    px = [[1] * (n * 8) for _ in range(8)]
    x = 0
    for ch in text:
        if ch == ' ': x += 2; continue
        for y, row in enumerate(font_en.G[ch]):
            for k, c in enumerate(row):
                if c == '#' and x + k < n * 8 and y + 1 < 8: px[y + 1][x + k] = 3
        x += font_en.width(ch)
    return to_tiles(px)
