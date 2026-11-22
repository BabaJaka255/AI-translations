"""Build patches/banners.ips: English title banners on the contest entry screens.

Each of the eight events has its own entry screen: a tileset (loaded to 0x9000)
and a BG map (bank 1D and others), loaded by the code at 0x6F8B-0x7224. The
title banner is map rows 2-3, columns 1-18: Japanese lettering, white with a
yellow top edge and a red shadow, on navy (palette 5; colors 0 white, 1 yellow,
2 red, 3 navy). The banner's tiles are used nowhere else on the screen, so they
are redrawn: each English letter is 8x16 (a main-font capital, made bold and
doubled in height) and takes one column; repeated letters share tiles, and
spaces use the screen's plain navy tile 0x02.

Usage (game folder): python3 tools/make_banners.py
"""
from __future__ import annotations

import os
import sys

TK = os.environ.get("RHTK", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "toolkit"))
sys.path.insert(0, TK)
sys.path.insert(0, os.path.dirname(__file__))
from rhtk import patch  # noqa: E402
from make_font import FONT_OFF  # noqa: E402

NAVY = 0x02  # an all-navy tile in every one of these tilesets
COL0, WIDTH = 1, 18
# (tileset, map, banner text); the order is the event table's (eventnames block)
BANNERS = [
    (0x6D8E0, 0x75000, "LOVELY CONTEST"),   # ラブリーコンテスト
    (0x6DCC0, 0x75800, "PRETTY CUP"),       # プリティーカップ
    (0x70000, 0x74000, "100M DASH"),        # 100メートル走
    (0x6E1B0, 0x76000, "LEAPFROG"),         # かえる跳び
    (0x6E5C0, 0x5C000, "SNACK RACE"),       # ひろいぐいレース
    (0x6EA50, 0x5C800, "30M MONKEY BARS"),  # 30Mうんてい
    (0x6EE40, 0x76800, "SEED CATCH"),       # たね キャッチ
    (0xEDA70, 0x69000, "WHEEL RACE!"),      # 回し車レース!! (one "!" per the style guide)
]
# main font codes: A = 0x7F, digits 0x6F-0x78, ! = 0x7B (tables/en.tbl)
CODES = {**{chr(65 + i): 0x7F + i for i in range(26)},
         **{str(i): 0x6F + i for i in range(10)}, "!": 0x7B}


# the font's 3 reads as an 8 at banner size
GLYPH_FIX = {"3": ["..####..", ".##..##.", ".....##.", "...###..", ".....##.", ".##..##.",
                   "..####..", "........"]}


def letter(rom, ch):
    """16 rows x 8 columns of 0/1: the font glyph doubled in height."""
    o = FONT_OFF + CODES[ch] * 16
    rows = []
    for y in range(8):
        b = rom[o + y * 2] | rom[o + y * 2 + 1]
        if ch in GLYPH_FIX:
            b = int(GLYPH_FIX[ch][y].replace(".", "0").replace("#", "1"), 2)
        rows += [[(b >> (7 - x)) & 1 for x in range(8)]] * 2
    return rows


def shade(body):
    """Banner colors for one 16x8 letter: white body, red shadow to the right,
    yellow edge on top, navy elsewhere."""
    h, w = len(body), len(body[0])
    at = lambda y, x: 0 <= y < h and 0 <= x < w and body[y][x]
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            if body[y][x]:
                row.append(0)
            elif at(y, x - 1) or at(y - 1, x - 1):
                row.append(2)
            elif at(y + 1, x):
                row.append(1)
            else:
                row.append(3)
        out.append(row)
    return out


def tile_bytes(pix):
    out = bytearray()
    for row in pix:
        lo = sum((c & 1) << (7 - x) for x, c in enumerate(row))
        hi = sum((c >> 1) << (7 - x) for x, c in enumerate(row))
        out += bytes((lo, hi))
    return bytes(out)


def main():
    rom = open("rom/original.gbc", "rb").read()
    out = bytearray(rom)
    for tiles, bgmap, text in BANNERS:
        assert len(text) <= WIDTH, text
        banner = {rom[bgmap + r * 32 + c] for r in (2, 3) for c in range(COL0, COL0 + WIDTH)}
        elsewhere = {rom[bgmap + r * 32 + c] for r in range(18) for c in range(20)
                     if not (r in (2, 3) and COL0 <= c < COL0 + WIDTH)}
        free = sorted(banner - elsewhere - {NAVY})
        assert all(b == 0xFF for b in rom[tiles + NAVY * 16:tiles + NAVY * 16 + 16]), "tile 02 is not navy"
        letters = sorted(set(text) - {" "})
        if 2 * len(letters) > len(free):
            sys.exit(f"{text}: {len(letters)} letters need {2 * len(letters)} tiles, {len(free)} free")
        pair = {}
        for i, ch in enumerate(letters):
            top, bottom = free[2 * i], free[2 * i + 1]
            pix = shade(letter(rom, ch))
            out[tiles + top * 16:tiles + top * 16 + 16] = tile_bytes(pix[:8])
            out[tiles + bottom * 16:tiles + bottom * 16 + 16] = tile_bytes(pix[8:])
            pair[ch] = (top, bottom)
        pair[" "] = (NAVY, NAVY)
        line = text.center(WIDTH)
        for c, ch in enumerate(line):
            out[bgmap + 2 * 32 + COL0 + c], out[bgmap + 3 * 32 + COL0 + c] = pair[ch]
    os.makedirs("patches", exist_ok=True)
    with open("patches/banners.ips", "wb") as f:
        f.write(patch.ips_create(rom, bytes(out)))
    print(f"wrote patches/banners.ips ({len(BANNERS)} banners)")


if __name__ == "__main__":
    main()
