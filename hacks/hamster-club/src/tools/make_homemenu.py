"""Build patches/homemenu.ips: the English home (care) menu.

The home menu is not text: its labels are kana tiles in a raw 2bpp tileset
at 0xD4740 (0x32 tiles, loaded to 0x9000 by the routine at 0xA092) and two
32x32 tile maps in bank 0x36:
  0xDB000  BG map: the menu (it scrolls), items on rows 2, 4, ... 20, columns 2-8,
           with each dakuten as tile 07 on the row above
  0xDB800  window map: the "わざ いちらん" (trick list) box, rows 7-17, and
           the hamster box at the top (age line on row 3); attributes at 0xDBC00
           "わざN:" in columns 14-17
The kana tiles are used only by these two maps, so they are redrawn as
English letters (one tile per letter, in the dialogue font's style) and the
maps are rewritten.

Usage (game folder): python3 tools/make_homemenu.py
"""
from __future__ import annotations

import os
import sys

TK = os.environ.get("RHTK", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "toolkit"))
sys.path.insert(0, TK)
sys.path.insert(0, os.path.dirname(__file__))
from rhtk import patch  # noqa: E402
from make_font import FONT_OFF, GLYPHS  # noqa: E402

TILES = 0xD4740
BG, WIN = 0xDB000, 0xDB800
WIN_ATTR = 0xDBC00  # the window map's GBC attributes (palette per tile)
# kana tiles that only the two maps use; the letters are drawn over them
FREE = [0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x16, 0x17, 0x18,
        0x1C, 0x1D, 0x1E, 0x23, 0x25, 0x27, 0x29, 0x2A, 0x2B, 0x2D, 0x30,
        0x2F, 0x31]  # 0x2F/0x31 are the digits 7 and 8, which neither map uses
DAKUTEN = 0x07
# あそぶ ちょうきょう しつけ しゅつじょう いどう じょうたい のうりょく けっとう わざ けいれき
ITEMS = ["Play", "Train", "Habits", "Contest", "Move", "Status", "Stats", "Lineage", "Tricks",
         "Record"]
WIN_TITLE = (2, 11, " Tricks ")  # row, column, text over "わざ いちらん"
# age line in the window map, row 3: "生NNヶ月" (N months old) becomes
# "<cake>NNmo". make_hacks.py moves the digits from columns 6-7 to 5-6.
AGE_ROW = 3
BIRTH, MONTH = 0x14, 0x15  # the 生 and ヶ月 tiles, redrawn as a cake and "m"
CAKE = ["...#....",
        "...#....",
        ".######.",
        ".#....#.",
        ".######.",
        ".#....#.",
        "########",
        "........"]


def bitmap(rows):
    out = bytearray()
    for row in rows:
        b = sum(1 << (7 - x) for x, c in enumerate(row) if c == "#")
        out += bytes((b, b))
    return bytes(out)


def glyph(rom, ch):
    """2bpp bytes for one letter: lowercase from make_font, capitals from the ROM font."""
    if ch.islower():
        return bitmap(GLYPHS[ch])
    code = 0x7F + ord(ch) - ord("A")
    return rom[FONT_OFF + code * 16:FONT_OFF + code * 16 + 16]


def main():
    rom = open("rom/original.gbc", "rb").read()
    out = bytearray(rom)
    letters = sorted(set("".join(ITEMS) + WIN_TITLE[2]) - {" "})
    if len(letters) > len(FREE):
        sys.exit(f"{len(letters)} letters but only {len(FREE)} free tiles")
    tile = dict(zip(letters, FREE))
    tile[" "] = 0x00
    for t in FREE:
        out[TILES + t * 16:TILES + t * 16 + 16] = bytes(16)
    for ch in letters:
        t = tile[ch]
        out[TILES + t * 16:TILES + t * 16 + 16] = glyph(rom, ch)

    def put(base, row, col, text):
        for i, ch in enumerate(text):
            out[base + row * 32 + col + i] = tile[ch]

    for i, item in enumerate(ITEMS):
        row = 2 + 2 * i
        assert len(item) <= 7, item
        put(BG, row, 2, item.ljust(7))
        for c in range(1, 9):  # dakuten row above
            if out[BG + (row - 1) * 32 + c] == DAKUTEN:
                out[BG + (row - 1) * 32 + c] = 0
    row, col, text = WIN_TITLE
    put(WIN, row, col, text)
    for c in range(col, col + len(text)):
        if out[WIN + (row - 1) * 32 + c] == DAKUTEN:
            out[WIN + (row - 1) * 32 + c] = 0
    out[TILES + BIRTH * 16:TILES + BIRTH * 16 + 16] = bitmap(CAKE)
    out[TILES + MONTH * 16:TILES + MONTH * 16 + 16] = bitmap(GLYPHS["m"])
    a = WIN + AGE_ROW * 32
    assert out[a + 5] == BIRTH and out[a + 8] == MONTH, "age line moved"
    out[a + 3:a + 9] = bytes([0, BIRTH, 0, 0, MONTH, tile["o"]])
    pal = WIN_ATTR + AGE_ROW * 32  # the cake keeps the highlight palette 生 had
    assert out[pal + 4:pal + 6] == bytes([0, 3]), "age line palettes moved"
    out[pal + 4:pal + 6] = bytes([3, 2])
    for row in range(7, 18, 2):  # "わざN:" -> "  N:"
        put(WIN, row, 14, "  ")
        if out[WIN + (row - 1) * 32 + 15] == DAKUTEN:
            out[WIN + (row - 1) * 32 + 15] = 0
    os.makedirs("patches", exist_ok=True)
    with open("patches/homemenu.ips", "wb") as f:
        f.write(patch.ips_create(rom, bytes(out)))
    print(f"wrote patches/homemenu.ips ({len(letters)} letter tiles)")


if __name__ == "__main__":
    main()
