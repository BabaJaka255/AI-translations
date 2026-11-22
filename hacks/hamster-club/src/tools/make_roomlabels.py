"""Build patches/roomlabels.ips: the English icon captions on the room and cage screens.

The box at the bottom of the cage screen names the icon under the cursor. The
captions are not text: they are tile map rows in bank 02 (0x8300-0x84FF, 32
bytes a row, a box border tile at each end) drawn in a small font, a raw 2bpp
tileset at 0xFC000 that the routine at 0x98DA loads to 0x8800 (tiles 0x80-0xDA).
The small font has no Latin letters, and its hiragana tiles 0x81-0x97 are used
only by these captions, so they are redrawn as English letters and the rows
are rewritten.

The cage view (one cage, icons for cleaning, items, food and status) does the
same with its own glyphs: tiles 0xE0-0xEE of a 32-tile set at 0xFFC90 that the
routine at 0x9BB7 loads to 0x8E00, and caption maps of 8-byte rows (7 columns
and a border tile; a dakuten row above each text row) at 0x898C and 0x8A0C, one
set per box style.

Usage (game folder): python3 tools/make_roomlabels.py
"""
from __future__ import annotations

import os
import sys

TK = os.environ.get("RHTK", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "toolkit"))
sys.path.insert(0, TK)
sys.path.insert(0, os.path.dirname(__file__))
from rhtk import patch  # noqa: E402
from make_homemenu import CAKE, bitmap, glyph  # noqa: E402
from make_font import GLYPHS  # noqa: E402

TILES = 0xFC000  # tile 0x80 (blank); the font is tiles 0x80-0xDA
FREE = list(range(0x81, 0x98))  # あ..ん, used only by the captions
DAKUTEN = 0x9B
# (map row offset, text): ハムスターいちらん, ハムスターくらぶ, スケジュール, すすめる
LABELS = [(0x8320, "Hamster List"), (0x8360, "Hamster Club"), (0x83A0, "Schedule"),
          (0x83E0, "Next Week")]
COL, WIDTH = 2, 17  # text columns 2-18 between the borders

CAGE_TILES = 0xFFC90  # tile 0xE0
CAGE_FREE = list(range(0xE0, 0xEF))  # the caption kana (and 0xE3, their dakuten)
CAGE_DAKUTEN = 0xE3
# text rows: ケージそうじ/そうじ, アイテム, しょくじ, ようす, in two box styles
CAGE_LABELS = [(0x8994, "Clean"), (0x89A4, "Items"), (0x89B4, "Food"), (0x89C4, "Status"),
               (0x8A14, "Clean"), (0x8A24, "Items"), (0x8A34, "Food"), (0x8A44, "Status")]
CAGE_WIDTH = 7
# hamster box in the cage view: window map 0xD9800 (attributes 0xD9C00), row 3 is
# "生NNヶ月" like the home screen; its tileset (0xD4170, a copy at 0xE3470) has 生
# and ヶ月 as tiles 0x15/0x16. They become a cake and "m", and the "o" caption
# glyph goes after them.
AGE_MAP, AGE_ATTR, AGE_ROW = 0xD9800, 0xD9C00, 3
AGE_TILESETS = [0xD4170, 0xE3470]
AGE_BIRTH, AGE_MONTH = 0x15, 0x16


def put_glyphs(rom, out, base, first, free, text):
    """Redraw tiles `free` (numbered from `first` at `base`) as the letters of text."""
    letters = sorted(set(text) - {" "})
    if len(letters) > len(free):
        sys.exit(f"{len(letters)} letters but only {len(free)} free tiles")
    tile = dict(zip(letters, free))
    for t in free:
        out[base + (t - first) * 16:base + (t - first) * 16 + 16] = bytes(16)
    for ch in letters:
        t = tile[ch]
        out[base + (t - first) * 16:base + (t - first) * 16 + 16] = glyph(rom, ch)
    return tile


def main():
    rom = open("rom/original.gbc", "rb").read()
    out = bytearray(rom)
    tile = put_glyphs(rom, out, TILES, 0x80, FREE, "".join(t for _, t in LABELS))
    tile[" "] = 0x80
    for row, text in LABELS:
        assert rom[row] == 0xC8 and rom[row + 19] == 0xC9, f"no caption row at 0x{row:X}"
        assert len(text) <= WIDTH, text
        out[row + COL:row + COL + WIDTH] = bytes(tile[c] for c in text.ljust(WIDTH))
        above = row - 32  # the dakuten row
        for c in range(1, 19):
            if out[above + c] == DAKUTEN:
                out[above + c] = 0x80
    ctile = put_glyphs(rom, out, CAGE_TILES, 0xE0, CAGE_FREE, "".join(t for _, t in CAGE_LABELS))
    ctile[" "] = 0x00
    for row, text in CAGE_LABELS:
        assert rom[row + 7] in (0x0B, 0x0F) and rom[row - 1] in (0x0B, 0x0F), f"no caption row at 0x{row:X}"
        assert len(text) <= CAGE_WIDTH, text
        out[row:row + CAGE_WIDTH] = bytes(ctile[c] for c in text.ljust(CAGE_WIDTH))
        out[row - 8:row - 8 + CAGE_WIDTH] = bytes(CAGE_WIDTH)  # the dakuten row
    for base in AGE_TILESETS:
        out[base + AGE_BIRTH * 16:base + AGE_BIRTH * 16 + 16] = bitmap(CAKE)
        out[base + AGE_MONTH * 16:base + AGE_MONTH * 16 + 16] = bitmap(GLYPHS["m"])
    a = AGE_MAP + AGE_ROW * 32
    assert out[a + 4] == AGE_BIRTH and out[a + 7] == AGE_MONTH and out[a + 8] == 0, "age line moved"
    out[a + 8] = ctile["o"]
    out[AGE_ATTR + AGE_ROW * 32 + 8] = out[AGE_ATTR + AGE_ROW * 32 + 7]
    os.makedirs("patches", exist_ok=True)
    with open("patches/roomlabels.ips", "wb") as f:
        f.write(patch.ips_create(rom, bytes(out)))
    print(f"wrote patches/roomlabels.ips ({len(tile) - 1} + {len(ctile) - 1} letter tiles)")


if __name__ == "__main__":
    main()
