# Read kana tiles in menu blocks by matching them against the game's own 8x8 text font.
from lzscan import lz77
from jpdec import dec
rom = open('../rom/k34.gba', 'rb').read()
FONT = {'g3': 0x1b51dc, 'g4': 0x0d2220}

def mask(t):
    px = [[(t[y * 4 + x // 2] >> (4 * (x & 1))) & 15 for x in range(8)] for y in range(8)]
    from collections import Counter
    bg = Counter(sum(px, [])).most_common(1)[0][0]
    return tuple(tuple(1 if v != bg else 0 for v in r) for r in px)

_ref = {}
def ref(game):
    if game not in _ref:
        f = FONT[game]; r = {}
        for c in range(0xf0):
            if c in (0x8d, 0x8e): continue
            m = mask(rom[f + c * 32:f + c * 32 + 32])
            if any(sum(m, ())): r.setdefault(m, c)
        _ref[game] = r
    return _ref[game]

def read_tile(t, game):
    m = mask(t)
    r = ref(game)
    if m in r: return dec(bytes([r[m]]), game)
    # tolerate a 1-pixel shift / small diffs
    best, bd = None, 99
    for k, c in r.items():
        d = sum(a != b for ra, rb in zip(k, m) for a, b in zip(ra, rb))
        if d < bd: best, bd = c, d
    return dec(bytes([best]), game) if bd <= 4 else '?'

def read_block(off, game):
    d, _ = lz77(rom, off, limit=0x10000)
    return {i: read_tile(d[i * 32:i * 32 + 32], game) for i in range(len(d) // 32) if any(d[i * 32:i * 32 + 32])}
