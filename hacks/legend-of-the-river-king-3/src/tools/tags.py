"""Small raw sprite graphics with baked-in Japanese, redrawn in English."""

# 装備 ("equipped") tag on the 32x32 item frame (raw 4bpp, 1D, 4x4 tiles). Colour a = dark box, b = white text,
# e/f = the orange frame. The box covers x 0-20, y 1-9; the frame runs e,f,e along the top and left edges.
EQUIP_TAG = 0x36FC5C
EQUIP_TEXT = {
    'E': ['###', '#..', '#..', '##.', '#..', '#..', '###'],
    'Q': ['.#.', '#.#', '#.#', '#.#', '#.#', '.#.', '..#'],
    'U': ['#.#', '#.#', '#.#', '#.#', '#.#', '#.#', '###'],
    'I': ['###', '.#.', '.#.', '.#.', '.#.', '.#.', '###'],
    'P': ['##.', '#.#', '#.#', '##.', '#..', '#..', '#..'],
}

def _put(rom, base, x, y, c):
    o = base + ((y // 8) * 4 + x // 8) * 32 + (y % 8) * 4 + (x % 8) // 2
    rom[o] = (rom[o] & 0x0F) | (c << 4) if x & 1 else (rom[o] & 0xF0) | c

def patch_equip_tag(rom):
    for y in range(11):
        for x in range(22):
            m = min(x, y)
            frame = (0xE, 0xF, 0xE)[m] if m < 3 else 0
            _put(rom, EQUIP_TAG, x, y, 0xA if 1 <= y <= 9 and x <= 20 else frame)
    for i, ch in enumerate('EQUIP'):
        for y, row in enumerate(EQUIP_TEXT[ch]):
            for x, c in enumerate(row):
                if c == '#': _put(rom, EQUIP_TAG, 1 + 4 * i + x, 2 + y, 0xB)
