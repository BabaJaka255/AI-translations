"""Build patches/keyboard.ips: an English name-entry screen.

The screen has three pages, each a 32x18 tile map in bank 0x36 and a list of
the character under each cursor position in bank 02 (notes/rom.md):
  page 0 (hiragana)  map 0xD8000, list 0xB981 (57 positions)
  page 1 (katakana)  map 0xD8800, list 0xB9BA (57 positions, same layout)
  page 2 (AB)        map 0xD9000, list 0xBB5B (55 positions)
Pages 0 and 1 both become the lowercase page; the AB page keeps its capitals
and digits, with the Japanese punctuation swapped for English. The cursor
x/y tables (0xB905 / 0xB943) give each kana position's tile.

Usage (game folder): python3 tools/make_keyboard.py
"""
from __future__ import annotations

import os
import sys

TK = os.environ.get("RHTK", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "toolkit"))
sys.path.insert(0, TK)
from rhtk import patch  # noqa: E402
from rhtk.table import Table  # noqa: E402

MAPS = (0xD8000, 0xD8800, 0xD9000)
KANA_LISTS = (0xB981, 0xB9BA)
KANA_N = 0x39
KANA_X, KANA_Y = 0xB905, 0xB943
AB_LIST, AB_N = 0xBB5B, 0x37
HAMSTER_TITLE = 0xB348  # 15 tiles from column 2; column 8 gets ♂/♀

# lowercase page, by kana cursor position (see the coordinate tables)
LOWER = ("abcde" "klmno" "uvwxy" "01234" "\";+()"   # positions 0-24: left block, rows 1-5
         "fghij" "pqrst" "z♂♀" "56789" "%~…♡ "      # 25-47: middle block
         ".,-'!" "?:&/")                            # 48-56: right block
assert len(LOWER) == KANA_N
# AB page: Japanese punctuation -> English
AB_SWAP = {0x9A: ",", 0x9D: ".", 0x9E: "-", 0xA0: '"', 0xB1: "(", 0xB2: ")",
           0xB5: "♂", 0xB6: "♀", 0xAB: "%", 0xAC: "♡", 0x7A: ";", 0x79: "~"}
TITLE = "Your name? "      # row 1, columns 4-14; the cage title overwrites columns
                           # 4-7 with tiles D7-DA, which make_font.py draws as "Cage"
PET_TITLE = " Pet (\x00) name? "
LABEL_KANA = (0x3D, 0x4C)   # カナ inside the 【】 buttons
LABEL_HIRA = (0x0A, 0x15)   # かな


def main():
    rom = open("rom/original.gbc", "rb").read()
    en = Table.parse(open("tables/en.tbl", encoding="utf-8").read())

    def code(ch: str) -> int:
        return 0x00 if ch in " \x00" else en.encode(ch)[0]

    out = bytearray(rom)
    # lowercase pages
    for page in (0, 1):
        m, lst = MAPS[page], KANA_LISTS[page]
        for pos, ch in enumerate(LOWER):
            col, row = rom[KANA_X + pos] // 8 - 1, rom[KANA_Y + pos] // 8 - 1
            out[m + row * 32 + col] = code(ch)
            out[lst + pos] = code(ch)
    # AB page punctuation (list and map)
    for i in range(AB_N):
        if rom[AB_LIST + i] in AB_SWAP:
            out[AB_LIST + i] = code(AB_SWAP[rom[AB_LIST + i]])
    for r in range(8, 17, 2):
        for c in range(1, 19):
            a = MAPS[2] + r * 32 + c
            if rom[a] in AB_SWAP and not (r in (12, 14) and c >= 14):  # keep the button brackets
                out[a] = code(AB_SWAP[rom[a]])
    # titles and page buttons on all three maps
    for m in MAPS:
        for i, ch in enumerate(TITLE):
            out[m + 32 + 4 + i] = code(ch)
        for r in (12, 14):
            inner = m + r * 32 + 15
            if tuple(rom[inner:inner + 2]) in (LABEL_KANA, LABEL_HIRA):
                out[inner:inner + 2] = bytes([code("a"), code("b")])
    title = bytes(code(ch) for ch in PET_TITLE)
    assert len(title) == 15
    out[HAMSTER_TITLE:HAMSTER_TITLE + 15] = title
    os.makedirs("patches", exist_ok=True)
    with open("patches/keyboard.ips", "wb") as f:
        f.write(patch.ips_create(rom, bytes(out)))
    print("wrote patches/keyboard.ips")


if __name__ == "__main__":
    main()
