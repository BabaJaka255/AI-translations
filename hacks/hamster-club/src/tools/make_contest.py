"""Build patches/contest.ips: English for the contest text that is not a script block.

Three kinds of fixes, all found by playing every event (see notes/rom.md
"Contest screens"):

1. Text the contest code builds in RAM (0xDBD4) with one immediate store per
   character, "ld a,XX / ld [de],a / inc de / inc b" (3e XX 12 13 04): the
   "エントリーナンバー N" header and the "<name>さんです" lines in banks 04, 07
   and 08. Each store gets an English character; unused stores become NOPs, so
   the length counter in b stays right. 0x7E (dakuten) takes no column in the
   Japanese, so a line keeps its 18 columns only if the English counts it.
2. Templates the code copies to RAM and fills with digits: the Pretty Cup
   judges' scores (bank 08) and the Leapfrog result (bank 07). The digit
   positions stay; only the words around them change.
3. Graphics: the Seed Catch score bar labels, the "results" board, the
   1st/2nd/3rd/last boards and the four grading stamps of the podium screen.

Usage (game folder): python3 tools/make_contest.py
"""
from __future__ import annotations

import os
import sys

TK = os.environ.get("RHTK", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "toolkit"))
sys.path.insert(0, TK)
sys.path.insert(0, os.path.dirname(__file__))
from rhtk import patch  # noqa: E402
from rhtk.table import Table  # noqa: E402
from make_font import FONT_OFF  # noqa: E402

EN = Table.load(os.path.join(os.path.dirname(__file__), "..", "tables", "en.tbl"))
NOP5 = bytes(5)

# --- 1. immediate stores: (offset, number of stores, English) --------------
STORES = [
    # "エントリーナンバー " + digit + 7 spaces + name: 18 columns before the name
    (0x108AC, 11, "Contestant "), (0x108F5, 7, " " * 6),   # bank 04 Charm Awards
    (0x1CAC7, 11, "Contestant "), (0x1CB10, 7, " " * 6),   # bank 07 Leapfrog
    (0x21C7F, 11, "Contestant "), (0x21CC8, 7, " " * 6),   # bank 08 Pretty Cup
    # after the name: "　さんです！！" and "さんです　どうぞー！"
    (0x10922, 8, "-san!"), (0x10983, 13, "-san, go!"),
    (0x21CF5, 8, "-san!"), (0x21D56, 13, "-san, go!"),
]

# --- 2. templates: (offset, original JP bytes, English with '#' = keep byte) --
TEMPLATES = [
    # Pretty Cup scores, copied to 0xDBFC; two-digit scores land on the "##"s,
    # the total on the last "##". " 0てん、" x3, 3 spaces, x2, 2 spaces, "50てーん！"
    (0x22B92, "006f132e9e006f132e9e006f132e9e000000006f132e9e006f132e9e0000746f137a2e7b",
     "##pt,##pt,##pt,   ##pt,##pt,  ##pts!"),
    # Leapfrog result, copied to 0xDBD4; digits are written at 5, 7, 8, 10, 11.
    # "きろくは、0M00．00です" and "きろくは、0M00です"  UNSURE: M is meters
    (0x1D3E8, "072b081a9e6f8b6f6fe26f6f137e0d", "Jump #m##.##   "),
    (0x1D40B, "072b081a9e6f8b6f6f137e0d", "Jump #m##   "),
]


def stores(text, n):
    out = bytearray()
    code = EN.encode(text)
    assert len(code) <= n, text
    for b in code:
        out += bytes((0x3E, b, 0x12, 0x13, 0x04))
    return bytes(out) + NOP5 * (n - len(code))


# --- 3. graphics -----------------------------------------------------------
def font_rows(rom, ch):
    """8 rows of 8 bits for a capital, digit or '!' from the ROM font."""
    code = EN.encode(ch)[0]
    o = FONT_OFF + code * 16
    return [rom[o + 2 * y] | rom[o + 2 * y + 1] for y in range(8)]


def glyph_cols(rows):
    used = [x for x in range(8) if any((r >> (7 - x)) & 1 for r in rows)]
    return (used[0], used[-1]) if used else (0, 2)


def draw_text(canvas, rom, text, cx, y, color, tall=False, gap=1):
    """Draw text centered on column cx (proportional, gap px between letters)."""
    parts = []
    for ch in text:
        if ch == " ":
            parts.append((None, 3))
            continue
        rows = font_rows(rom, ch)
        a, b = glyph_cols(rows)
        parts.append(((rows, a), b - a + 1))
    width = sum(w for _, w in parts) + gap * (len(parts) - 1)
    x = cx - width // 2
    for g, w in parts:
        if g:
            rows, a = g
            for gy, r in enumerate(rows):
                for gx in range(w):
                    if (r >> (7 - (a + gx))) & 1:
                        for dy in ((0, 1) if tall else (0,)):
                            canvas[y + gy * (2 if tall else 1) + dy][x + gx] = color
        x += w + gap


def tile_from(pix, tx, ty):
    out = bytearray()
    for y in range(8):
        row = pix[ty * 8 + y][tx * 8:tx * 8 + 8]
        out += bytes((sum((c & 1) << (7 - x) for x, c in enumerate(row)),
                      sum((c >> 1) << (7 - x) for x, c in enumerate(row))))
    return bytes(out)


def tile_pixels(data):
    return [[((data[2 * y] >> (7 - x)) & 1) | (((data[2 * y + 1] >> (7 - x)) & 1) << 1)
             for x in range(8)] for y in range(8)]


# Seed Catch score bar: "タネ 00 マメ 00 じかん 50" -> "SEED 00 BEAN 00 TIME 50".
# The labels are kana tiles in the two race tilesets (loaded by code at
# 0x13960-0x139A0); they are found by their pixels. 3x7 capitals, color 3.
SEED_TILESETS = [(0xB11A0, 0x4A0), (0xB2430, 0x4A0)]
# the dakuten of じ sits in the map row above the labels: (map cell, tile)
SEED_DAKUTEN = [(0xAD800 + 15 * 32 + 13, 0x2F), (0xB3000 + 15 * 32 + 13, 0x2E)]
MINI = {
    "S": ["###", "#..", "#..", "###", "..#", "..#", "###"],
    "E": ["###", "#..", "#..", "###", "#..", "#..", "###"],
    "D": ["##.", "#.#", "#.#", "#.#", "#.#", "#.#", "##."],
    "B": ["##.", "#.#", "#.#", "##.", "#.#", "#.#", "##."],
    "A": [".#.", "#.#", "#.#", "###", "#.#", "#.#", "#.#"],
    "N": ["#..#", "##.#", "##.#", "#.##", "#.##", "#..#", "#..#"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
}
# (original kana tile pixels as 2bpp hex, in order) -> label
SEED_LABELS = [
    (["40407e7e4242a2a21212040438380000", "3030fcfc040408083434d2d210100000"], "SEED"),
    (["fefe0202020244442828101008080000", "040404044444282810102828c4c40000"], "BEAN"),
    (["40404040404040404040444438380000", "4444f2f24a4a48484848888810100000",
      "1010101020202020525252528c8c0000"], "TIME"),
]


def mini_label(text, tiles):
    w = tiles * 8
    pix = [[0] * w for _ in range(8)]
    width = sum(len(MINI[c][0]) for c in text) + len(text) - 1
    x = (w - width + 1) // 2
    for c in text:
        for y, row in enumerate(MINI[c]):
            for dx, p in enumerate(row):
                if p == "#":
                    pix[y][x + dx] = 3
        x += len(MINI[c][0]) + 1
    return [tile_from(pix, t, 0) for t in range(tiles)]


# Podium screen (results of every event). Tilesets: 0xBE190 -> 0x8000,
# 0xBD9B0 -> 0x8800, 0xBD1B0 -> 0x9000 (BG uses 0x8800 addressing); maps are
# 0x400 bytes with attributes 0x400 later. The board inside each map is
# rows 3-9, columns 5-14, black (tile 0x20) with white letters.
TS_LO, TS_HI = 0xBD9B0, 0xBD1B0   # tiles 0x80-0xFD and 0x00-0x7F
RESULTS_TILES = 0xBDF80           # 結果発表: 8x2 tiles (0xDD-0xEC), black on light
RESULTS_MAP = 0xB9800
BLACK = 0x20
RANK_BOARDS = [(0xBA000, "1ST"), (0xBB000, "2ND"), (0xB4000, "3RD"), (0xB5000, "LAST")]
# grading stamps (the classic teacher's stamps), circle at rows 3-9, columns 7-12
STAMPS = [
    (0xBA800, ["GREAT", "JOB!"]),          # たいへんよくできました
    (0xBB800, ["GOOD", "JOB"]),            # まあまあよくできました
    (0xB4800, ["TRY", "MORE"]),          # もうすこしガンバリましょう
    (0xB5800, ["NOT", "EVEN", "CLOSE"]),   # もうぜんぜんダメです
]
ALL_MAPS = [RESULTS_MAP] + [m for m, _ in RANK_BOARDS] + [m for m, _ in STAMPS]


def tile_addr(t):
    return TS_LO + (t - 0x80) * 16 if t >= 0x80 else TS_HI + t * 16


def in_board(row, col):
    return 3 <= row <= 9 and 5 <= col <= 14


def podium(rom, out):
    # tiles that only ever appear inside the boards can be redrawn freely
    inside, outside = set(), set()
    for m in ALL_MAPS:
        for row in range(32):
            for col in range(32):
                t = rom[m + row * 32 + col]
                (inside if m != RESULTS_MAP and in_board(row, col) else outside).add(t)
    pool = sorted(inside - outside - {BLACK})
    assert all(rom[tile_addr(BLACK) + i] == 0xFF for i in range(16)), "tile 0x20 is not black"
    made = {}

    def place(data):
        if data == b"\xff" * 16:
            return BLACK
        if data not in made:
            if not pool:
                sys.exit("podium boards: out of free tiles")
            t = pool.pop(0)
            out[tile_addr(t):tile_addr(t) + 16] = data
            made[data] = t
        return made[data]

    def board(m, r0, c0, rows, cols, pix):
        for ty in range(rows):
            for tx in range(cols):
                out[m + (r0 + ty) * 32 + c0 + tx] = place(tile_from(pix, tx, ty))

    for m, text in RANK_BOARDS:
        pix = [[3] * 80 for _ in range(16)]
        draw_text(pix, rom, text, 40, 0, 0, tall=True, gap=2)
        board(m, 5, 5, 2, 10, pix)
    for m, lines in STAMPS:
        # the stamp as it is, then everything between the left and right edges
        # of the ring erased, row by row
        pix = [[3] * 48 for _ in range(56)]
        for ty in range(7):
            for tx in range(6):
                t = rom[m + (3 + ty) * 32 + 7 + tx]
                for y, row in enumerate(tile_pixels(rom[tile_addr(t):tile_addr(t) + 16])):
                    pix[ty * 8 + y][tx * 8:tx * 8 + 8] = row
        for y in range(56):
            xs = [x for x in range(48) if pix[y][x] != 3]
            if not xs:
                continue
            left = xs[0]
            while left + 1 < 48 and pix[y][left + 1] != 3:
                left += 1
            right = xs[-1]
            while right - 1 > left and pix[y][right - 1] != 3:
                right -= 1
            if right - left > 6:
                for x in range(left + 1, right):
                    pix[y][x] = 3
        step = 10 if len(lines) < 3 else 9  # the ring narrows toward the bottom
        top = 27 - (len(lines) * step - 2) // 2
        for i, line in enumerate(lines):
            draw_text(pix, rom, line, 24, top + i * step, 0)
        board(m, 3, 7, 7, 6, pix)
    # results board: one 64x16 strip of tiles 0xDD-0xEC, text color 3 on 0
    pix = [[0] * 64 for _ in range(16)]
    draw_text(pix, rom, "RESULTS", 32, 0, 3, tall=True, gap=2)
    for t in range(16):
        o = RESULTS_TILES + t * 16
        out[o:o + 16] = tile_from(pix, t % 8, t // 8)
    return len(made), len(pool)


def main():
    rom = open("rom/original.gbc", "rb").read()
    out = bytearray(rom)
    for off, n, text in STORES:
        old = rom[off:off + 5 * n]
        assert all(old[i] == 0x3E and old[i + 2:i + 5] == b"\x12\x13\x04" for i in range(0, 5 * n, 5)), hex(off)
        out[off:off + 5 * n] = stores(text, n)
    for off, jp, en in TEMPLATES:
        jp = bytes.fromhex(jp)
        if rom[off:off + len(jp)] != jp:
            sys.exit(f"template at 0x{off:X} moved")
        assert len(en) == len(jp), en
        for i, ch in enumerate(en):
            if ch != "#":
                out[off + i] = EN.encode(ch)[0]
    for base, size in SEED_TILESETS:
        for kana, label in SEED_LABELS:
            new = mini_label(label, len(kana))
            for old, data in zip(kana, new):
                old = bytes.fromhex(old)
                i = rom.find(old, base, base + size)
                assert i >= 0 and (i - base) % 16 == 0, (hex(base), label)
                out[i:i + 16] = data
    for cell, tile in SEED_DAKUTEN:
        assert rom[cell] == tile, hex(cell)
        out[cell] = 0x00
    used, left = podium(rom, out)
    os.makedirs("patches", exist_ok=True)
    with open("patches/contest.ips", "wb") as f:
        f.write(patch.ips_create(rom, bytes(out)))
    print(f"wrote patches/contest.ips ({len(STORES)} stored strings, {len(TEMPLATES)} templates, "
          f"{used} board tiles, {left} spare)")


if __name__ == "__main__":
    main()
