"""English title menu (Start / Resume / Guide), drawn into the six 16x16 menu sprites.

Each row is two sprites; the right one is moved from x=104 to x=96 so the pair is a
contiguous 32x16 strip. Sprite data is raw 4bpp planar on the disc (sector 138 area).
"""
G = {  # rows top to bottom, all glyphs end on the baseline row
 'S': ['.###.', '#...#', '#....', '#....', '.#...', '..##.', '....#', '....#', '....#', '#...#', '.###.'],
 'R': ['####.', '#...#', '#...#', '#...#', '#...#', '####.', '#.#..', '#..#.', '#..#.', '#...#', '#...#'],
 'G': ['.###.', '#...#', '#....', '#....', '#....', '#.###', '#...#', '#...#', '#...#', '#..##', '.##.#'],
 't': ['.#.', '.#.', '###', '.#.', '.#.', '.#.', '.#.', '.#.', '..#'],
 'a': ['.##.', '...#', '.###', '#..#', '#..#', '#..#', '.###'],
 'r': ['#.##', '##..', '#...', '#...', '#...', '#...', '#...'],
 'e': ['.##.', '#..#', '#..#', '####', '#...', '#..#', '.##.'],
 's': ['.###', '#...', '#...', '.##.', '...#', '...#', '###.'],
 'u': ['#..#', '#..#', '#..#', '#..#', '#..#', '#..#', '.###'],
 'm': ['##.#.', '#.#.#', '#.#.#', '#.#.#', '#.#.#', '#.#.#', '#.#.#'],
 'i': ['#', '.', '#', '#', '#', '#', '#', '#', '#'],
 'd': ['...#', '...#', '...#', '...#', '.###', '#..#', '#..#', '#..#', '#..#', '#..#', '.###'],
}
BASE = 13
# (left sprite offset, right sprite offset) in data.iso, word, x start
ROWS = [((0x45700, 0x45780), 'Start', 1), ((0x45F80, 0x46700), 'Resume', 0), ((0x46F80, 0x46B00), 'Guide', 1)]
XPOS = (0x11E94, 0x11E9E, 0x11EA8)   # "lda #$88 / sta $287a|$2972|$29b2": right column x

def strip(word, x0, color=15):
    px = [[0] * 32 for _ in range(16)]
    x = x0
    for ch in word:
        g = G[ch]; top = BASE + 1 - len(g)
        for y, row in enumerate(g):
            for i, c in enumerate(row):
                if c == '#': px[top + y][x + i] = color
        x += len(g[0]) + 1
    assert x - 1 <= 32, word
    return px

def sprite(px, xoff):
    out = bytearray(128)
    for p in range(4):
        for y in range(16):
            w = 0
            for x in range(16):
                if (px[y][xoff + x] >> p) & 1: w |= 0x8000 >> x
            out[p * 32 + y * 2] = w & 0xFF; out[p * 32 + y * 2 + 1] = w >> 8
    return bytes(out)

def patches():
    """yield (data.iso offset, bytes, expected original prefix)"""
    for (l, r), word, x0 in ROWS:
        px = strip(word, x0)
        yield l, sprite(px, 0), None
        yield r, sprite(px, 16), None
    for o in XPOS:
        yield o + 1, b'\x80', b'\x88'

if __name__ == '__main__':
    for _, word, x0 in ROWS:
        for row in strip(word, x0): print(''.join('#' if c else '.' for c in row))
        print()
